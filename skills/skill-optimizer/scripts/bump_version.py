#!/usr/bin/env python3
"""
Bump a lovstudio skill's version and append a CHANGELOG entry.

Source of truth: README.md version badge. SKILL.md frontmatter metadata.version
is kept in sync when present.

Usage:
    python bump_version.py <skill-name> --type patch --message "fix frontmatter trigger phrases"
    python bump_version.py <skill-name> --type minor --message "add --verbose flag" --change "add -v shortcut"
    python bump_version.py <skill-name> --set 0.2.0 --message "..."
    python bump_version.py <skill-name> --type patch --message "..." --dry-run

Notes:
- --type: patch | minor | major (mutually exclusive with --set)
- --message: single-line summary used as the changelog bullet
- --change: may be repeated for additional bullet lines
- Creates CHANGELOG.md if missing (Keep a Changelog format).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

BADGE_COLOR = "CC785C"  # Lovstudio terracotta
BADGE_RE = re.compile(
    r"!\[Version\]\(https://img\.shields\.io/badge/version-(\d+\.\d+\.\d+)-[A-Za-z0-9]+\)"
)
FM_VERSION_RE = re.compile(r'(\n\s*version:\s*")(\d+\.\d+\.\d+)(")')


def find_repo_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / "CLAUDE.md").exists() and (p / "skills").is_dir():
            return p
    return start


def resolve_skill_dir(name: str, path: str | None) -> Path:
    if path:
        return Path(path).resolve()
    name = name.removeprefix("lovstudio-").removeprefix("lovstudio:")
    root = find_repo_root(Path.cwd())
    return (root / "skills" / f"lovstudio-{name}").resolve()


def read_current_version(skill_dir: Path) -> str:
    readme = skill_dir / "README.md"
    if readme.exists():
        m = BADGE_RE.search(readme.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        m = FM_VERSION_RE.search(skill_md.read_text(encoding="utf-8"))
        if m:
            return m.group(2)
    return "0.0.0"


def bump(version: str, kind: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown bump type: {kind}")


def badge_line(version: str) -> str:
    return f"![Version](https://img.shields.io/badge/version-{version}-{BADGE_COLOR})"


def update_readme(skill_dir: Path, new_version: str, dry: bool) -> bool:
    readme = skill_dir / "README.md"
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8")
    new_badge = badge_line(new_version)
    if BADGE_RE.search(text):
        new_text = BADGE_RE.sub(new_badge, text, count=1)
    else:
        # Insert badge right after the H1 title
        lines = text.splitlines()
        inserted = False
        out = []
        for i, line in enumerate(lines):
            out.append(line)
            if not inserted and line.startswith("# "):
                out.append("")
                out.append(new_badge)
                inserted = True
        new_text = "\n".join(out)
        if not text.endswith("\n"):
            new_text += "\n"
    if new_text != text:
        if not dry:
            readme.write_text(new_text, encoding="utf-8")
        return True
    return False


def update_skill_md_version(skill_dir: Path, new_version: str, dry: bool) -> bool:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False
    text = skill_md.read_text(encoding="utf-8")
    if not FM_VERSION_RE.search(text):
        return False
    new_text = FM_VERSION_RE.sub(rf'\g<1>{new_version}\g<3>', text, count=1)
    if new_text != text and not dry:
        skill_md.write_text(new_text, encoding="utf-8")
    return new_text != text


CHANGELOG_HEADER = """# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

"""


def update_changelog(
    skill_dir: Path,
    new_version: str,
    message: str,
    changes: list[str],
    kind: str,
    dry: bool,
) -> None:
    path = skill_dir / "CHANGELOG.md"
    today = date.today().isoformat()
    section_title = {"major": "Changed", "minor": "Added", "patch": "Fixed"}.get(kind, "Changed")

    entry_lines = [f"## [{new_version}] - {today}", "", f"### {section_title}", "", f"- {message}"]
    for c in changes:
        entry_lines.append(f"- {c}")
    entry_lines.append("")
    entry = "\n".join(entry_lines) + "\n"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing.startswith("# Changelog"):
            # insert after header paragraph
            head_end = existing.find("\n## ")
            if head_end == -1:
                # no prior entries
                body = existing.rstrip() + "\n\n" + entry
            else:
                body = existing[:head_end].rstrip() + "\n\n" + entry + existing[head_end + 1 :]
        else:
            body = CHANGELOG_HEADER + entry + existing
    else:
        body = CHANGELOG_HEADER + entry

    if not dry:
        path.write_text(body, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Bump version and update changelog for a lovstudio skill")
    ap.add_argument("name", nargs="?", help="Skill name (with or without lovstudio- prefix)")
    ap.add_argument("--path", help="Absolute path to skill directory (overrides name)")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--type", choices=["patch", "minor", "major"], help="Semver bump kind")
    group.add_argument("--set", dest="set_version", help="Set an explicit version (e.g. 0.2.0)")
    ap.add_argument("--message", "-m", required=True, help="Primary changelog entry")
    ap.add_argument("--change", "-c", action="append", default=[], help="Additional changelog bullets")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = ap.parse_args()

    if not args.name and not args.path:
        ap.error("provide a skill name or --path")

    skill_dir = resolve_skill_dir(args.name or "", args.path)
    if not skill_dir.exists():
        print(f"ERROR: skill directory not found: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    current = read_current_version(skill_dir)
    if args.set_version:
        if not re.match(r"^\d+\.\d+\.\d+$", args.set_version):
            print(f"ERROR: --set value must be semver x.y.z (got {args.set_version})", file=sys.stderr)
            sys.exit(1)
        new_version = args.set_version
        kind = "minor"  # default section label for manual sets
    else:
        new_version = bump(current, args.type)
        kind = args.type

    print(f"skill:    {skill_dir.name}")
    print(f"current:  {current}")
    print(f"new:      {new_version}")
    print(f"message:  {args.message}")
    if args.dry_run:
        print("(dry run — no files written)")

    update_readme(skill_dir, new_version, args.dry_run)
    update_skill_md_version(skill_dir, new_version, args.dry_run)
    update_changelog(skill_dir, new_version, args.message, args.change, kind, args.dry_run)

    print("done.")


if __name__ == "__main__":
    main()
