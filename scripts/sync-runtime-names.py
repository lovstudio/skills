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

Free entries also list every dependency their mirror's top-level `depends_on`
declares, because `npx lovstudio skills add` installs the catalog's closure, not
the SKILL.md's. A declared runtime name maps to the entry with that
`runtime_name` (or that short `name`). `--write` inserts what is missing in the
declared order and never removes the entry's other dependencies. A declared name
that free installs cannot take (no catalog entry, a paid or internal entry in its
closure, or a cycle) is left out and reported as a warning: one Skill's
declaration must not stop every other mirror from publishing.

Usage:
    python3 scripts/sync-runtime-names.py          # validate only
    python3 scripts/sync-runtime-names.py --write  # update skills.yaml in place
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_entries import is_installable, is_internal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "skills.yaml"
MIRROR_ROOT = ROOT / "skills"
ENTRY_RE = re.compile(
    r"(?ms)^- name: (?P<name>[^\n]+)\n(?P<body>.*?)(?=^- name: |\Z)"
)
RUNTIME_FIELD_RE = re.compile(r"(?m)^  runtime_name:[^\n]*(?:\n|$)")
VERSION_FIELD_RE = re.compile(r"(?m)^  version:(?P<value>[^\n]*)(?:\n|$)")
UPDATED_AT_FIELD_RE = re.compile(r"(?m)^  updated_at:[^\n]*(?:\n|$)")
# A block list (`  depends_on:` then `  - name` lines) or a one-line flow list.
DEPENDS_FIELD_RE = re.compile(r"(?m)^  depends_on:[^\n]*\n(?:  - [^\n]*\n)*")
# tagline_zh with its continuation lines: new depends_on blocks go right after it.
TAGLINE_ZH_FIELD_RE = re.compile(r"(?m)^  tagline_zh:[^\n]*\n(?:(?!  [A-Za-z_][A-Za-z0-9_]*:)[^\n]*\n)*")


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


def read_dependencies(skill_md: Path) -> list[str]:
    value = read_frontmatter(skill_md).get("depends_on")
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError("SKILL.md depends_on is not a list of Skill names")
    return [item.strip() for item in value]


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


def declared_dependencies(catalog: dict[str, dict]) -> tuple[dict[str, list[str]], list[str]]:
    """Each free mirror's declared depends_on, plus a warning per unreadable declaration."""
    declared: dict[str, list[str]] = {}
    warnings: list[str] = []
    for name, skill in catalog.items():
        skill_md = MIRROR_ROOT / name / "SKILL.md"
        # Paid and internal entries keep hand-maintained dependencies, like their versions.
        if not is_installable(skill) or not skill_md.exists():
            continue
        try:
            dependencies = read_dependencies(skill_md)
        except (OSError, ValueError, yaml.YAMLError) as error:
            warnings.append(f"{name}: {error}")
            continue
        if dependencies:
            declared[name] = dependencies
    return declared, warnings


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


def merge_dependencies(listed: list[str], declared: list[str]) -> list[str]:
    """Keep the listed order; put each new item before the next declared item already listed."""
    merged = list(listed)
    for index, dependency in enumerate(declared):
        if dependency in merged:
            continue
        anchor = next((item for item in declared[index + 1:] if item in merged), None)
        merged.insert(merged.index(anchor) if anchor else len(merged), dependency)
    return merged


def reachable(graph: dict[str, list[str]], start: str) -> list[str]:
    """`start` and everything it depends on, transitively, in depth-first order."""
    order: list[str] = []
    stack, seen = [start], set()
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        order.append(name)
        stack.extend(reversed(graph.get(name, [])))
    return order


def plan_dependencies(
    catalog: dict[str, dict], runtime_names: dict[str, str], declared: dict[str, list[str]]
) -> tuple[dict[str, list[str]], list[str]]:
    """Return the full depends_on of each entry that gains a declared dependency, and warnings.

    A warning names every declared dependency the catalog lacks and cannot take:
    one with no entry, one whose closure holds a paid or internal entry (free
    installs would then need a membership, or fail), or one that closes a cycle.
    """
    by_runtime_name = {
        str(skill["runtime_name"]).strip(): name for name, skill in catalog.items() if skill.get("runtime_name")
    }
    by_runtime_name.update({runtime_name: name for name, runtime_name in runtime_names.items()})
    graph = {name: [str(item) for item in skill.get("depends_on") or []] for name, skill in catalog.items()}
    lists: dict[str, list[str]] = {}
    warnings: list[str] = []
    for name, dependencies in declared.items():
        listed = list(graph[name])
        wanted: list[str] = []
        for dependency in dependencies:
            target = by_runtime_name.get(dependency) or (dependency if dependency in catalog else None)
            if target is None:
                warnings.append(f"{name}: SKILL.md declares {dependency}, which has no catalog entry")
                continue
            if target == name:
                warnings.append(f"{name}: SKILL.md lists itself in depends_on")
                continue
            if target in graph[name]:
                wanted.append(target)
                continue
            closure = reachable(graph, target)
            blocked = next((item for item in closure if item in catalog and not is_installable(catalog[item])), None)
            if name in closure:
                warnings.append(
                    f"{name}: SKILL.md declares {dependency}, but {target} already depends on {name}; "
                    "listing it would close a cycle"
                )
            elif blocked is not None:
                via = f"{dependency}," if blocked == target else f"{dependency}, which depends on"
                if is_internal(catalog[blocked]):
                    warnings.append(f"{name}: SKILL.md declares {via} the internal entry {blocked}; public installs cannot resolve it")
                else:
                    warnings.append(
                        f"{name}: SKILL.md declares {via} the paid entry {blocked}; "
                        f"listing it would make every install of {name} require a membership"
                    )
            else:
                wanted.append(target)
                graph[name].append(target)
        merged = merge_dependencies(listed, wanted)
        if merged != listed:
            lists[name] = merged
    return lists, warnings


