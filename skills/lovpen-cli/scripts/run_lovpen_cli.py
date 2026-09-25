#!/usr/bin/env python3
"""Resolve and invoke lovpen-cli without shell evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SKILL_ID = "lovpen-cli"
CLI_COMMAND = "lovpen-cli"


def context_id(code: str, message: str) -> str:
    digest = hashlib.sha256(f"{code}|{message}".encode("utf-8")).hexdigest()[:8]
    return f"skill-{digest}"


def fail(code: str, message: str, hint: str, exit_code: int = 3) -> int:
    payload = {
        "ok": False,
        "command": "resolve",
        "error": {
            "code": code,
            "message": message,
            "context_id": context_id(code, message),
            "hint": hint,
        },
    }
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    return exit_code


def load_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def nested(data: Dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def read_profile() -> Dict[str, Any]:
    raw_path = os.environ.get("SKILL_PROFILE_PATH", "").strip()
    if not raw_path:
        return {}
    return load_json(Path(raw_path).expanduser())


def profile_values(profile: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    skill = nested(profile, "skills", SKILL_ID)
    skill = skill if isinstance(skill, dict) else {}
    skill_profile = skill.get("profile") if isinstance(skill.get("profile"), dict) else {}
    records = skill.get("records") if isinstance(skill.get("records"), dict) else {}
    workspace = profile.get("workspace") if isinstance(profile.get("workspace"), dict) else {}

    cli_path = skill_profile.get("cli_path") or records.get("cli_path")
    project_root = (
        skill_profile.get("project_root")
        or records.get("project_root")
        or workspace.get("project_root")
    )
    return (
        str(cli_path) if isinstance(cli_path, str) and cli_path.strip() else None,
        str(project_root) if isinstance(project_root, str) and project_root.strip() else None,
    )


def resolve_executable(value: str) -> Optional[str]:
    candidate = Path(value).expanduser()
    if candidate.is_absolute() or "/" in value or "\\" in value:
        resolved = candidate.resolve()
        return str(resolved) if resolved.is_file() and os.access(resolved, os.X_OK) else None
    return shutil.which(value)


def ancestor_roots(start: Path) -> Iterable[Path]:
    current = start.resolve()
    yield current
    yield from current.parents


def ready_source(root: Path) -> Optional[Tuple[Path, Path]]:
    harness = root / "agent-harness"
    spec_path = harness / "lov-cli.json"
    module_path = harness / "src" / "lovpen_cli" / "__main__.py"
    spec = load_json(spec_path)
    if (
        spec.get("schema") == "lov-cli/v1"
        and spec.get("status") == "ready"
        and spec.get("command") == CLI_COMMAND
        and module_path.is_file()
    ):
        return root.resolve(), (harness / "src").resolve()
    return None


def project_candidates(explicit: str, profile_root: Optional[str]) -> Iterable[Path]:
    seen = set()
    raw_values = [
        explicit,
        os.environ.get("LOVPEN_PROJECT_ROOT", ""),
        profile_root or "",
    ]
    for raw in raw_values:
        if not raw:
            continue
        candidate = Path(raw).expanduser().resolve()
        if candidate not in seen:
            seen.add(candidate)
            yield candidate
    for candidate in ancestor_roots(Path.cwd()):
        if candidate not in seen:
            seen.add(candidate)
            yield candidate


def resolve_backend(explicit_cli: str, explicit_project: str) -> Dict[str, Any]:
    profile = read_profile()
    profile_cli, profile_root = profile_values(profile)
    cli_values = [
        explicit_cli,
        os.environ.get("LOVPEN_CLI", ""),
        profile_cli or "",
        CLI_COMMAND,
    ]
    for raw in cli_values:
        if not raw:
            continue
        executable = resolve_executable(raw)
        if executable:
            raw_project_root = (
                explicit_project
                or os.environ.get("LOVPEN_PROJECT_ROOT", "")
                or profile_root
                or ""
            )
            project_root = (
                Path(raw_project_root).expanduser().resolve()
                if raw_project_root
                else None
            )
            return {
                "mode": "executable",
                "argv": [executable],
                "resolved": executable,
                "project_root": str(project_root) if project_root else None,
                "env": os.environ.copy(),
            }

    for root in project_candidates(explicit_project, profile_root):
        source = ready_source(root)
        if not source:
            continue
        project_root, python_path = source
        env = os.environ.copy()
        current_python_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = str(python_path) + (
            os.pathsep + current_python_path if current_python_path else ""
        )
        return {
            "mode": "source-checkout",
            "argv": [sys.executable, "-m", "lovpen_cli"],
            "resolved": str(python_path / "lovpen_cli"),
            "project_root": str(project_root),
            "env": env,
        }

    raise FileNotFoundError(
        "Neither an installed lovpen-cli nor a ready Lovpen agent-harness could be resolved."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", default="", help="Explicit lovpen-cli executable")
    parser.add_argument("--project-root", default="", help="Explicit Lovpen project root")
    parser.add_argument("--resolve-only", action="store_true", help="Print the resolved backend without invoking it")
    parser.add_argument("cli_args", nargs=argparse.REMAINDER, help="Arguments after -- are passed to lovpen-cli")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        backend = resolve_backend(args.cli, args.project_root)
    except FileNotFoundError as exc:
        return fail(
            "lovpen_cli_not_found",
            str(exc),
            "Install lovpen-cli 0.2.0, set LOVPEN_CLI, or pass --project-root for a ready Lovpen checkout.",
            3,
        )

    if args.resolve_only:
        data = {
            "mode": backend["mode"],
            "resolved": backend["resolved"],
            "project_root": backend["project_root"],
        }
        print(json.dumps({"ok": True, "command": "resolve", "data": data}, ensure_ascii=False))
        return 0

    cli_args: List[str] = list(args.cli_args)
    if cli_args and cli_args[0] == "--":
        cli_args = cli_args[1:]
    if not cli_args:
        return fail(
            "missing_cli_arguments",
            "No lovpen-cli arguments were supplied.",
            "Pass arguments after --, for example: -- --json doctor",
            2,
        )

    argv = list(backend["argv"])
    project_root = backend.get("project_root")
    if project_root and "--project-root" not in cli_args:
        argv.extend(["--project-root", project_root])
    argv.extend(cli_args)
    try:
        completed = subprocess.run(
            argv,
            env=backend["env"],
            shell=False,
            check=False,
        )
    except OSError as exc:
        return fail(
            "lovpen_cli_exec_failed",
            f"Could not start the resolved Lovpen CLI: {exc}",
            "Run --resolve-only and verify the reported executable or source checkout.",
            4,
        )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
