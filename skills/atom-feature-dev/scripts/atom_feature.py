#!/usr/bin/env python3
"""Initialize and validate a LovStudio atom-feature control manifest."""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List


SCHEMA = "lovstudio/atom-feature/v1"
STATUSES = ("planned", "implemented", "verified", "released", "not-applicable")
SURFACES = ("sdk", "cli", "api", "ui", "agent")
OPERATIONS = ("docs", "tests", "seo", "geo", "auth", "payment", "analytics", "support")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ManifestError(ValueError):
    pass


def atom_dir(root: Path) -> Path:
    return root.expanduser().resolve() / ".atom-feature"


def manifest_path(root: Path) -> Path:
    return atom_dir(root) / "manifest.json"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(path)


def initial_manifest(feature_id: str, title: str) -> Dict[str, Any]:
    surface_map = {
        name: {
            "status": "planned",
            "artifact": None,
            "contract": ".atom-feature/contract.schema.json",
            "command": None,
            "verification": [],
            "reason": None,
        }
        for name in SURFACES
    }
    operation_map = {
        name: {
            "status": "planned",
            "artifact": None,
            "verification": [],
            "reason": None,
        }
        for name in OPERATIONS
    }
    return {
        "schema": SCHEMA,
        "version": "0.2.0",
        "feature": {
            "id": feature_id,
            "title": title,
            "summary": "",
            "status": "planned",
        },
        "contracts": {
            "feature": ".atom-feature/contract.schema.json",
            "profiles": ".atom-feature/profiles.schema.json",
            "acceptance": ".atom-feature/acceptance.json",
        },
        "surfaces": surface_map,
        "operations": operation_map,
        "dashboard": {
            "status": "planned",
            "artifact": None,
            "route": None,
            "verification": [],
        },
    }


def init_command(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        raise ManifestError(f"target project does not exist: {root}")
    if not ID_RE.fullmatch(args.feature_id):
        raise ManifestError("feature id must use kebab-case")
    path = manifest_path(root)
    if path.exists():
        raise ManifestError(f"refusing to overwrite existing manifest: {path}")

    directory = atom_dir(root)
    write_json(path, initial_manifest(args.feature_id, args.title.strip()))
    write_json(
        directory / "contract.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"urn:lovstudio:atom-feature:{args.feature_id}:contract",
            "title": args.title.strip(),
            "type": "object",
            "properties": {
                "input": {"type": "object"},
                "output": {"type": "object"},
            },
            "required": ["input"],
            "additionalProperties": False,
        },
    )
    write_json(
        directory / "profiles.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"urn:lovstudio:atom-feature:{args.feature_id}:profiles",
            "title": f"{args.title.strip()} Profile Preset",
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "values": {"type": "object"},
            },
            "required": ["name", "values"],
            "additionalProperties": False,
        },
    )
    write_json(directory / "acceptance.json", {"schema": SCHEMA, "vectors": []})
    write_json(directory / "presets.json", {"active": None, "presets": []})
    write_json(directory / "status.json", {"schema": SCHEMA, "runs": []})
    print(f"created={path}")
    return 0