def added_dependencies(catalog: dict[str, dict], lists: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        name: [item for item in dependencies if item not in (catalog[name].get("depends_on") or [])]
        for name, dependencies in lists.items()
    }


def rewrite_dependencies(text: str, lists: dict[str, list[str]]) -> str:
    """Write each entry's depends_on as a block list, in place or right after tagline_zh."""
    seen: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        name = match.group("name").strip()
        dependencies = lists.get(name)
        if dependencies is None:
            return match.group(0)
        seen.add(name)
        head = match.group(0)[: match.start("body") - match.start()]
        body = match.group("body")
        block = "  depends_on:\n" + "".join(f"  - {item}\n" for item in dependencies)
        field = DEPENDS_FIELD_RE.search(body)
        if field:
            return head + body[: field.start()] + block + body[field.end():]
        anchor = TAGLINE_ZH_FIELD_RE.search(body)
        at = anchor.end() if anchor else len(body)
        before, after = body[:at], body[at:]
        if before and not before.endswith("\n"):
            before += "\n"
        return head + before + block + after

    result = ENTRY_RE.sub(replace, text)
    missing = sorted(set(lists) - seen)
    if missing:
        raise ValueError(f"catalog entries not found in source text: {', '.join(missing)}")
    if lists:
        # The edit is textual; refuse one that would touch anything but these lists.
        expected = yaml.safe_load(text) or {}
        for skill in expected.get("skills") or []:
            if skill["name"] in lists:
                skill["depends_on"] = lists[skill["name"]]
        if yaml.safe_load(result) != expected:
            raise ValueError("depends_on rewrite would change other catalog fields")
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


def report_warnings(warnings: list[str]) -> None:
    """Warn without failing. A CI step shows only its first 10 annotations, so the summary lists all."""
    if not warnings:
        return
    headline = f"{len(warnings)} declared {'dependency needs' if len(warnings) == 1 else 'dependencies need'} a fix by hand"
    print(f"{headline}:", file=sys.stderr)
    for warning in warnings:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            message = warning.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::warning title=Declared dependency not listed::{message}", flush=True)
        else:
            print(f"  ! {warning}", file=sys.stderr)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"### {headline}\n\n")
            handle.writelines(f"- {warning}\n" for warning in warnings)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="update skills.yaml before validating")
    args = parser.parse_args()

    text, catalog = load_catalog()
    runtime_names, errors = expected_runtime_names(catalog)
    versions, version_errors = expected_versions(catalog)
    declared, declaration_warnings = declared_dependencies(catalog)
    errors += version_errors
    if errors:
        print("SKILL.md frontmatter discovery failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.write:
        drift = validate_versions(catalog, versions)
        dependency_lists, _ = plan_dependencies(catalog, runtime_names, declared)
        added = added_dependencies(catalog, dependency_lists)
        next_text = rewrite_dependencies(rewrite_versions(rewrite(text, runtime_names), versions), dependency_lists)
        if next_text != text:
            YAML_PATH.write_text(next_text, encoding="utf-8")
            print(f"Updated skills.yaml from {len(runtime_names)} mirrored SKILL.md files.")
            for change in drift:
                print(f"  - {change}")
            for name, items in added.items():
                print(f"  - {name}.depends_on: added {', '.join(items)}")
        text, catalog = load_catalog()

    dependency_lists, dependency_warnings = plan_dependencies(catalog, runtime_names, declared)
    report_warnings(declaration_warnings + dependency_warnings)
    errors = (
        validate(catalog, runtime_names)
        + validate_versions(catalog, versions)
        + duplicate_runtime_fields(text)
        + [
            f"{name}.depends_on: lacks {', '.join(items)}, which its mirrored SKILL.md declares"
            for name, items in added_dependencies(catalog, dependency_lists).items()
        ]
    )
    if errors:
        print("Runtime name, version and dependency validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Runtime name, version and dependency validation passed for {len(runtime_names)} installable Skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
