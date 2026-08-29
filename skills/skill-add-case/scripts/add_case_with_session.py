#!/usr/bin/env python3
"""Upload the accepted session as paid evidence, then add its case atomically."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ADD_CASE_PATH = SCRIPT_DIR / "add_case.py"
SPEC = importlib.util.spec_from_file_location("lov_skill_add_case_core", ADD_CASE_PATH)
if not SPEC or not SPEC.loader:
    raise SystemExit(f"cannot load {ADD_CASE_PATH}")
add_case = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = add_case
SPEC.loader.exec_module(add_case)

class WorkflowError(RuntimeError):
    pass


def resolve_share_script(explicit: Path | None) -> Path:
    candidates = [
        explicit,
        Path(os.environ["LOV_SHARE_SESSION_SKILL_DIR"]) / "scripts" / "share_session.py"
        if os.environ.get("LOV_SHARE_SESSION_SKILL_DIR")
        else None,
        Path.home() / ".agents" / "skills" / "lov-share-session" / "scripts" / "share_session.py",
        SCRIPT_DIR.parents[1] / "share-session-skill" / "scripts" / "share_session.py",
    ]
    for candidate in candidates:
        if candidate and candidate.expanduser().is_file():
            return candidate.expanduser().resolve()
    raise WorkflowError(
        "cannot find lov-share-session; pass --share-session-script or install it in ~/.agents/skills"
    )


def share_command(
    args: argparse.Namespace,
    script: Path,
    skill_id: str,
    case_id: str,
    title: str,
) -> list[str]:
    command = [
        sys.executable,
        str(script),
        "--detail",
        args.detail,
        "--title",
        args.session_title or f"{title} · 完整实战 Session",
        "--paid-skill",
        skill_id,
        "--case-id",
        case_id,
        "--base-url",
        args.base_url,
        "--timeout",
        str(args.timeout),
    ]
    if args.file:
        command.extend(["--file", args.file])
    elif args.session_id:
        command.extend(["--session-id", args.session_id])
    if args.profile_path:
        command.extend(["--profile-path", str(args.profile_path)])
    command.append("--dry-run" if args.dry_run else "--json")
    return command


def execute_share(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip() or completed.stdout.strip()
        raise WorkflowError(
            f"lov-share-session failed with exit {completed.returncode}: {diagnostic}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise WorkflowError(
            f"lov-share-session returned invalid JSON: {completed.stdout[:500]}"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkflowError("lov-share-session result must be one JSON object")
    return payload


def paid_session_case_field(
    payload: dict[str, Any],
    *,
    skill_id: str,
    case_id: str,
) -> dict[str, Any]:
    if (
        payload.get("access") != "paid"
        or payload.get("targetSkill") != skill_id
        or payload.get("caseId") != case_id
        or payload.get("pricingRule") != add_case.SESSION_PRICING_RULE
    ):
        raise WorkflowError("lov-share-session returned mismatched paid case metadata")
    return {
        "url": payload.get("url"),
        "access": "paid",
        "priceCredits": payload.get("priceCredits"),
        "pricingRule": payload.get("pricingRule"),
        "targetSkill": payload.get("targetSkill"),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.target.expanduser().resolve()
    if not (root / "SKILL.md").is_file():
        raise WorkflowError(f"target is not a Skill source: {root}")
    raw = add_case.load_json(args.case)
    case = add_case.validate_case(root, raw, require_session=False)
    preflight = add_case.mutate_case(
        root,
        case,
        replace_existing=args.replace_existing,
        dry_run=True,
    )
    skill_id = add_case.target_skill_id(root)
    share_script = resolve_share_script(args.share_session_script)
    command = share_command(
        args,
        share_script,
        skill_id,
        case["id"],
        str(case["title"]),
    )
    share = execute_share(command)

    if args.dry_run:
        access = share.get("access")
        if not isinstance(access, dict) or access.get("mode") != "paid":
            raise WorkflowError("lov-share-session dry run did not prepare paid access")
        return {
            **preflight,
            "target_skill_id": skill_id,
            "session_status": "prepared-not-uploaded",
            "session_price": "server-derived-on-upload",
        }

    case["session"] = paid_session_case_field(
        share,
        skill_id=skill_id,
        case_id=case["id"],
    )
    try:
        complete_case = add_case.validate_case(root, case)
        result = add_case.mutate_case(
            root,
            complete_case,
            replace_existing=args.replace_existing,
            dry_run=False,
        )
    except Exception as exc:
        raise WorkflowError(
            f"session uploaded at {share.get('url')}, but local case mutation failed: {exc}"
        ) from exc
    return {
        **result,
        "target_skill_id": skill_id,
        "session": complete_case["session"],
        "session_status": "uploaded-paid",
    }


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--case", required=True, help="Case JSON without a session field")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", help="Explicit transcript path")
    source.add_argument("--session-id", help="Explicit Claude or Codex session id")
    parser.add_argument("--share-session-script", type=Path, default=None)
    parser.add_argument("--session-title", default=None)
    parser.add_argument(
        "--detail",
        choices=("hidden", "concise", "detailed", "verbose"),
        default="concise",
    )
    parser.add_argument("--base-url", default="https://lovstudio.ai")
    parser.add_argument("--profile-path", type=Path, default=None)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    try:
        result = run(build_args())
    except (WorkflowError, add_case.CaseError, OSError) as exc:
        print(f"context_id=skill-add-case-session error={exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
