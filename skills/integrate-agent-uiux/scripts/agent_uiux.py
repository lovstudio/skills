#!/usr/bin/env python3
"""Audit, scaffold, and verify reusable Agent conversation UI components."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


VERSION = "0.1.0"
SUPPORTED_STACKS = ("react-native", "react")
COMMON_FILES = ("types.ts", "model.ts", "markdown.ts")
PLATFORM_FILES = {
    "react-native": (
        "AgentMarkdown.tsx",
        "AgentTranscript.tsx",
        "AgentComposer.tsx",
        "AgentConversation.tsx",
    ),
    "react": (
        "AgentMarkdown.tsx",
        "AgentTranscript.tsx",
        "AgentComposer.tsx",
        "AgentConversation.tsx",
        "agent-uiux.css",
    ),
}
PLACEHOLDER_MARKERS = ("TO" + "DO:", "TO" + "DO：")
REQUIRED_TOKENS = {
    "types.ts": (
        "AgentMessage",
        "AgentSessionState",
        "PendingInteraction",
        "clientRequestId",
    ),
    "model.ts": (
        "filterAgentMessages",
        "groupAdjacentTools",
        "safeAgentLink",
        "createAgentRequestId",
    ),
    "AgentConversation.tsx": (
        "AgentTranscript",
        "AgentComposer",
        "jumpToLatest",
    ),
}


class AgentUiuxError(RuntimeError):
    """A user-actionable integration error."""


@dataclass(frozen=True)
class ProjectAudit:
    project: Path
    package_json: Path
    package_manager: str
    stack: str | None
    source_root: Path
    default_component_dir: Path
    dependencies: tuple[str, ...]
    scripts: dict[str, str]
    existing_agent_paths: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        relative = lambda value: str(value.relative_to(self.project))
        return {
            "schema": "lovstudio/agent-uiux-audit/v1",
            "version": VERSION,
            "project": self.project.name,
            "package_json": relative(self.package_json),
            "package_manager": self.package_manager,
            "stack": self.stack,
            "supported": self.stack in SUPPORTED_STACKS,
            "source_root": relative(self.source_root) or ".",
            "default_component_dir": relative(self.default_component_dir),
            "dependencies": list(self.dependencies),
            "scripts": self.scripts,
            "existing_agent_paths": list(self.existing_agent_paths),
            "next": (
                "scaffold"
                if self.stack in SUPPORTED_STACKS
                else "implement from references/integration-contract.md"
            ),
        }


def context_id(command: str, project: Path) -> str:
    digest = hashlib.sha256(f"{command}:{project.resolve()}".encode()).hexdigest()[:10]
    return f"agent-uiux-{command}-{digest}"


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AgentUiuxError("package.json was not found") from exc
    except json.JSONDecodeError as exc:
        raise AgentUiuxError(f"package.json is invalid JSON at line {exc.lineno}") from exc
    if not isinstance(value, dict):
        raise AgentUiuxError("package.json must contain a JSON object")
    return value


def dependency_names(package: dict[str, Any]) -> tuple[str, ...]:
    names: set[str] = set()
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(field, {})
        if isinstance(values, dict):
            names.update(str(name) for name in values)
    return tuple(sorted(names))


def detect_stack(names: Iterable[str]) -> str | None:
    dependencies = set(names)
    if "react-native" in dependencies or "expo" in dependencies:
        return "react-native"
    if "react" in dependencies and (
        "react-dom" in dependencies or "next" in dependencies or "vite" in dependencies
    ):
        return "react"
    return None


def detect_package_manager(project: Path) -> str:
    for filename, manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lockb", "bun"),
        ("bun.lock", "bun"),
        ("package-lock.json", "npm"),
    ):
        if project.joinpath(filename).exists():
            return manager
    return "unknown"


def find_existing_agent_paths(project: Path) -> tuple[str, ...]:
    matches: list[str] = []
    for base_name in ("src", "app", "components"):
        base = project / base_name
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if len(matches) >= 24:
                break
            if path.is_dir() or any(part in {"node_modules", "dist", "build"} for part in path.parts):
                continue
            lowered = path.name.lower()
            if any(token in lowered for token in ("agent", "chat", "conversation", "transcript")):
                matches.append(str(path.relative_to(project)))
    return tuple(matches)


def audit_project(project_value: str | Path) -> ProjectAudit:
    project = Path(project_value).expanduser().resolve()
    if not project.is_dir():
        raise AgentUiuxError("project directory does not exist")
    package_json = project / "package.json"
    package = read_json(package_json)
    dependencies = dependency_names(package)
    stack = detect_stack(dependencies)
    source_root = project / "src" if (project / "src").is_dir() else project
    default_component_dir = source_root / "components" / "agent-uiux"
    raw_scripts = package.get("scripts", {})
    scripts = {
        name: str(command)
        for name, command in raw_scripts.items()
        if isinstance(raw_scripts, dict)
        and name in {"format", "lint", "typecheck", "test", "build"}
    }
    return ProjectAudit(
        project=project,
        package_json=package_json,
        package_manager=detect_package_manager(project),
        stack=stack,
        source_root=source_root,
        default_component_dir=default_component_dir,
        dependencies=dependencies,
        scripts=scripts,
        existing_agent_paths=find_existing_agent_paths(project),
    )


def resolve_component_dir(audit: ProjectAudit, value: str | None) -> Path:
    target = audit.default_component_dir if value is None else (audit.project / value).resolve()
    try:
        target.relative_to(audit.project)
    except ValueError as exc:
        raise AgentUiuxError("component directory must stay inside the target project") from exc
    return target


def asset_root() -> Path:
    return Path(__file__).resolve().parent.parent / "assets"


def files_for_stack(stack: str) -> tuple[str, ...]:
    return (*COMMON_FILES, *PLATFORM_FILES[stack])


def render_integration_guide(stack: str, component_dir: Path, project: Path) -> str:
    relative = component_dir.relative_to(project)
    css_step = (
        "1. Import `agent-uiux.css` once from the host application entrypoint.\n"
        if stack == "react"
        else "1. Keep the component inside the host SafeArea/keyboard ownership boundary.\n"
    )
    return f"""# Agent UI Integration\n\nStack: `{stack}`  \nComponent directory: `{relative}`  \nTemplate version: `{VERSION}`\n\n## Required host work\n\n{css_step}2. Create one adapter from provider/session data to the types in `types.ts`.\n3. Render `AgentConversation` with controlled messages, session, draft, attachments, and callbacks.\n4. Map host brand tokens through the theme prop and visible strings through the copy prop.\n5. Run the host format, lint, typecheck, test, and build commands.\n6. Exercise tool progress, Markdown, pending interaction, send failure/retry, and a final response.\n\nThe components do not fetch, persist, authenticate, or reconnect. Those remain host responsibilities.\n"""


