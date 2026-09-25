#!/usr/bin/env python3
"""Validate a generated CLI harness, its JSON contract, and real invocation."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


CLI_SCHEMA = "lov-cli/v1"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
RESERVED = {"doctor", "info", "capabilities"}


def load_json(path: Path, errors: List[str]) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        errors.append(f"missing required file: {path.name}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot parse {path.name}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path.name} must contain a JSON object")
        return None
    return value


def validate_spec(root: Path, spec: Dict[str, Any], errors: List[str]) -> None:
    if spec.get("schema") != CLI_SCHEMA:
        errors.append(f"lov-cli.json schema must be {CLI_SCHEMA}")
    if spec.get("status") != "ready":
        errors.append("lov-cli.json status must be ready after real E2E tests pass")
    command = spec.get("command")
    package = spec.get("package")
    version = spec.get("version")
    if not isinstance(command, str) or not NAME_RE.fullmatch(command):
        errors.append("lov-cli.json command must be kebab-case")
    if not isinstance(package, str) or not PACKAGE_RE.fullmatch(package):
        errors.append("lov-cli.json package must be a safe snake_case name")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        errors.append("lov-cli.json version must use SemVer")
    if not isinstance(spec.get("description"), str) or not spec["description"].strip():
        errors.append("lov-cli.json description is required")
    dependencies = spec.get("python_dependencies", [])
    if not isinstance(dependencies, list) or not all(
        isinstance(item, str) and item.strip() for item in dependencies
    ):
        errors.append("lov-cli.json python_dependencies must be a string list")
    project = spec.get("project")
    if not isinstance(project, dict) or not isinstance(project.get("root_relative"), str):
        errors.append("lov-cli.json project.root_relative is required")
    backend = spec.get("backend")
    if not isinstance(backend, dict) or backend.get("kind") not in {"subprocess", "custom"}:
        errors.append("lov-cli.json backend.kind must be subprocess or custom")
    commands = spec.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("lov-cli.json must declare at least one project-specific command")
    else:
        names: List[str] = []
        for index, item in enumerate(commands):
            if not isinstance(item, dict):
                errors.append(f"commands[{index}] must be an object")
                continue
            name = item.get("name")
            if not isinstance(name, str) or not NAME_RE.fullmatch(name) or name in RESERVED:
                errors.append(f"commands[{index}].name is invalid or reserved")
            else:
                names.append(name)
            if not isinstance(item.get("description"), str) or not item["description"].strip():
                errors.append(f"commands[{index}].description is required")
            if not isinstance(item.get("mutates"), bool):
                errors.append(f"commands[{index}].mutates must be boolean")
        if len(names) != len(set(names)):
            errors.append("project-specific command names must be unique")
    required = [
        root / "pyproject.toml",
        root / "setup.py",
        root / "requirements.txt",
        root / "README.md",
        root / "CLI_SPEC.md",
        root / "TEST.md",
        root / "LICENSE",
        root / "tests" / "test_core.py",
        root / "tests" / "test_e2e.py",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")
    if isinstance(package, str):
        package_root = root / "src" / package
        for name in ("__init__.py", "__main__.py", "cli.py", "backend.py", "cli_spec.json"):
            if not (package_root / name).is_file():
                errors.append(f"missing required package file: src/{package}/{name}")
        packaged = load_json(package_root / "cli_spec.json", errors)
        if packaged is not None and packaged != spec:
            errors.append("packaged cli_spec.json must exactly match root lov-cli.json")
    pyproject = root / "pyproject.toml"
    if pyproject.is_file() and isinstance(command, str) and isinstance(package, str):
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        entry = re.compile(
            rf"(?m)^\s*{re.escape(command)}\s*=\s*[\"']{re.escape(package)}\.cli:main[\"']\s*$"
        )
        if not entry.search(text):
            errors.append("pyproject.toml console entry point does not match lov-cli.json")
    test_doc = root / "TEST.md"
    if test_doc.is_file():
        text = test_doc.read_text(encoding="utf-8", errors="replace")
        if re.search(r"(?i)status:\s*scaffold", text):
            errors.append("TEST.md still reports scaffold status; append real named results")


def run_process(
    argv: Sequence[str],
    cwd: Path,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def parse_success(result: subprocess.CompletedProcess[str], label: str, errors: List[str]) -> Optional[Dict[str, Any]]:
    if result.returncode != 0:
        errors.append(
            f"{label} exited {result.returncode}: {(result.stderr or result.stdout).strip()}"
        )
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        errors.append(f"{label} did not emit one JSON object: {exc}")
        return None
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        errors.append(f"{label} JSON envelope must contain ok=true")
        return None
    return payload


def validate_invocation(root: Path, spec: Dict[str, Any], require_installed: bool, errors: List[str], checks: List[str]) -> None:
    package = spec.get("package")
    command = spec.get("command")
    if not isinstance(package, str) or not isinstance(command, str):
        return
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    module = [sys.executable, "-m", package]
    with tempfile.TemporaryDirectory(prefix="lov-cli-validate-") as temporary_name:
        neutral = Path(temporary_name)
        help_result = run_process([*module, "--help"], neutral, env)
        if help_result.returncode != 0:
            errors.append(f"source --help failed: {(help_result.stderr or help_result.stdout).strip()}")
        elif not all(name in help_result.stdout for name in RESERVED):
            errors.append("source --help must list doctor, info, and capabilities")
        else:
            checks.append("source-help")
        capabilities = parse_success(
            run_process([*module, "--json", "capabilities"], neutral, env),
            "source capabilities",
            errors,
        )
        if capabilities is not None:
            declared = capabilities.get("data", {}).get("commands", [])
            if len(declared) < 1:
                errors.append("source capabilities must list a project-specific command")
            else:
                checks.append("source-capabilities-json")
        doctor = parse_success(
            run_process([*module, "--json", "doctor"], neutral, env),
            "source doctor",
            errors,
        )
        if doctor is not None:
            if doctor.get("data", {}).get("ready") is not True:
                errors.append("source doctor must report ready=true")
            else:
                checks.append("source-doctor-json")
        installed = shutil.which(command)
        if require_installed and not installed:
            errors.append(f"installed command not found in PATH: {command}")
        if installed:
            info = parse_success(
                run_process([installed, "--json", "info"], neutral),
                "installed info",
                errors,
            )
            if info is not None:
                data = info.get("data", {})
                if data.get("command") != command or data.get("version") != spec.get("version"):
                    errors.append("installed command identity does not match lov-cli.json")
                else:
                    checks.append("installed-command-neutral-cwd")


def run_tests(root: Path, errors: List[str], checks: List[str]) -> None:
    result = run_process(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        root,
        timeout=300,
    )
    if result.returncode != 0:
        errors.append(f"test suite failed:\n{result.stdout}{result.stderr}".strip())
    else:
        match = re.search(r"Ran\s+(\d+)\s+tests?", result.stderr + result.stdout)
        checks.append(f"tests:{match.group(1) if match else 'passed'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("harness", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--require-installed", action="store_true")
    parser.add_argument("--json", dest="json_output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.harness.expanduser().resolve()
    errors: List[str] = []
    checks: List[str] = []
    if not root.is_dir():
        errors.append(f"harness is not a directory: {root}")
        spec = None
    else:
        spec = load_json(root / "lov-cli.json", errors)
    if spec is not None:
        validate_spec(root, spec, errors)
        if not errors:
            validate_invocation(root, spec, args.require_installed, errors, checks)
        if args.run_tests and not errors:
            run_tests(root, errors, checks)
    result = {
        "ok": not errors,
        "harness": str(root),
        "checks": checks,
        "errors": errors,
    }
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False))
    elif errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"PASSED: CLI validation ({root})")
        for check in checks:
            print(f"- {check}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
