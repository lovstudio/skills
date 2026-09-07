#!/usr/bin/env python3
"""Inventory legacy slash commands or prepare an isolated migration work area."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import yaml
import init_skill


def inspect(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    frontmatter = {}
    if text.startswith("---\n"):
        parts = text.split("\n---", 1)
        if len(parts) != 2:
            raise ValueError("unclosed frontmatter")
        frontmatter = yaml.safe_load(parts[0][4:]) or {}
        if not isinstance(frontmatter, dict):
            raise ValueError("frontmatter must be a mapping")
    findings = []
    for key in ("disable-model-invocation", "user-invocable", "argument-hint", "model", "context", "agent", "hooks", "aliases"):
        if key in frontmatter:
            findings.append("host-field:" + key)
    for label, pattern in (
        ("argument-interpolation", r"\$(?:ARGUMENTS|[1-9])\b"),
        ("implicit-file-reference", r"(?<!\w)@[\w./-]+"),
        ("shell-interpolation", r"!`|!\$\("),
        ("host-tool", r"AskUserQuestion|TodoWrite|Read\(\*\)|Bash\("),
        ("legacy-invocation", r"/(?:lovstudio|skill-publisher)/"),
        ("host-path", r"~/\.(?:claude|codex)/"),
        ("placeholder-domain", r"https?://example\.com"),
    ):
        if re.search(pattern, text):
            findings.append(label)
    return {
        "file": str(path),
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "name": frontmatter.get("name") or path.stem,
        "description": frontmatter.get("description", ""),
        "findings": findings,
        "state": "needs-review",
    }


def inventory(roots: list[Path], sources: list[Path]) -> dict:
    entries, seen = [], {}
    for root in roots + sources:
        if not root.is_dir():
            raise ValueError("inventory root does not exist: " + str(root))
        paths = root.rglob("*.md") if root in roots else root.glob("*/SKILL.md")
        for path in sorted(paths):
            if any(part.startswith(".") or part in ("node_modules", "output") for part in path.relative_to(root).parts):
                continue
            try:
                entry = inspect(path)
                resolved = str(path.resolve(strict=True))
                if resolved in seen:
                    seen[resolved].setdefault("aliases", []).append(str(path))
                    continue
                if root in sources and not entry["findings"]:
                    continue
                seen[resolved] = entry
                entries.append(entry)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                entries.append({"file": str(path), "state": "blocked", "error": type(exc).__name__})
    return {"schema": "slash-command-inventory/v1", "count": len(entries), "entries": entries}


def prepare(source: Path, destination: Path, name: str, content_class: str) -> dict:
    name = init_skill.normalize_name(name)
    original = source.read_bytes()
    entry = inspect(source)
    # mkdir without exist_ok also rejects symlinks and interrupted previous runs.
    destination.mkdir(parents=True)
    (destination / "original.md").write_bytes(original)
    target = destination / (name + "-skill")
    target.mkdir()
    init_skill.write_skill(target / "SKILL.md", name, "", content_class=content_class,
                           branding_consistency=content_class in ("microcopy", "authored-prose"))
    init_skill.write_manifest(target, name)
    init_skill.write_profile_reference(target)
    init_skill.write_composition_reference(target)
    init_skill.write_card_bundle(target, name)
    init_skill.copy_runtime_scripts(target, Path(__file__).resolve().parent)
    if content_class == "authored-prose":
        init_skill.write_authorship_reference(target)
    (target / "README.md").write_text(init_skill.README_MD.format(
        name=name, configuration_section=init_skill.README_CONFIGURATION), encoding="utf-8")
    (target / "LICENSE").write_text(init_skill.LICENSE_MD, encoding="utf-8")
    (target / "CHANGELOG.md").write_text(init_skill.CHANGELOG_MD, encoding="utf-8")
    report = {"schema": "slash-command-migration/v1", "source": entry,
              "candidate": str(target), "state": "needs-semantic-upgrade",
              "installed": False, "published": False,
              "required_review": ["preserve behavior and safeguards", "port host syntax and resources",
                                  "resolve overlap", "verify real case", "validate and install"]}
    (destination / "migration.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("inventory")
    scan.add_argument("--command-root", type=Path, action="append", default=[])
    scan.add_argument("--source-root", type=Path, action="append", default=[])
    stage = commands.add_parser("prepare")
    stage.add_argument("source", type=Path)
    stage.add_argument("--output", type=Path, required=True, help="New work area outside canonical source")
    stage.add_argument("--name", required=True)
    stage.add_argument("--content-class", required=True, choices=init_skill.CONTENT_CLASSES)
    args = parser.parse_args()
    try:
        if args.command == "inventory":
            if not args.command_root and not args.source_root:
                raise ValueError("provide at least one inventory root")
            result = inventory(args.command_root, args.source_root)
        else:
            result = prepare(args.source, args.output, args.name, args.content_class)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