def scaffold(
    audit: ProjectAudit,
    stack: str,
    target: Path,
    *,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    if stack not in SUPPORTED_STACKS:
        raise AgentUiuxError(f"unsupported stack: {stack}")
    sources = [
        *((asset_root() / "common" / name, name) for name in COMMON_FILES),
        *((asset_root() / stack / name, name) for name in PLATFORM_FILES[stack]),
    ]
    missing = [str(source) for source, _ in sources if not source.is_file()]
    if missing:
        raise AgentUiuxError(f"Skill assets are incomplete: {', '.join(missing)}")
    occupied = target.exists() and any(target.iterdir())
    if occupied and not force:
        raise AgentUiuxError(
            f"component target is occupied: {target.relative_to(audit.project)}; "
            "choose --component-dir or explicitly authorize --force"
        )
    planned = [str((target / name).relative_to(audit.project)) for _, name in sources]
    planned.extend(
        str((target / name).relative_to(audit.project))
        for name in ("INTEGRATION.md", "agent-uiux-manifest.json")
    )
    result = {
        "schema": "lovstudio/agent-uiux-scaffold/v1",
        "version": VERSION,
        "stack": stack,
        "target": str(target.relative_to(audit.project)),
        "dry_run": dry_run,
        "files": planned,
    }
    if dry_run:
        return result
    target.mkdir(parents=True, exist_ok=True)
    for source, name in sources:
        shutil.copy2(source, target / name)
    (target / "INTEGRATION.md").write_text(
        render_integration_guide(stack, target, audit.project), encoding="utf-8"
    )
    manifest = {
        "schema": "lovstudio/agent-uiux-template/v1",
        "version": VERSION,
        "stack": stack,
        "files": list(files_for_stack(stack)),
    }
    (target / "agent-uiux-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def verify(audit: ProjectAudit, stack: str, target: Path) -> dict[str, Any]:
    errors: list[str] = []
    expected = files_for_stack(stack)
    for name in expected:
        path = target / name
        if not path.is_file():
            errors.append(f"missing {path.relative_to(audit.project)}")
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in PLACEHOLDER_MARKERS):
            errors.append(f"unresolved placeholder in {path.relative_to(audit.project)}")
        for token in REQUIRED_TOKENS.get(name, ()):
            if token not in text:
                errors.append(f"{path.relative_to(audit.project)} is missing contract token {token}")
    manifest_path = target / "agent-uiux-manifest.json"
    if not manifest_path.is_file():
        errors.append(f"missing {manifest_path.relative_to(audit.project)}")
    else:
        manifest = read_json(manifest_path)
        if manifest.get("schema") != "lovstudio/agent-uiux-template/v1":
            errors.append("template manifest schema is invalid")
        if manifest.get("stack") != stack:
            errors.append("template manifest stack does not match verification stack")
    dependency_error = (
        stack == "react-native" and "react-native" not in audit.dependencies and "expo" not in audit.dependencies
    ) or (
        stack == "react" and "react" not in audit.dependencies
    )
    if dependency_error:
        errors.append(f"package.json does not declare the required {stack} runtime")
    result = {
        "schema": "lovstudio/agent-uiux-verification/v1",
        "version": VERSION,
        "stack": stack,
        "target": str(target.relative_to(audit.project)),
        "passed": not errors,
        "checked_files": list(expected),
        "errors": errors,
        "host_commands": audit.scripts,
    }
    if errors:
        raise AgentUiuxError("; ".join(errors))
    return result


def print_result(value: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return
    for key, item in value.items():
        if isinstance(item, (dict, list)):
            print(f"{key}={json.dumps(item, ensure_ascii=False)}")
        else:
            print(f"{key}={item}")


def run_self_test() -> dict[str, Any]:
    checked: list[str] = []
    with tempfile.TemporaryDirectory(prefix="agent-uiux-self-test-") as temporary:
        root = Path(temporary)
        fixtures = {
            "react-native": {"dependencies": {"expo": "1", "react": "1", "react-native": "1"}},
            "react": {"dependencies": {"react": "1", "react-dom": "1", "vite": "1"}},
        }
        for stack, package in fixtures.items():
            project = root / stack
            (project / "src").mkdir(parents=True)
            (project / "package.json").write_text(json.dumps(package), encoding="utf-8")
            audit = audit_project(project)
            if audit.stack != stack:
                raise AgentUiuxError(f"self-test detected {audit.stack} instead of {stack}")
            target = resolve_component_dir(audit, None)
            preview = scaffold(audit, stack, target, dry_run=True, force=False)
            if not preview["dry_run"] or target.exists():
                raise AgentUiuxError("dry-run changed the fixture")
            scaffold(audit, stack, target, dry_run=False, force=False)
            verify(audit, stack, target)
            try:
                scaffold(audit, stack, target, dry_run=False, force=False)
            except AgentUiuxError:
                pass
            else:
                raise AgentUiuxError("occupied target was not rejected")
            checked.append(stack)
    return {
        "schema": "lovstudio/agent-uiux-self-test/v1",
        "version": VERSION,
        "passed": True,
        "checked_stacks": checked,
        "checks": ["detection", "dry-run", "scaffold", "verify", "collision refusal"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit", help="inspect a host project")
    audit_parser.add_argument("project")
    audit_parser.add_argument("--format", choices=("text", "json"), default="text")
    scaffold_parser = subparsers.add_parser("scaffold", help="copy target-stack components")
    scaffold_parser.add_argument("project")
    scaffold_parser.add_argument("--stack", choices=SUPPORTED_STACKS)
    scaffold_parser.add_argument("--component-dir")
    scaffold_parser.add_argument("--dry-run", action="store_true")
    scaffold_parser.add_argument("--force", action="store_true")
    scaffold_parser.add_argument("--format", choices=("text", "json"), default="text")
    verify_parser = subparsers.add_parser("verify", help="verify scaffold structure")
    verify_parser.add_argument("project")
    verify_parser.add_argument("--stack", choices=SUPPORTED_STACKS)
    verify_parser.add_argument("--component-dir")
    verify_parser.add_argument("--format", choices=("text", "json"), default="text")
    self_test_parser = subparsers.add_parser("self-test", help="exercise both bundled scaffolds")
    self_test_parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project = Path(getattr(args, "project", ".")).expanduser().resolve()
    try:
        if args.command == "self-test":
            print_result(run_self_test(), args.format)
            return 0
        audit = audit_project(project)
        if args.command == "audit":
            print_result(audit.as_dict(), args.format)
            return 0
        stack = args.stack or audit.stack
        if stack not in SUPPORTED_STACKS:
            raise AgentUiuxError(
                "could not detect React Native/Expo or React; pass a supported --stack only "
                "when the package manifest genuinely uses it"
            )
        target = resolve_component_dir(audit, args.component_dir)
        if args.command == "scaffold":
            print_result(
                scaffold(audit, stack, target, dry_run=args.dry_run, force=args.force),
                args.format,
            )
            return 0
        if args.command == "verify":
            print_result(verify(audit, stack, target), args.format)
            return 0
        raise AgentUiuxError(f"unknown command: {args.command}")
    except AgentUiuxError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"context_id={context_id(args.command, project)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
