#!/usr/bin/env python3
"""Validate a portable local Skill Publisher Skill source directory."""

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
        "ERROR: PyYAML is required. Install it with: python3 -m pip install PyYAML",
        file=sys.stderr,
    )
    raise SystemExit(2)


FRONTMATTER_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt", ".svg", ".py"}
JUNK_NAMES = {"__pycache__", ".DS_Store"}
JUNK_SUFFIXES = {".pyc", ".pyo"}
SKIP_DIRS = {".git", "dist", ".venv", "venv", "node_modules"}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
SKILL_PATH_RE = re.compile(r"\$(SKILL_DIR|KIT_DIR)/([A-Za-z0-9_./-]+)")
CARD_STANDARD = "lovstudio/skill-card/v1"
PRICING_CARD_SCHEMA = "lovstudio/pricing-card/v1"


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


def has_content(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(has_content(item) for item in value)
    if isinstance(value, dict):
        return any(has_content(item) for item in value.values())
    return value is not None


def contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(re.search(r"\bTODO\b|\{[^}]+\}", value, re.I))
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())
    return False


def validate_card_bundle(skill_root: Path, errors: list[str]) -> None:
    card_path = skill_root / "skill-card.yaml"
    card_doc_path = skill_root / "skill-card.md"
    cases_path = skill_root / "cases" / "cases.json"
    pricing_path = skill_root / "pricing-card.yaml"
    for path in (card_path, card_doc_path, cases_path, pricing_path):
        if not path.is_file():
            errors.append(f"{path}: required Skill trust-bundle file is missing")

    card = load_yaml(card_path, errors) if card_path.is_file() else None
    if card is not None:
        if card.get("schema") != CARD_STANDARD:
            errors.append(f"{card_path}: schema must be {CARD_STANDARD}")
        required = (
            "description", "owner", "license", "use_case", "deployment",
            "requirements", "risks", "references", "output", "version",
            "ethical_considerations", "dimensions", "pricing", "distribution",
        )
        for key in required:
            if key not in card or not has_content(card.get(key)):
                errors.append(f"{card_path}: required field '{key}' is missing or empty")
        dimensions = card.get("dimensions")
        if not isinstance(dimensions, list) or len(dimensions) < 3:
            errors.append(f"{card_path}: dimensions need at least three entries")
        else:
            ids: set[str] = set()
            for index, dimension in enumerate(dimensions):
                label = f"{card_path}: dimensions[{index}]"
                if not isinstance(dimension, dict):
                    errors.append(f"{label}: expected a mapping")
                    continue
                dimension_id = compact_text(dimension.get("id"))
                if not dimension_id or dimension_id in ids:
                    errors.append(f"{label}: id is required and unique")
                ids.add(dimension_id)
                for key in ("label", "description", "evidence"):
                    if not compact_text(dimension.get(key)):
                        errors.append(f"{label}: '{key}' is required")
        risks = card.get("risks")
        if not isinstance(risks, list) or not risks:
            errors.append(f"{card_path}: risks need risk and mitigation entries")
        else:
            for index, risk in enumerate(risks):
                if not isinstance(risk, dict) or not compact_text(risk.get("risk")) or not compact_text(risk.get("mitigation")):
                    errors.append(f"{card_path}: risks[{index}] needs risk and mitigation")
        distribution = card.get("distribution")
        if not isinstance(distribution, dict) or not isinstance(distribution.get("paid"), list) or not isinstance(distribution.get("free"), list):
            errors.append(f"{card_path}: distribution needs paid and free lists")
        if contains_placeholder(card):
            errors.append(f"{card_path}: unresolved placeholder")

    if card_doc_path.is_file():
        card_doc = read_text(card_doc_path)
        headings = (
            "Description", "Owner", "License", "Use Case", "Deployment Geography",
            "Requirements", "Known Risks", "References", "Skill Output",
            "Skill Version", "Ethical Considerations", "User Cases",
            "Dimension Map", "Pricing Basis", "Distribution",
        )
        for heading in headings:
            if not re.search(rf"(?mi)^#+\s+{re.escape(heading)}", card_doc):
                errors.append(f"{card_doc_path}: missing '{heading}' section")
        if re.search(r"\bTODO\b|\{[^}]+\}", card_doc, re.I):
            errors.append(f"{card_doc_path}: unresolved placeholder")

    if cases_path.is_file():
        try:
            cases = json.loads(read_text(cases_path))
        except json.JSONDecodeError as exc:
            errors.append(f"{cases_path}: invalid JSON: {exc}")
            cases = []
        if not isinstance(cases, list) or not cases:
            errors.append(f"{cases_path}: at least one user case is required")
        else:
            for index, case in enumerate(cases):
                label = f"{cases_path}: cases[{index}]"
                if not isinstance(case, dict):
                    errors.append(f"{label}: expected a mapping")
                    continue
                for key in ("title", "description", "input", "prompt", "output"):
                    if not has_content(case.get(key)):
                        errors.append(f"{label}: '{key}' is required")
                if contains_placeholder(case):
                    errors.append(f"{label}: unresolved placeholder")

    pricing = load_yaml(pricing_path, errors) if pricing_path.is_file() else None
    if pricing is not None:
        if pricing.get("schema") != PRICING_CARD_SCHEMA:
            errors.append(f"{pricing_path}: schema must be {PRICING_CARD_SCHEMA}")
        for key in ("model", "currency", "list_price_cny", "basis", "boundary", "review_trigger", "confidence"):
            if key not in pricing or (key != "list_price_cny" and not has_content(pricing.get(key))):
                errors.append(f"{pricing_path}: required field '{key}' is missing or empty")
        if contains_placeholder(pricing):
            errors.append(f"{pricing_path}: unresolved placeholder")


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
    for path, data in parsed:
        metadata = data.get("metadata")
        if isinstance(metadata, dict) and metadata.get("card_standard") == CARD_STANDARD:
            validate_card_bundle(path.parent, errors)
    validate_kit(root, names, errors)

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
