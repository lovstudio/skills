#!/usr/bin/env python3
"""Scaffold, validate, and exercise Codeex runtime plugins safely."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
REQUIRED_PROJECT_FILES = (
    "plugins/catalog.mjs",
    "plugins/state.mjs",
    "scripts/plugins-cli.mjs",
    "scripts/build-webview.mjs",
    "scripts/start.mjs",
    "scripts/control-server.mjs",
    "scripts/verify.mjs",
    "package.json",
)
REQUIRED_MANIFEST_FIELDS = ("id", "name", "version", "description", "entry")
HOOK_PATTERNS = {
    "transformWebview": re.compile(
        r"\bexport\s+(?:async\s+)?function\s+transformWebview\b"
    ),
    "beforeLaunch": re.compile(
        r"\bexport\s+(?:async\s+)?function\s+beforeLaunch\b"
    ),
    "handleControlRequest": re.compile(
        r"\bexport\s+(?:async\s+)?function\s+handleControlRequest\b"
    ),
}


class ContractError(RuntimeError):
    """Raised when a Codeex plugin or project violates the audited contract."""


def emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    summary = payload.get("summary")
    if summary:
        print(summary)
    for key, value in payload.items():
        if key == "summary":
            continue
        if isinstance(value, (list, dict)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            rendered = str(value)
        print(f"{key}={rendered}")


def atomic_write_json(path: Path, payload: Any, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / (
        f".{path.name}.next-{os.getpid()}-{secrets.token_hex(4)}"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(temporary, flags, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def resolve_project_root(value: str | None, require_contract: bool = True) -> Path:
    candidate = value or os.environ.get("CODEEX_PROJECT_ROOT") or os.getcwd()
    root = Path(candidate).expanduser().resolve()
    if require_contract:
        missing = [relative for relative in REQUIRED_PROJECT_FILES if not (root / relative).is_file()]
        if missing:
            raise ContractError(
                "Not a compatible Codeex repository; missing: " + ", ".join(missing)
            )
    return root


def normalize_plugin_id(value: str) -> str:
    plugin_id = value.strip()
    if not PLUGIN_ID_RE.fullmatch(plugin_id):
        raise ContractError(
            "Plugin ID must be lower-case kebab-case and start with a letter."
        )
    return plugin_id


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def parse_permissions(values: Iterable[str]) -> list[dict[str, str]]:
    permissions: list[dict[str, str]] = []
    for raw in values:
        label, separator, detail = raw.partition(":")
        if not separator or not label.strip() or not detail.strip():
            raise ContractError(
                "Each permission must use the form Label:Detail with both values present."
            )
        permissions.append({"label": label.strip(), "detail": detail.strip()})
    return permissions


def default_display_name(plugin_id: str) -> str:
    return " ".join(part.capitalize() for part in plugin_id.split("-"))


def entry_source(plugin_id: str, hook: str, control_route: bool = False) -> str:
    quoted_id = json.dumps(plugin_id)
    sections = [
        "// Safe no-op hooks are generated first. Implement behavior only through",
        "// the staged context supplied by Codeex, then add focused tests.",
    ]
    if hook in ("webview", "both"):
        sections.extend(
            [
                "",
                "export async function transformWebview(context) {",
                "  if (!context?.stage || !context?.entryFile) {",
                "    throw new Error('Codeex webview context is incomplete.');",
                "  }",
                f"  return {{ pluginId: {quoted_id}, transformedFiles: 0 }};",
                "}",
            ]
        )
    if hook in ("before-launch", "both"):
        sections.extend(
            [
                "",
                "export function beforeLaunch(context) {",
                "  if (!context?.env) {",
                "    throw new Error('Codeex launch context is incomplete.');",
                "  }",
                f"  return {{ pluginId: {quoted_id}, env: {{}} }};",
                "}",
            ]
        )
    if hook == "control" or control_route:
        sections.extend(
            [
                "",
                "export async function handleControlRequest(context) {",
                "  if (!context?.request || !context?.url) {",
                "    throw new Error('Codeex control request context is incomplete.');",
                "  }",
                "  // Return null for routes this plugin does not own.",
                "  return null;",
                "}",
            ]
        )
    return "\n".join(sections) + "\n"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ContractError(f"Missing file: {path}") from error
    except json.JSONDecodeError as error:
        raise ContractError(f"Invalid JSON in {path}: {error}") from error


def run_node_check(entry: Path) -> None:
    node = shutil.which("node")
    if not node:
        raise ContractError("Node.js is required to validate the plugin entry module.")
    result = subprocess.run(
        [node, "--check", str(entry)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise ContractError(f"Entry module syntax check failed: {detail}")


def validate_plugin_directory(
    plugin_dir: Path,
    expected_id: str | None = None,
    enforce_directory_name: bool = True,
) -> dict[str, Any]:
    manifest_file = plugin_dir / "plugin.json"
    manifest = load_json(manifest_file)
    if not isinstance(manifest, dict):
        raise ContractError(f"Manifest must be a JSON object: {manifest_file}")
    for field in REQUIRED_MANIFEST_FIELDS:
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContractError(f"Manifest field '{field}' must be a non-empty string.")
    plugin_id = normalize_plugin_id(manifest["id"])
    if expected_id and plugin_id != expected_id:
        raise ContractError(f"Expected plugin ID {expected_id}, found {plugin_id}.")
    if enforce_directory_name and plugin_dir.name != plugin_id:
        raise ContractError(
            f"Plugin directory {plugin_dir.name} does not match manifest ID {plugin_id}."
        )
    if not SEMVER_RE.fullmatch(manifest["version"]):
        raise ContractError("Manifest version must use semantic versioning.")
    permissions = manifest.get("permissions", [])
    if not isinstance(permissions, list):
        raise ContractError("Manifest permissions must be a list when present.")
    for permission in permissions:
        if not isinstance(permission, dict) or not all(
            isinstance(permission.get(field), str) and permission[field].strip()
            for field in ("label", "detail")
        ):
            raise ContractError(
                "Each permission must contain non-empty label and detail strings."
            )
    entry = (plugin_dir / manifest["entry"]).resolve()
    plugin_root = plugin_dir.resolve()
    if not is_relative_to(entry, plugin_root) or not entry.is_file():
        raise ContractError("Manifest entry must resolve to a file inside the plugin directory.")
    run_node_check(entry)
    source = entry.read_text(encoding="utf-8")
    hooks = [name for name, pattern in HOOK_PATTERNS.items() if pattern.search(source)]
    if not hooks:
        raise ContractError(
            "Plugin entry must export transformWebview, beforeLaunch, "
            "handleControlRequest, or a combination."
        )
    return {
        "id": plugin_id,
        "manifest": str(manifest_file),
        "entry": str(entry),
        "hooks": hooks,
        "permissions": permissions,
        "requiresRestart": bool(manifest.get("requiresRestart")),
        "reloadBoundaries": {
            "rendererRebuild": "transformWebview" in hooks,
            "runtimeRestart": bool(hooks),
            "launcherServiceReloadAfterBackendChange": (
                "handleControlRequest" in hooks
            ),
        },
    }


def scaffold_plugin(
    project_root: Path,
    plugin_id: str,
    name: str,
    version: str,
    description: str,
    category: str,
    hook: str,
    control_route: bool,
    permissions: list[dict[str, str]],
) -> dict[str, Any]:
    plugin_id = normalize_plugin_id(plugin_id)
    if not SEMVER_RE.fullmatch(version):
        raise ContractError("Plugin version must use semantic versioning.")
    if not name.strip() or not description.strip() or not category.strip():
        raise ContractError("Name, description, and category must be non-empty.")
    plugins_root = project_root / "plugins"
    plugins_root.mkdir(parents=True, exist_ok=True)
    target = plugins_root / plugin_id
    if target.exists() or target.is_symlink():
        raise ContractError(f"Plugin target already exists: {target}")
    stage = plugins_root / (
        f".{plugin_id}.next-{os.getpid()}-{secrets.token_hex(4)}"
    )
    try:
        stage.mkdir(mode=0o755)
        manifest = {
            "id": plugin_id,
            "name": name.strip(),
            "version": version,
            "description": description.strip(),
            "category": category.strip(),
            "entry": "./index.mjs",
            "requiresRestart": True,
            "permissions": permissions,
        }
        atomic_write_json(stage / "plugin.json", manifest, mode=0o644)
        (stage / "index.mjs").write_text(
            entry_source(plugin_id, hook, control_route), encoding="utf-8"
        )
        validation = validate_plugin_directory(
            stage, expected_id=plugin_id, enforce_directory_name=False
        )
        os.replace(stage, target)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    validation["manifest"] = str(target / "plugin.json")
    validation["entry"] = str(target / "index.mjs")
    validation["sourceCommit"] = "staged-directory-rename"
    return validation


def run_codeex_cli(
    project_root: Path,
    args: list[str],
    state_file: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if not node:
        raise ContractError("Node.js is required to run the Codeex plugin CLI.")
    environment = os.environ.copy()
    if state_file is not None:
        environment["CODEEX_PLUGIN_STATE"] = str(state_file.resolve())
    result = subprocess.run(
        [node, "scripts/plugins-cli.mjs", *args],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        detail = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part.strip()
        )
        raise ContractError(
            f"Codeex plugin CLI failed with exit code {result.returncode}: {detail}"
        )
    return result


def state_contains(state_file: Path, plugin_id: str) -> bool:
    state = load_json(state_file)
    installed = state.get("installed") if isinstance(state, dict) else None
    if not isinstance(installed, list) or not all(isinstance(item, str) for item in installed):
        raise ContractError(f"Invalid Codeex plugin state: {state_file}")
    return plugin_id in installed


def lifecycle_change(
    project_root: Path,
    plugin_id: str,
    installed: bool,
    state_file: Path | None,
) -> dict[str, Any]:
    plugin_id = normalize_plugin_id(plugin_id)
    validation = validate_plugin_directory(project_root / "plugins" / plugin_id)
    action = "install" if installed else "uninstall"
    result = run_codeex_cli(project_root, [action, plugin_id], state_file=state_file)
    if state_file is not None:
        observed = state_contains(state_file, plugin_id)
    else:
        marker = "●" if installed else "○"
        observed = any(
            line.strip().startswith(f"{marker} {plugin_id}")
            for line in result.stdout.splitlines()
        )
    if observed is not installed:
        raise ContractError(
            f"Codeex CLI returned success but {action} postcondition was not observed."
        )
    return {
        "summary": f"Codeex plugin {plugin_id} desired state is now {action}ed.",
        "pluginId": plugin_id,
        "desiredInstalled": installed,
        "activeRuntimeVerified": False,
        "restartRequired": validation["requiresRestart"],
        "stateCommit": "codeex-cli-atomic-rename",
    }


def command_scaffold(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_project_root(args.project_root)
    return {
        "summary": f"Created Codeex plugin source: {args.plugin_id}",
        **scaffold_plugin(
            root,
            args.plugin_id,
            args.name or default_display_name(args.plugin_id),
            args.version,
            args.description,
            args.category,
            args.hook,
            args.control_route,
            parse_permissions(args.permission),
        ),
    }


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_project_root(args.project_root)
    if args.plugin_id:
        plugin_ids = [normalize_plugin_id(args.plugin_id)]
    else:
        plugin_ids = sorted(
            entry.name
            for entry in (root / "plugins").iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        )
    validations = [
        validate_plugin_directory(root / "plugins" / plugin_id)
        for plugin_id in plugin_ids
    ]
    return {
        "summary": f"Validated {len(validations)} Codeex plugin source(s).",
        "plugins": validations,
    }


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_project_root(args.project_root)
    state_file = Path(args.state_file).expanduser().resolve() if args.state_file else None
    result = run_codeex_cli(root, ["list"], state_file=state_file)
    return {
        "summary": "Read Codeex desired plugin state.",
        "listing": [line for line in result.stdout.splitlines() if line.strip()],
        "activeRuntimeVerified": False,
    }


def command_lifecycle(args: argparse.Namespace, installed: bool) -> dict[str, Any]:
    root = resolve_project_root(args.project_root)
    state_file = Path(args.state_file).expanduser().resolve() if args.state_file else None
    return lifecycle_change(root, args.plugin_id, installed, state_file)


def command_exercise(args: argparse.Namespace) -> dict[str, Any]:
    root = resolve_project_root(args.project_root)
    plugin_id = normalize_plugin_id(args.plugin_id)
    source_validation = validate_plugin_directory(root / "plugins" / plugin_id)
    with tempfile.TemporaryDirectory(prefix="codeex-plugin-exercise-") as temporary:
        temporary_root = Path(temporary)
        state_file = temporary_root / "plugins.json"
        atomic_write_json(
            state_file, {"schemaVersion": 1, "installed": []}, mode=0o600
        )
        install_one = lifecycle_change(root, plugin_id, True, state_file)
        install_two = lifecycle_change(root, plugin_id, True, state_file)
        installed_observed = state_contains(state_file, plugin_id)
        uninstall_one = lifecycle_change(root, plugin_id, False, state_file)
        uninstall_two = lifecycle_change(root, plugin_id, False, state_file)
        uninstalled_observed = not state_contains(state_file, plugin_id)
        before_invalid = state_file.read_bytes()
        invalid_id = "codeex-contract-unknown-plugin"
        invalid = run_codeex_cli(
            root, ["install", invalid_id], state_file=state_file, check=False
        )
        invalid_rejected = invalid.returncode != 0
        invalid_preserved_state = state_file.read_bytes() == before_invalid

        fixture = temporary_root / "scaffold-fixture"
        (fixture / "plugins").mkdir(parents=True)
        scaffold_id = "atomic-smoke-plugin"
        scaffold_validation = scaffold_plugin(
            fixture,
            scaffold_id,
            "Atomic Smoke Plugin",
            "0.1.0",
            "Exercise staged Codeex plugin source creation without changing a live repository.",
            "Development Tools",
            "both",
            True,
            [],
        )
        duplicate_rejected = False
        try:
            scaffold_plugin(
                fixture,
                scaffold_id,
                "Atomic Smoke Plugin",
                "0.1.0",
                "Exercise occupied-target rejection.",
                "Development Tools",
                "both",
                True,
                [],
            )
        except ContractError:
            duplicate_rejected = True
        staging_clean = not any((fixture / "plugins").glob(".*.next-*"))
        state_mode = stat.S_IMODE(state_file.stat().st_mode)

    checks = {
        "sourceManifestValid": source_validation["id"] == plugin_id,
        "sourceHooksDetected": bool(source_validation["hooks"]),
        "scaffoldCommittedByRename": scaffold_validation["sourceCommit"]
        == "staged-directory-rename",
        "scaffoldDuplicateRejected": duplicate_rejected,
        "scaffoldStagingClean": staging_clean,
        "scaffoldControlHookDetected": (
            "handleControlRequest" in scaffold_validation["hooks"]
        ),
        "firstInstallObserved": installed_observed and install_one["desiredInstalled"],
        "duplicateInstallIdempotent": install_two["desiredInstalled"],
        "firstUninstallObserved": uninstalled_observed
        and not uninstall_one["desiredInstalled"],
        "duplicateUninstallIdempotent": not uninstall_two["desiredInstalled"],
        "unknownPluginRejected": invalid_rejected,
        "failedMutationPreservedState": invalid_preserved_state,
        "stateFilePrivateMode": state_mode == 0o600,
    }
    passed = all(checks.values())
    report = {
        "schema": "lov-codeex-creator/exercise/v1",
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "pluginId": plugin_id,
        "hooks": source_validation["hooks"],
        "checks": checks,
        "passed": passed,
        "liveStateMutated": False,
        "activeRuntimeVerified": False,
        "note": "Desired-state lifecycle used an isolated state file; runtime activation requires separate smoke evidence.",
    }
    if not passed:
        raise ContractError("Codeex plugin lifecycle exercise failed: " + json.dumps(checks))
    if args.output:
        output = Path(args.output).expanduser().resolve()
        atomic_write_json(output, report, mode=0o644)
        report["evidenceWritten"] = str(output)
    report["summary"] = f"Codeex plugin lifecycle exercise passed for {plugin_id}."
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and exercise Codeex runtime plugins without mutating live state during tests."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_project_root(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--project-root",
            help="Codeex repository root; falls back to CODEEX_PROJECT_ROOT or cwd.",
        )

    scaffold = subparsers.add_parser("scaffold", help="Create staged plugin source.")
    scaffold.add_argument("plugin_id")
    add_project_root(scaffold)
    scaffold.add_argument("--name")
    scaffold.add_argument("--version", default="0.1.0")
    scaffold.add_argument("--description", required=True)
    scaffold.add_argument("--category", default="Development Tools")
    scaffold.add_argument(
        "--hook",
        choices=("webview", "before-launch", "both", "control"),
        default="webview",
    )
    scaffold.add_argument(
        "--control-route",
        action="store_true",
        help="Also scaffold an authenticated handleControlRequest hook.",
    )
    scaffold.add_argument(
        "--permission",
        action="append",
        default=[],
        help="Repeatable Label:Detail declaration.",
    )

    validate = subparsers.add_parser("validate", help="Validate one or all plugins.")
    validate.add_argument("plugin_id", nargs="?")
    add_project_root(validate)

    status_parser = subparsers.add_parser("status", help="Read desired plugin state.")
    add_project_root(status_parser)
    status_parser.add_argument("--state-file", help="Use an isolated state file.")

    for action in ("install", "uninstall"):
        lifecycle = subparsers.add_parser(
            action, help=f"Commit desired {action} state through Codeex."
        )
        lifecycle.add_argument("plugin_id")
        add_project_root(lifecycle)
        lifecycle.add_argument("--state-file", help="Use an isolated state file.")

    exercise = subparsers.add_parser(
        "exercise", help="Exercise atomic source and isolated state transitions."
    )
    exercise.add_argument("plugin_id")
    add_project_root(exercise)
    exercise.add_argument("--output", help="Atomically write a JSON evidence report.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "scaffold":
            payload = command_scaffold(args)
        elif args.command == "validate":
            payload = command_validate(args)
        elif args.command == "status":
            payload = command_status(args)
        elif args.command == "install":
            payload = command_lifecycle(args, True)
        elif args.command == "uninstall":
            payload = command_lifecycle(args, False)
        elif args.command == "exercise":
            payload = command_exercise(args)
        else:
            parser.error(f"Unsupported command: {args.command}")
            return 2
        emit(payload, args.json)
        return 0
    except ContractError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
