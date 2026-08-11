#!/usr/bin/env python3
"""Validate Skill Publisher source Skills and WorkBuddy distributions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML is required for standards-compliant frontmatter parsing. "
        "Install it with: python3 -m pip install PyYAML",
        file=sys.stderr,
    )
    raise SystemExit(2)


SOURCE_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "allowed-tools",
    "metadata",
}
WORKBUDDY_FRONTMATTER_KEYS = {
    "name",
    "description",
    "version",
    "author",
    "source_type",
    "clawhub_slug",
    "skillhub_slug",
    "git_url",
}
SOURCE_LOCATORS = ("clawhub_slug", "skillhub_slug", "git_url")
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt", ".svg", ".py"}
JUNK_NAMES = {"__pycache__", ".DS_Store"}
JUNK_SUFFIXES = {".pyc", ".pyo"}
SKIP_DIRS = {".git", "dist", ".venv", "venv", "node_modules"}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
SKILL_PATH_RE = re.compile(
    r"\$(SKILL_DIR|KIT_DIR)/([A-Za-z0-9_./-]+)"
)


class ValidationFailure(Exception):
    """Raised when a validation input cannot be parsed."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = read_text(path)
    if not text.startswith("---\n"):
        raise ValidationFailure(f"{path}: missing YAML frontmatter")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise ValidationFailure(f"{path}: frontmatter is not closed")
    raw = text[4:marker]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValidationFailure(
            f"{path}: standard YAML parser rejected frontmatter: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise ValidationFailure(f"{path}: frontmatter must be a YAML mapping")
    return data, text[marker + 5 :]


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", value).strip() if isinstance(value, str) else ""


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            yield path


def validate_name(name: Any, label: str, errors: list[str]) -> None:
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        errors.append(f"{label}: name must be kebab-case")
    elif len(name) > 64:
        errors.append(f"{label}: name must be at most 64 characters")


def validate_description(
    value: Any,
    label: str,
    errors: list[str],
    minimum: int = 50,
    maximum: int = 200,
) -> None:
    description = compact_text(value)
    if not minimum <= len(description) <= maximum:
        errors.append(
            f"{label}: description must contain {minimum}-{maximum} characters "
            f"(found {len(description)})"
        )
    if "<" in description or ">" in description:
        errors.append(f"{label}: description must not contain angle brackets")


def validate_triggers(body: str, label: str, errors: list[str]) -> None:
    if not re.search(r"(?mi)^##\s+Triggers\s*$", body):
        errors.append(f"{label}: add an explicit '## Triggers' section")
    if not re.search(
        (
            r"(?mi)^###\s+(?:Do not activate when|Non-triggers?|"
            r"不应触发|不要触发)\s*$"
        ),
        body,
    ):
        errors.append(
            f"{label}: Triggers must include explicit non-trigger conditions"
        )
    trigger_block = re.search(
        r"(?ms)^##\s+Triggers\s*$([\s\S]*?)(?=^##\s+|\Z)", body
    )
    if trigger_block and len(re.findall(r"(?m)^\s*-\s+\S", trigger_block.group(1))) < 3:
        errors.append(
            f"{label}: Triggers should include at least two activation examples "
            "and one non-trigger condition"
        )


def validate_frontmatter(
    path: Path, target: str, errors: list[str]
) -> tuple[dict[str, Any], str] | None:
    try:
        data, body = split_frontmatter(path)
    except ValidationFailure as exc:
        errors.append(str(exc))
        return None

    allowed = (
        SOURCE_FRONTMATTER_KEYS
        if target == "source"
        else WORKBUDDY_FRONTMATTER_KEYS
    )
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        errors.append(
            f"{path}: unsupported {target} frontmatter keys: "
            + ", ".join(unexpected)
        )

    validate_name(data.get("name"), str(path), errors)
    validate_description(data.get("description"), str(path), errors)
    validate_triggers(body, str(path), errors)
    if not body.strip():
        errors.append(f"{path}: body is empty")

    if target == "source":
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{path}: metadata must be a mapping")
        else:
            if not compact_text(metadata.get("author")):
                errors.append(f"{path}: metadata.author is required")
            version = compact_text(metadata.get("version"))
            if not SEMVER_RE.fullmatch(version):
                errors.append(f"{path}: metadata.version must use SemVer")
            tags = metadata.get("tags")
            if not isinstance(tags, list) or not tags or not all(
                isinstance(tag, str) and tag.strip() for tag in tags
            ):
                errors.append(f"{path}: metadata.tags must be a non-empty list")
    else:
        version = compact_text(data.get("version"))
        if not SEMVER_RE.fullmatch(version):
            errors.append(f"{path}: version must use SemVer")
        if not compact_text(data.get("author")):
            errors.append(f"{path}: author is required")
        if data.get("source_type") not in {"git", "clawhub", "skillhub"}:
            errors.append(
                f"{path}: source_type must be git, clawhub, or skillhub"
            )
        if not any(compact_text(data.get(key)) for key in SOURCE_LOCATORS):
            errors.append(
                f"{path}: add one source locator: " + ", ".join(SOURCE_LOCATORS)
            )
    return data, body


def validate_todos(paths: Iterable[Path], errors: list[str]) -> None:
    for path in paths:
        if path.is_file() and re.search(r"\bTODO\s*[:：]", read_text(path)):
            errors.append(f"{path}: unresolved TODO placeholder")


def validate_junk(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.name in JUNK_NAMES or path.suffix.lower() in JUNK_SUFFIXES:
            errors.append(f"{path}: generated/cache artifact must not be released")


def validate_private_paths(root: Path, errors: list[str]) -> None:
    private_path = re.compile(
        r"(?:/Users/[^/\s]+/|[A-Za-z]:\\\\Users\\\\[^\\\\\s]+\\\\)"
    )
    for path in iter_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.name == "validate_skill.py":
            continue
        if private_path.search(read_text(path)):
            errors.append(f"{path}: contains a private absolute user path")


def normalize_link_target(raw: str) -> str:
    target = raw.strip().split(maxsplit=1)[0].strip("<>")
    return target.split("#", 1)[0]


def validate_local_references(root: Path, errors: list[str]) -> None:
    for path in iter_files(root):
        if path.suffix.lower() != ".md":
            continue
        text = read_text(path)
        for raw in MARKDOWN_LINK_RE.findall(text):
            target = normalize_link_target(raw)
            if (
                not target
                or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I)
                or target.startswith("#")
                or any(token in target for token in ("TODO", "{", "}"))
            ):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"{path}: broken local link '{target}'")
        skill_root = path.parent
        current = path.parent
        while current != root.parent:
            if (current / "SKILL.md").is_file():
                skill_root = current
                break
            if current == root:
                break
            current = current.parent
        kit_root = skill_root
        current = path.parent
        while current != root.parent:
            if (current / "kit.yaml").is_file():
                kit_root = current
                break
            if current == root:
                break
            current = current.parent
        for variable, target in SKILL_PATH_RE.findall(text):
            if "TODO" in target:
                continue
            base = skill_root if variable == "SKILL_DIR" else kit_root
            resolved = (base / target.rstrip(".,;:)")).resolve()
            if not is_relative_to(resolved, root.resolve()) or not resolved.exists():
                errors.append(
                    f"{path}: missing or external required resource "
                    f"'${variable}/{target}'"
                )


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
            errors.append(f"{label} must be a mapping")
            continue
        module_id = compact_text(module.get("id"))
        skill = compact_text(module.get("skill"))
        relative = compact_text(module.get("path"))
        if not module_id or module_id in module_ids:
            errors.append(f"{label}: id is required and must be unique")
        module_ids.add(module_id)
        if skill not in skill_names:
            errors.append(f"{label}: unresolved child skill '{skill}'")
        module_path = (root / relative).resolve()
        if (
            not relative
            or not is_relative_to(module_path, root.resolve())
            or not (module_path / "SKILL.md").is_file()
        ):
            errors.append(
                f"{label}: missing self-contained module at '{relative}/SKILL.md'"
            )
        else:
            try:
                module_data, _ = split_frontmatter(module_path / "SKILL.md")
            except ValidationFailure as exc:
                errors.append(str(exc))
            else:
                actual_name = compact_text(module_data.get("name"))
                if actual_name != skill:
                    errors.append(
                        f"{label}: expected Skill name '{skill}' at "
                        f"'{relative}/SKILL.md', found '{actual_name}'"
                    )
    pipelines = data.get("pipelines")
    if pipelines is not None:
        if not isinstance(pipelines, dict):
            errors.append(f"{manifest}: pipelines must be a mapping")
        else:
            for pipeline, sequence in pipelines.items():
                if not isinstance(sequence, list) or not sequence:
                    errors.append(
                        f"{manifest}: pipeline '{pipeline}' must be a non-empty list"
                    )
                    continue
                missing = [item for item in sequence if item not in module_ids]
                if missing:
                    errors.append(
                        f"{manifest}: pipeline '{pipeline}' has unknown modules: "
                        + ", ".join(map(str, missing))
                    )


