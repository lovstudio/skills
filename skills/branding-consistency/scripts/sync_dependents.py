#!/usr/bin/env python3
"""Declare and verify the branding consistency dependency across canonical Skills."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml


DEPENDENCY = "lov-branding-consistency"
IGNORED_PARTS = {
    ".backups",
    ".git",
    ".worktrees",
    "node_modules",
    "output",
    "dist",
    "build",
}


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], list[str], int]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("unterminated YAML frontmatter")
    data = yaml.safe_load("".join(lines[1:end])) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data, lines, end


def manifest_names(path: Path) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    names: list[str] = []
    for values in (data.get("categories") or {}).values():
        names.extend(values or [])
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate manifest names: {duplicates}")
    if DEPENDENCY in names:
        raise ValueError("the dependency cannot depend on itself")
    return names


def discover(roots: list[Path], wanted: set[str]) -> dict[str, list[Path]]:
    found = {name: [] for name in wanted}
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("SKILL.md"):
            if any(part in IGNORED_PARTS for part in path.relative_to(root).parts):
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                data, _, _ = parse_frontmatter(path)
            except (OSError, ValueError, yaml.YAMLError):
                continue
            name = data.get("name")
            if name in wanted:
                found[name].append(path)
    return found


def dependency_values(data: dict[str, Any]) -> list[str]:
    value = data.get("depends_on", [])
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ValueError("depends_on must be a string or list")


def add_dependency(path: Path) -> bool:
    data, lines, end = parse_frontmatter(path)
    if DEPENDENCY in dependency_values(data):
        return False

    start = next((i for i in range(1, end) if re.match(r"^depends_on\s*:", lines[i])), None)
    if start is None:
        insertion = next((i for i in range(1, end) if re.match(r"^metadata\s*:", lines[i])), end)
        lines[insertion:insertion] = [f"depends_on:\n", f"  - {DEPENDENCY}\n"]
    else:
        inline = lines[start].split(":", 1)[1].strip()
        if inline:
            current = yaml.safe_load(inline)
            values = [current] if isinstance(current, str) else list(current or [])
            replacement = ["depends_on:\n"] + [f"  - {item}\n" for item in values + [DEPENDENCY]]
            lines[start : start + 1] = replacement
        else:
            stop = start + 1
            while stop < end and (lines[stop].startswith((" ", "\t")) or not lines[stop].strip()):
                stop += 1
            lines[stop:stop] = [f"  - {DEPENDENCY}\n"]

    content = "".join(lines)
    original_mode = path.stat().st_mode & 0o777
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.chmod(temp_name, original_mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--search-root", action="append", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Validate only discovered entries, for partial installation roots",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    names = manifest_names(args.manifest)
    found = discover(args.search_root, set(names))
    missing = sorted(name for name, paths in found.items() if not paths)
    changed: list[str] = []
    invalid: list[dict[str, str]] = []

    for name in names:
        for path in found[name]:
            try:
                data, _, _ = parse_frontmatter(path)
                if DEPENDENCY not in dependency_values(data):
                    if args.apply:
                        add_dependency(path)
                    changed.append(str(path))
            except (OSError, ValueError, yaml.YAMLError) as exc:
                invalid.append({"path": str(path), "error": str(exc)})

    result = {
        "dependency": DEPENDENCY,
        "declared_skill_names": len(names),
        "discovered_skill_files": sum(len(paths) for paths in found.values()),
        "missing_skill_names": missing,
        "missing_allowed": args.allow_missing,
        "invalid": invalid,
        "mode": "apply" if args.apply else "check",
        "changed_or_missing_dependency": changed,
        "ok": (args.allow_missing or not missing)
        and not invalid
        and (args.apply or not changed),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
