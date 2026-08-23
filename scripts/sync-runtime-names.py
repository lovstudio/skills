#!/usr/bin/env python3
"""Keep catalog slugs and installable Skill runtime names explicitly aligned.

`skills.yaml` uses short product/catalog slugs such as `write-professional-book`,
while Agent runtimes select the `name` declared by each mirrored SKILL.md, such
as `lov-write-professional-book`. These values are not always derivable from a
prefix convention, so the catalog records both.

Usage:
    python3 scripts/sync-runtime-names.py          # validate only
    python3 scripts/sync-runtime-names.py --write  # update skills.yaml in place
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "skills.yaml"
MIRROR_ROOT = ROOT / "skills"
ENTRY_RE = re.compile(
    r"(?m)^- name: (?P<name>[^\n]+)\n(?:  runtime_name: (?P<runtime>[^\n]+)\n)?"
)


def read_runtime_name(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("SKILL.md has no YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("SKILL.md frontmatter is not closed")
    frontmatter = yaml.safe_load(parts[1]) or {}
    runtime_name = str(frontmatter.get("name") or "").strip()
    if not runtime_name:
        raise ValueError("SKILL.md frontmatter has no name")
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", runtime_name):
        raise ValueError(f"unsafe runtime name {runtime_name!r}")
    return runtime_name


def load_catalog() -> tuple[str, dict[str, dict]]:
    text = YAML_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    return text, {str(skill["name"]): skill for skill in data.get("skills") or []}


def expected_runtime_names(catalog: dict[str, dict]) -> tuple[dict[str, str], list[str]]:
    runtime_names: dict[str, str] = {}
    errors: list[str] = []
    for name, skill in catalog.items():
        skill_md = MIRROR_ROOT / name / "SKILL.md"
        installable = not skill.get("paid") or bool(skill.get("encrypted_bundle"))
        if not skill_md.exists():
            if installable and not skill.get("test"):
                errors.append(f"{name}: installable catalog entry has no mirrored SKILL.md")
            continue
        try:
            runtime_names[name] = read_runtime_name(skill_md)
        except (OSError, ValueError, yaml.YAMLError) as error:
            errors.append(f"{name}: {error}")
    return runtime_names, errors


def rewrite(text: str, runtime_names: dict[str, str]) -> str:
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        name = match.group("name").strip()
        runtime_name = runtime_names.get(name)
        if runtime_name is None:
            return match.group(0)
        seen.add(name)
        return f"- name: {name}\n  runtime_name: {runtime_name}\n"

    result = ENTRY_RE.sub(replace, text)
    missing = sorted(set(runtime_names) - seen)
    if missing:
        raise ValueError(f"catalog entries not found in source text: {', '.join(missing)}")
    return result


def validate(catalog: dict[str, dict], runtime_names: dict[str, str]) -> list[str]:
    errors: list[str] = []
    seen_runtime_names: dict[str, str] = {}
    for name, expected in runtime_names.items():
        declared = str(catalog[name].get("runtime_name") or "").strip()
        if declared != expected:
            errors.append(f"{name}.runtime_name: declared {declared!r}, mirrored SKILL.md uses {expected!r}")
        previous = seen_runtime_names.get(expected)
        if previous is not None:
            errors.append(f"duplicate runtime_name {expected!r}: {previous}, {name}")
        else:
            seen_runtime_names[expected] = name
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="update skills.yaml before validating")
    args = parser.parse_args()

    text, catalog = load_catalog()
    runtime_names, errors = expected_runtime_names(catalog)
    if errors:
        print("Runtime name discovery failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.write:
        next_text = rewrite(text, runtime_names)
        if next_text != text:
            YAML_PATH.write_text(next_text, encoding="utf-8")
            print(f"Updated runtime_name for {len(runtime_names)} catalog entries.")
        _, catalog = load_catalog()

    errors = validate(catalog, runtime_names)
    if errors:
        print("Runtime name validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Runtime name validation passed for {len(runtime_names)} installable Skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