def validate_dependencies(
    skill_data: list[tuple[Path, dict[str, Any]]],
    names: set[str],
    errors: list[str],
    require_self_contained: bool,
) -> None:
    for path, data in skill_data:
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            continue
        dependencies = metadata.get("dependencies", [])
        if not isinstance(dependencies, list):
            errors.append(f"{path}: metadata.dependencies must be a list")
            continue
        for dependency in dependencies:
            name = (
                dependency
                if isinstance(dependency, str)
                else dependency.get("skill")
                if isinstance(dependency, dict)
                else ""
            )
            if not name:
                errors.append(f"{path}: dependency entries need a skill name")
            elif not isinstance(name, str) or not NAME_RE.fullmatch(name):
                errors.append(f"{path}: dependency names must be kebab-case")
            elif require_self_contained and name not in names:
                errors.append(
                    f"{path}: unresolved required dependency '{name}'; "
                    "embed it in the Skill Kit before release"
                )


def validate_readme_version(
    root: Path, root_data: dict[str, Any] | None, errors: list[str]
) -> None:
    readme = root / "README.md"
    if not readme.is_file():
        errors.append(f"{readme}: required for Skill Publisher source repositories")
        return
    if root_data is None:
        return
    metadata = root_data.get("metadata")
    if not isinstance(metadata, dict):
        return
    version = compact_text(metadata.get("version"))
    if version and f"version-{version}-" not in read_text(readme):
        errors.append(
            f"{readme}: version badge does not match SKILL.md version {version}"
        )


