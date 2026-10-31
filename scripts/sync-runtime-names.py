#!/usr/bin/env python3
"""Keep catalog entries aligned with their mirrored SKILL.md frontmatter.

`skills.yaml` uses short product/catalog slugs such as `write-professional-book`,
while Agent runtimes select the `name` declared by each mirrored SKILL.md, such
as `lov-write-professional-book`. These values are not always derivable from a
prefix convention, so the catalog records both.

Free entries also take `version` from the mirror's `metadata.version`. When it
changes, `updated_at` is stamped with the sync time, because lovstudio.ai dates
Skill updates by that field. Paid and internal entries are not mirrored and keep
a hand-maintained `version`.

Usage:
    python3 scripts/sync-runtime-names.py          # validate only
    python3 scripts/sync-runtime-names.py --write  # update skills.yaml in place
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_entries import is_installable  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "skills.yaml"
MIRROR_ROOT = ROOT / "skills"
ENTRY_RE = re.compile(
    r"(?ms)^- name: (?P<name>[^\n]+)\n(?P<body>.*?)(?=^- name: |\Z)"
)
RUNTIME_FIELD_RE = re.compile(r"(?m)^  runtime_name:[^\n]*(?:\n|$)")
VERSION_FIELD_RE = re.compile(r"(?m)^  version:(?P<value>[^\n]*)(?:\n|$)")
UPDATED_AT_FIELD_RE = re.compile(r"(?m)^  updated_at:[^\n]*(?:\n|$)")


def read_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("SKILL.md has no YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("SKILL.md frontmatter is not closed")
    return yaml.safe_load(parts[1]) or {}


def read_runtime_name(skill_md: Path) -> str:
    runtime_name = str(read_frontmatter(skill_md).get("name") or "").strip()
    if not runtime_name:
        raise ValueError("SKILL.md frontmatter has no name")
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", runtime_name):
        raise ValueError(f"unsafe runtime name {runtime_name!r}")
    return runtime_name


def read_version(skill_md: Path) -> str | None:
    frontmatter = read_frontmatter(skill_md)
    metadata = frontmatter.get("metadata")
    value = metadata.get("version") if isinstance(metadata, dict) else None
    if value is None:
        value = frontmatter.get("version")
    version = str(value or "").strip()
    if not version:
        return None
    if not re.fullmatch(r"[A-Za-z0-9._+-]+", version):
        raise ValueError(f"unsafe version {version!r}")
    return version


def load_catalog() -> tuple[str, dict[str, dict]]:
    text = YAML_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    return text, {str(skill["name"]): skill for skill in data.get("skills") or []}


def expected_runtime_names(catalog: dict[str, dict]) -> tuple[dict[str, str], list[str]]:
    runtime_names: dict[str, str] = {}
    errors: list[str] = []
    for name, skill in catalog.items():
        skill_md = MIRROR_ROOT / name / "SKILL.md"
        installable = is_installable(skill)
        if not skill_md.exists():
            if installable and not skill.get("test"):
                errors.append(f"{name}: installable catalog entry has no mirrored SKILL.md")
            continue
        try:
            runtime_names[name] = read_runtime_name(skill_md)
        except (OSError, ValueError, yaml.YAMLError) as error:
            errors.append(f"{name}: {error}")
    return runtime_names, errors


def expected_versions(catalog: dict[str, dict]) -> tuple[dict[str, str], list[str]]:
    versions: dict[str, str] = {}
    errors: list[str] = []
    for name, skill in catalog.items():
        skill_md = MIRROR_ROOT / name / "SKILL.md"
        # A paid version selects the private repo's download tag; never take it from a stray mirror.
        if not is_installable(skill) or not skill_md.exists():
            continue
        try:
            version = read_version(skill_md)
        except (OSError, ValueError, yaml.YAMLError) as error:
            errors.append(f"{name}: {error}")
            continue
        if version is not None:
            versions[name] = version
    return versions, errors


def rewrite(text: str, runtime_names: dict[str, str]) -> str:
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        name = match.group("name").strip()
        runtime_name = runtime_names.get(name)
        if runtime_name is None:
            return match.group(0)
        seen.add(name)
        body = match.group('body')
        replaced = False

        def replace_field(field: re.Match[str]) -> str:
            nonlocal replaced
            if replaced:
                return ''
            replaced = True
            return f'  runtime_name: {runtime_name}\n'

        body = RUNTIME_FIELD_RE.sub(replace_field, body)
        if not replaced:
            body = f'  runtime_name: {runtime_name}\n' + body
        return f'- name: {name}\n{body}'

    result = ENTRY_RE.sub(replace, text)
    missing = sorted(set(runtime_names) - seen)
    if missing:
        raise ValueError(f"catalog entries not found in source text: {', '.join(missing)}")
    return result


def sync_version(body: str, version: str, updated_at: str) -> str:
    field = VERSION_FIELD_RE.search(body)
    raw = field.group("value").strip() if field else ""
    if field and str(yaml.safe_load(raw)) == version:
        return body
    quote = raw[0] if raw[:1] in ("'", '"') else ""
    # Plain `1.10` would load as the float 1.1.
    if not quote and yaml.safe_load(version) != version:
        quote = "'"
    version_line = f"  version: {quote}{version}{quote}\n"
    updated_line = f"  updated_at: {updated_at}\n"
    if UPDATED_AT_FIELD_RE.search(body):
        body = UPDATED_AT_FIELD_RE.sub(lambda _: updated_line, body, count=1)
        updated_line = ""
    if field:
        return VERSION_FIELD_RE.sub(lambda _: version_line + updated_line, body, count=1)
    return version_line + updated_line + body


def rewrite_versions(text: str, versions: dict[str, str], synced_at: datetime | None = None) -> str:
    moment = (synced_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    updated_at = moment.strftime("%Y-%m-%d %H:%M:%S+00:00")
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        name = match.group("name").strip()
        version = versions.get(name)
        if version is None:
            return match.group(0)
        seen.add(name)
        head = match.group(0)[: match.start("body") - match.start()]
        return head + sync_version(match.group("body"), version, updated_at)

    result = ENTRY_RE.sub(replace, text)
    missing = sorted(set(versions) - seen)
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


def validate_versions(catalog: dict[str, dict], versions: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for name, expected in versions.items():
        declared = catalog[name].get("version")
        declared = "" if declared is None else str(declared).strip()
        if declared != expected:
            errors.append(f"{name}.version: declared {declared!r}, mirrored SKILL.md uses {expected!r}")
    return errors


def duplicate_runtime_fields(text: str) -> list[str]:
    return [
        f"{match.group('name').strip()}: repeated runtime_name field"
        for match in ENTRY_RE.finditer(text)
        if len(RUNTIME_FIELD_RE.findall(match.group('body'))) > 1
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="update skills.yaml before validating")
    args = parser.parse_args()

    text, catalog = load_catalog()
    runtime_names, errors = expected_runtime_names(catalog)
    versions, version_errors = expected_versions(catalog)
    errors += version_errors
    if errors:
        print("SKILL.md frontmatter discovery failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.write:
        drift = validate_versions(catalog, versions)
        next_text = rewrite_versions(rewrite(text, runtime_names), versions)
        if next_text != text:
            YAML_PATH.write_text(next_text, encoding="utf-8")
            print(f"Updated skills.yaml from {len(runtime_names)} mirrored SKILL.md files.")
            for change in drift:
                print(f"  - {change}")
        text, catalog = load_catalog()

    errors = (
        validate(catalog, runtime_names)
        + validate_versions(catalog, versions)
        + duplicate_runtime_fields(text)
    )
    if errors:
        print("Runtime name and version validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Runtime name and version validation passed for {len(runtime_names)} installable Skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