def validate_manifest(root: Path) -> List[str]:
    errors: List[str] = []
    path = manifest_path(root)
    try:
        manifest = load_json(path)
    except ManifestError as exc:
        return [str(exc)]
    if not isinstance(manifest, dict):
        return [f"{path}: root must be an object"]
    if manifest.get("schema") != SCHEMA:
        errors.append(f"{path}: schema must be {SCHEMA}")
    feature = manifest.get("feature")
    if not isinstance(feature, dict):
        errors.append(f"{path}: feature must be an object")
    else:
        feature_id = feature.get("id")
        if not isinstance(feature_id, str) or not ID_RE.fullmatch(feature_id):
            errors.append(f"{path}: feature.id must use kebab-case")
        if not isinstance(feature.get("title"), str) or not feature.get("title", "").strip():
            errors.append(f"{path}: feature.title is required")
        if feature.get("status") not in STATUSES:
            errors.append(f"{path}: feature.status is invalid")

    contracts = manifest.get("contracts")
    if not isinstance(contracts, dict):
        errors.append(f"{path}: contracts must be an object")
    else:
        for name in ("feature", "profiles", "acceptance"):
            relative = contracts.get(name)
            if not isinstance(relative, str) or not relative:
                errors.append(f"{path}: contracts.{name} is required")
                continue
            resolved = (root / relative).resolve()
            if root.resolve() not in (resolved, *resolved.parents):
                errors.append(f"{path}: contracts.{name} escapes the project root")
            elif not resolved.is_file():
                errors.append(f"{path}: contracts.{name} does not exist: {relative}")

    for group_name in ("surfaces", "operations"):
        group = manifest.get(group_name)
        if not isinstance(group, dict) or not group:
            errors.append(f"{path}: {group_name} must be a non-empty object")
            continue
        for name, record in group.items():
            label = f"{path}: {group_name}.{name}"
            if not isinstance(record, dict):
                errors.append(f"{label} must be an object")
                continue
            status = record.get("status")
            if status not in STATUSES:
                errors.append(f"{label}.status is invalid")
            verification = record.get("verification")
            if not isinstance(verification, list):
                errors.append(f"{label}.verification must be an array")
            if status in ("verified", "released") and not verification:
                errors.append(f"{label} needs verification evidence for status {status}")
            if status == "not-applicable" and not record.get("reason"):
                errors.append(f"{label} needs a reason for not-applicable")
            artifact = record.get("artifact")
            if status in ("implemented", "verified", "released") and not artifact:
                errors.append(f"{label} needs an artifact for status {status}")
            command = record.get("command")
            if command is not None and (
                not isinstance(command, list)
                or not command
                or not all(isinstance(item, str) and item for item in command)
            ):
                errors.append(f"{label}.command must be a non-empty string array or null")
    dashboard = manifest.get("dashboard")
    if not isinstance(dashboard, dict):
        errors.append(f"{path}: dashboard must be an object")
    else:
        dashboard_status = dashboard.get("status")
        dashboard_evidence = dashboard.get("verification")
        if dashboard_status not in STATUSES:
            errors.append(f"{path}: dashboard.status is invalid")
        if not isinstance(dashboard_evidence, list):
            errors.append(f"{path}: dashboard.verification must be an array")
        if dashboard_status in ("implemented", "verified", "released") and not dashboard.get("artifact"):
            errors.append(f"{path}: dashboard needs an artifact for status {dashboard_status}")
        if dashboard_status in ("verified", "released") and not dashboard_evidence:
            errors.append(f"{path}: dashboard needs verification evidence for status {dashboard_status}")
    return errors


def validate_command(args: argparse.Namespace) -> int:
    errors = validate_manifest(args.root.expanduser().resolve())
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASSED: atom feature manifest ({manifest_path(args.root)})")
    return 0