def validate_source(
    root: Path,
    errors: list[str],
    require_self_contained: bool = False,
) -> None:
    skill_files = [root / "SKILL.md", *sorted((root / "skills").glob("*/SKILL.md"))]
    if not skill_files[0].is_file():
        errors.append(f"{skill_files[0]}: file is required")
        return
    parsed: list[tuple[Path, dict[str, Any]]] = []
    root_data: dict[str, Any] | None = None
    for path in skill_files:
        result = validate_frontmatter(path, "source", errors)
        if result:
            data, _ = result
            parsed.append((path, data))
            if path == root / "SKILL.md":
                root_data = data
    names = {
        compact_text(data.get("name"))
        for _, data in parsed
        if compact_text(data.get("name"))
    }
    if len(names) != len(parsed):
        errors.append(f"{root}: every embedded Skill must have a unique name")
    validate_dependencies(parsed, names, errors, require_self_contained)
    validate_kit(root, names, errors)
    validate_readme_version(root, root_data, errors)
    validate_todos([root / "SKILL.md", root / "README.md", *skill_files[1:]], errors)
    validate_junk(root, errors)
    validate_private_paths(root, errors)
    validate_local_references(root, errors)
    if (root / "workbuddy").exists():
        errors.append(
            f"{root / 'workbuddy'}: keep platform metadata outside canonical source"
        )


def validate_connector_meta(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        errors.append(f"{path}: required for WorkBuddy distribution")
        return None
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: expected a JSON object")
        return None
    required = (
        "name",
        "name_zh",
        "name_en",
        "description",
        "description_zh",
        "description_en",
        "source",
        "type",
        "version",
        "examples_zh",
        "examples_en",
        "source_type",
    )
    for field in required:
        if field not in data:
            errors.append(f"{path}: missing '{field}'")
    if not 2 <= len(compact_text(data.get("name"))) <= 20:
        errors.append(f"{path}: name should contain 2-20 characters")
    for field in ("description_zh", "description_en"):
        value = compact_text(data.get(field))
        if not 20 <= len(value) <= 100:
            errors.append(f"{path}: {field} should contain 20-100 characters")
    source = compact_text(data.get("source"))
    if not NAME_RE.fullmatch(source):
        errors.append(f"{path}: source must be a globally unique kebab-case ID")
    if data.get("type") != "skill-only":
        errors.append(f"{path}: type must be 'skill-only'")
    if not SEMVER_RE.fullmatch(compact_text(data.get("version"))):
        errors.append(f"{path}: version must use SemVer")
    if data.get("source_type") not in {"git", "clawhub", "skillhub"}:
        errors.append(f"{path}: source_type must be git, clawhub, or skillhub")
    if not any(compact_text(data.get(key)) for key in SOURCE_LOCATORS):
        errors.append(
            f"{path}: add one source locator: " + ", ".join(SOURCE_LOCATORS)
        )
    for field in ("examples_zh", "examples_en"):
        examples = data.get(field)
        if not isinstance(examples, list) or not 2 <= len(examples) <= 5:
            errors.append(f"{path}: {field} must contain 2-5 examples")
    if re.search(r"\bTODO\s*[:：]", read_text(path)):
        errors.append(f"{path}: unresolved TODO placeholder")
    return data


def validate_workbuddy_package(root: Path, errors: list[str]) -> None:
    validate_connector_meta(root / "connector-meta.json", errors)
    icons = [root / f"icon{suffix}" for suffix in (".svg", ".png", ".jpg", ".jpeg")]
    if not any(path.is_file() for path in icons):
        errors.append(f"{root}: missing market icon")
    skills_root = root / "skills"
    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    if not skill_files:
        errors.append(f"{skills_root}: package must contain at least one Skill")
        return
    names: set[str] = set()
    for path in sorted(skills_root.rglob("SKILL.md")):
        result = validate_frontmatter(path, "workbuddy", errors)
        if result:
            data, _ = result
            name = compact_text(data.get("name"))
            names.add(name)
    for root_skill in skill_files:
        validate_kit(root_skill.parent, names, errors)
    validate_junk(root, errors)
    validate_private_paths(root, errors)
    validate_local_references(root, errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Skill source or package directory")
    parser.add_argument(
        "--target",
        choices=("source", "workbuddy-package"),
        default="source",
        help="Validation profile",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.path.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: directory does not exist: {root}", file=sys.stderr)
        return 2
    errors: list[str] = []
    if args.target == "source":
        validate_source(root, errors)
    else:
        validate_workbuddy_package(root, errors)
    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASSED: {args.target} validation ({root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
