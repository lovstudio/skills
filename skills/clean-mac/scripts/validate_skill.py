#!/usr/bin/env python3
"""Validate a portable local Skill source directory."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML is required. Install it with: python3 -m pip install PyYAML",
        file=sys.stderr,
    )
    raise SystemExit(2)


FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "allowed-tools",
    "metadata",
}
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt", ".svg", ".py"}
JUNK_NAMES = {"__pycache__", ".DS_Store"}
JUNK_SUFFIXES = {".pyc", ".pyo"}
SKIP_DIRS = {".git", "dist", ".venv", "venv", "node_modules"}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
SKILL_PATH_RE = re.compile(r"\$(SKILL_DIR|KIT_DIR)/([A-Za-z0-9_./-]+)")


class ValidationFailure(Exception):
    """Raised when source metadata cannot be parsed."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", value).strip() if isinstance(value, str) else ""


def split_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = read_text(path)
    if not text.startswith("---\n"):
        raise ValidationFailure(f"{path}: missing YAML frontmatter")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise ValidationFailure(f"{path}: frontmatter is not closed")
    try:
        data = yaml.safe_load(text[4:marker])
    except yaml.YAMLError as exc:
        raise ValidationFailure(
            f"{path}: standard YAML parser rejected frontmatter: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise ValidationFailure(f"{path}: frontmatter must be a mapping")
    return data, text[marker + 5 :]


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            yield path


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_skill_file(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        data, body = split_frontmatter(path)
    except ValidationFailure as exc:
        errors.append(str(exc))
        return None

    unexpected = sorted(set(data) - FRONTMATTER_KEYS)
    if unexpected:
        errors.append(f"{path}: unsupported frontmatter keys: {', '.join(unexpected)}")

    name = compact_text(data.get("name"))
    if not NAME_RE.fullmatch(name) or len(name) > 64:
        errors.append(f"{path}: name must be kebab-case and at most 64 characters")

    description = compact_text(data.get("description"))
    if not 50 <= len(description) <= 200:
        errors.append(
            f"{path}: description must contain 50-200 characters "
            f"(found {len(description)})"
        )

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        errors.append(f"{path}: metadata must be a mapping")
    else:
        if not compact_text(metadata.get("author")):
            errors.append(f"{path}: metadata.author is required")
        if not SEMVER_RE.fullmatch(compact_text(metadata.get("version"))):
            errors.append(f"{path}: metadata.version must use SemVer")
        tags = metadata.get("tags")
        if not isinstance(tags, list) or not tags or not all(
            isinstance(tag, str) and tag.strip() for tag in tags
        ):
            errors.append(f"{path}: metadata.tags must be a non-empty list")
        dependencies = metadata.get("dependencies", [])
        if not isinstance(dependencies, list):
            errors.append(f"{path}: metadata.dependencies must be a list")

    trigger_block = re.search(
        r"(?ms)^##\s+Triggers\s*$([\s\S]*?)(?=^##\s+|\Z)", body
    )
    if not trigger_block:
        errors.append(f"{path}: add an explicit '## Triggers' section")
    else:
        block = trigger_block.group(1)
        if len(re.findall(r"(?m)^\s*-\s+\S", block)) < 3:
            errors.append(f"{path}: add two activation examples and one non-trigger")
        if not re.search(r"[\u3400-\u9fff]", block):
            errors.append(f"{path}: add a concrete Chinese trigger phrase")
        if not re.search(r"(?i)\b(?:the|a|an|create|build|help|publish|review|use)\b", block):
            errors.append(f"{path}: add a concrete English trigger phrase")
    if not re.search(
        r"(?mi)^###\s+(?:Do not activate when|Non-triggers?|不应触发|不要触发)\s*$",
        body,
    ):
        errors.append(f"{path}: add explicit non-trigger conditions")
    if len(read_text(path).splitlines()) >= 500:
        errors.append(f"{path}: keep SKILL.md below 500 lines")
    if not body.strip():
        errors.append(f"{path}: body is empty")
    return data


def load_yaml(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(read_text(path))
    except yaml.YAMLError as exc:
        errors.append(f"{path}: standard YAML parser rejected file: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: expected a YAML mapping")
        return None
    return data


def validate_kit(root: Path, skill_names: set[str], errors: list[str]) -> None:
    manifest = root / "kit.yaml"
    if not manifest.exists():
        return
    data = load_yaml(manifest, errors)
    if data is None:
        return
    modules = data.get("modules")
    if not isinstance(modules, list) or not modules:
        errors.append(f"{manifest}: modules must be a non-empty list")
        return
    module_ids: set[str] = set()
    for index, module in enumerate(modules):
        label = f"{manifest}: modules[{index}]"
        if not isinstance(module, dict):
            errors.append(f"{label}: expected a mapping")
            continue
        module_id = compact_text(module.get("id"))
        skill_name = compact_text(module.get("skill"))
        relative = compact_text(module.get("path"))
        if not module_id or module_id in module_ids:
            errors.append(f"{label}: id is required and must be unique")
        module_ids.add(module_id)
        module_path = (root / relative).resolve()
        if (
            not relative
            or not is_relative_to(module_path, root.resolve())
            or not (module_path / "SKILL.md").is_file()
        ):
            errors.append(f"{label}: missing module at '{relative}/SKILL.md'")
        if skill_name not in skill_names:
            errors.append(f"{label}: unresolved child skill '{skill_name}'")
    pipelines = data.get("pipelines")
    if not isinstance(pipelines, dict) or not pipelines:
        errors.append(f"{manifest}: pipelines must be a non-empty mapping")
        return
    for pipeline, sequence in pipelines.items():
        if not isinstance(sequence, list) or not sequence:
            errors.append(f"{manifest}: pipeline '{pipeline}' must be a non-empty list")
            continue
        missing = [str(item) for item in sequence if item not in module_ids]
        if missing:
            errors.append(
                f"{manifest}: pipeline '{pipeline}' has unknown modules: "
                + ", ".join(missing)
            )


def validate_local_references(root: Path, errors: list[str]) -> None:
    for path in iter_files(root):
        if path.suffix.lower() != ".md":
            continue
        text = read_text(path)
        for raw in MARKDOWN_LINK_RE.findall(text):
            target = raw.strip().split(maxsplit=1)[0].strip("<>").split("#", 1)[0]
            if (
                not target
                or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I)
                or any(token in target for token in ("TODO", "{", "}"))
            ):
                continue
            if not (path.parent / target).resolve().exists():
                errors.append(f"{path}: broken local link '{target}'")
        skill_root = path.parent if path.name == "SKILL.md" else root
        for variable, target in SKILL_PATH_RE.findall(text):
            if "TODO" in target:
                continue
            base = skill_root if variable == "SKILL_DIR" else root
            resolved = (base / target.rstrip(".,;:)")).resolve()
            if not is_relative_to(resolved, root.resolve()) or not resolved.exists():
                errors.append(f"{path}: missing required resource '${variable}/{target}'")


def validate_runtime_manifest(root: Path, root_data: dict[str, Any], errors: list[str]) -> None:
    manifest = root / "skill.yaml"
    if not manifest.is_file():
        errors.append(f"{manifest}: runtime manifest is required")
        return
    data = load_yaml(manifest, errors)
    if data is None:
        return
    if data.get("schema") != "skill-manifest/v1":
        errors.append(f"{manifest}: schema must be skill-manifest/v1")
    if compact_text(data.get("id")) != compact_text(root_data.get("name")):
        errors.append(f"{manifest}: id must match the root SKILL.md name")
    if compact_text(data.get("version")) != compact_text(root_data.get("metadata", {}).get("version")):
        errors.append(f"{manifest}: version must match the root SKILL.md metadata.version")
    if data.get("runtime") != "skill-runtime/v1":
        errors.append(f"{manifest}: runtime must be skill-runtime/v1")
    context = data.get("context")
    if not isinstance(context, dict):
        errors.append(f"{manifest}: context must be an object")
        return
    for source in ("profile", "preferences"):
        block = context.get(source)
        if not isinstance(block, dict) or not isinstance(block.get("fields"), list):
            errors.append(f"{manifest}: context.{source}.fields must be a list")
    interaction = context.get("interaction")
    if not isinstance(interaction, dict) or not isinstance(interaction.get("ask_missing"), bool):
        errors.append(f"{manifest}: context.interaction.ask_missing must be boolean")


def validate_hygiene(root: Path, errors: list[str]) -> None:
    private_path = re.compile(r"(?:/Users/[^/\s]+/|[A-Za-z]:\\\\Users\\\\[^\\\s]+\\\\)")
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.name in JUNK_NAMES or path.suffix.lower() in JUNK_SUFFIXES:
            errors.append(f"{path}: generated/cache artifact must not ship")
    for path in iter_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES or path.name == "validate_skill.py":
            continue
        text = read_text(path)
        if private_path.search(text):
            errors.append(f"{path}: contains a private absolute user path")
        if path.name != "init_skill.py" and re.search(r"\bTODO\s*[:：]", text):
            errors.append(f"{path}: unresolved TODO placeholder")
    for relative in ("workbuddy", "scripts/build_workbuddy.py"):
        if (root / relative).exists():
            errors.append(
                f"{root / relative}: platform distribution artifacts belong to skill-publish"
            )


def validate_source(root: Path, errors: list[str]) -> None:
    root_skill = root / "SKILL.md"
    skill_files = [root_skill, *sorted((root / "skills").glob("*/SKILL.md"))]
    if not root_skill.is_file():
        errors.append(f"{root_skill}: file is required")
        return
    parsed: list[tuple[Path, dict[str, Any]]] = []
    for path in skill_files:
        data = validate_skill_file(path, errors)
        if data:
            parsed.append((path, data))
    names = {compact_text(data.get("name")) for _, data in parsed}
    if len(names) != len(parsed):
        errors.append(f"{root}: every embedded Skill must have a unique name")
    validate_kit(root, names, errors)
    if parsed:
        validate_runtime_manifest(root, parsed[0][1], errors)

    readme = root / "README.md"
    if not readme.is_file():
        errors.append(f"{readme}: file is required")
    elif parsed:
        metadata = parsed[0][1].get("metadata")
        version = compact_text(metadata.get("version")) if isinstance(metadata, dict) else ""
        if version and f"version-{version}-" not in read_text(readme):
            errors.append(f"{readme}: version badge must match {version}")

    validate_hygiene(root, errors)
    validate_local_references(root, errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Local Skill source directory")
    args = parser.parse_args()
    root = args.path.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: directory does not exist: {root}", file=sys.stderr)
        return 2
    errors: list[str] = []
    validate_source(root, errors)
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASSED: source validation ({root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