def set_status_command(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    path = manifest_path(root)
    manifest = load_json(path)
    if args.group == "dashboard":
        record = manifest.get("dashboard")
        item_name = "dashboard"
        if not isinstance(record, dict):
            raise ManifestError("manifest dashboard record is missing")
    else:
        group = manifest.get(args.group)
        if not args.name:
            raise ManifestError(f"--name is required for group {args.group}")
        if not isinstance(group, dict) or args.name not in group:
            raise ManifestError(f"unknown {args.group} item: {args.name}")
        record = group[args.name]
        item_name = args.name
    if args.status in ("verified", "released") and not args.evidence:
        raise ManifestError(f"status {args.status} requires at least one --evidence")
    if args.status == "not-applicable" and not args.reason:
        raise ManifestError("status not-applicable requires --reason")
    if args.status in ("implemented", "verified", "released") and not (args.artifact or record.get("artifact")):
        raise ManifestError(f"status {args.status} requires --artifact")
    record["status"] = args.status
    if args.artifact:
        record["artifact"] = args.artifact
    if args.evidence:
        record["verification"] = args.evidence
    if args.reason:
        record["reason"] = args.reason
    manifest["feature"]["status"] = derive_overall_status(manifest)
    write_json(path, manifest)
    print(f"updated={args.group}.{item_name}:{args.status}")
    return 0


def derive_overall_status(manifest: Dict[str, Any]) -> str:
    records = list(manifest.get("surfaces", {}).values())
    records.extend(manifest.get("operations", {}).values())
    dashboard = manifest.get("dashboard")
    if isinstance(dashboard, dict):
        records.append(dashboard)
    statuses = [record.get("status") for record in records if isinstance(record, dict)]
    applicable = [status for status in statuses if status != "not-applicable"]
    if not applicable or "planned" in applicable:
        return "planned"
    if "implemented" in applicable:
        return "implemented"
    if all(status == "released" for status in applicable):
        return "released"
    return "verified"


def status_command(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    manifest = load_json(manifest_path(root))
    feature = manifest["feature"]
    if args.format == "json":
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    print(f"# {feature['title']}")
    print()
    print(f"Overall: `{feature['status']}`")
    for group_name in ("surfaces", "operations"):
        print()
        print(f"## {group_name.title()}")
        print()
        for name, record in manifest[group_name].items():
            evidence = len(record.get("verification", []))
            print(f"- `{name}`: {record['status']} ({evidence} evidence item(s))")
    return 0


def selftest_command(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        args = argparse.Namespace(root=root, feature_id="sample-atom", title="Sample Atom")
        init_command(args)
        errors = validate_manifest(root)
        if errors:
            for error in errors:
                print(error)
            return 1
    print("PASSED: atom_feature.py selftest")
    return 0


def dashboard_command(args: argparse.Namespace) -> int:
    import atom_dashboard

    dashboard_args = argparse.Namespace(
        root=args.root,
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        allow_run=args.allow_run,
        allow_write=args.allow_write,
        open=args.open,
        verbose=args.verbose,
    )
    return atom_dashboard.serve_command(dashboard_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a new atom feature manifest")
    init_parser.add_argument("--root", type=Path, required=True)
    init_parser.add_argument("--id", dest="feature_id", required=True)
    init_parser.add_argument("--title", required=True)
    init_parser.set_defaults(handler=init_command)

    validate_parser = subparsers.add_parser("validate", help="validate an atom feature manifest")
    validate_parser.add_argument("--root", type=Path, required=True)
    validate_parser.set_defaults(handler=validate_command)

    status_parser = subparsers.add_parser("status", help="render current atom feature status")
    status_parser.add_argument("--root", type=Path, required=True)
    status_parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    status_parser.set_defaults(handler=status_command)

    set_parser = subparsers.add_parser("set-status", help="update one surface or operation status")
    set_parser.add_argument("--root", type=Path, required=True)
    set_parser.add_argument("--group", choices=("surfaces", "operations", "dashboard"), required=True)
    set_parser.add_argument("--name", help="required for surfaces and operations")
    set_parser.add_argument("--status", choices=STATUSES, required=True)
    set_parser.add_argument("--artifact")
    set_parser.add_argument("--evidence", action="append", default=[])
    set_parser.add_argument("--reason")
    set_parser.set_defaults(handler=set_status_command)

    dashboard_parser = subparsers.add_parser("dashboard", help="serve the companion Atom Workbench")
    dashboard_parser.add_argument("--root", type=Path, required=True)
    dashboard_parser.add_argument("--host", default="127.0.0.1")
    dashboard_parser.add_argument("--port", type=int, default=6174)
    dashboard_parser.add_argument("--timeout", type=int, default=60)
    dashboard_parser.add_argument("--allow-run", action="store_true")
    dashboard_parser.add_argument("--allow-write", action="store_true")
    dashboard_parser.add_argument("--open", action="store_true")
    dashboard_parser.add_argument("--verbose", action="store_true")
    dashboard_parser.set_defaults(handler=dashboard_command)

    selftest_parser = subparsers.add_parser("selftest", help="exercise init and validation")
    selftest_parser.set_defaults(handler=selftest_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except ManifestError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
