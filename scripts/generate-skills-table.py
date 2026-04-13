#!/usr/bin/env python3
"""Generate the Available Skills table in README.md from SKILL.md frontmatter.

Reads category + tagline from each skills/*/SKILL.md, groups by category,
sorts alphabetically within each group, and replaces the section between
<!-- SKILLS:BEGIN --> and <!-- SKILLS:END --> markers in README.md.
"""

from __future__ import annotations

import os
import re
import sys
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(REPO_ROOT, "skills")
README_PATH = os.path.join(REPO_ROOT, "README.md")

# Display order for categories
CATEGORY_ORDER = [
    "Meta Skills",
    "Document Conversion",
    "Content Processing",
    "Content Creation",
    "Business",
    "xBTI",
    "Dev Tools",
]

BEGIN_MARKER = "<!-- SKILLS:BEGIN -->"
END_MARKER = "<!-- SKILLS:END -->"


def parse_frontmatter(path: str) -> dict | None:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.+?)\n---", text, re.DOTALL)
    if not m:
        return None
    return yaml.safe_load(m.group(1))


def dir_display_name(dirname: str) -> str:
    """Strip lovstudio- prefix for display: lovstudio-any2pdf -> any2pdf."""
    return dirname.removeprefix("lovstudio-")


def generate_table() -> str:
    skills: dict[str, list] = {}  # category -> list of (display_name, dirname, tagline)

    for entry in sorted(os.listdir(SKILLS_DIR)):
        skill_md = os.path.join(SKILLS_DIR, entry, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        fm = parse_frontmatter(skill_md)
        if not fm:
            print(f"WARNING: no frontmatter in {skill_md}", file=sys.stderr)
            continue
        category = fm.get("category")
        tagline = fm.get("tagline")
        if not category or not tagline:
            print(f"WARNING: missing category/tagline in {skill_md}", file=sys.stderr)
            continue
        display = dir_display_name(entry)
        skills.setdefault(category, []).append((display, entry, tagline))

    # Sort each category alphabetically by display name
    for cat in skills:
        skills[cat].sort(key=lambda x: x[0].lower())

    # Stats
    total_skills = sum(len(v) for v in skills.values())
    total_categories = len(skills)

    lines = [
        f'<p align="center">',
        f'  <img src="https://img.shields.io/badge/skills-{total_skills}-CC785C?style=for-the-badge" alt="{total_skills} skills">',
        f'  <img src="https://img.shields.io/badge/categories-{total_categories}-181818?style=for-the-badge" alt="{total_categories} categories">',
        f'</p>\n',
    ]

    for cat in CATEGORY_ORDER:
        entries = skills.pop(cat, [])
        if not entries:
            continue
        lines.append(f"### {cat}\n")
        lines.append("| Skill | Description |")
        lines.append("|-------|-------------|")
        for display, dirname, tagline in entries:
            lines.append(f"| [{display}](skills/{dirname}/) | {tagline} |")
        lines.append("")

    # Any remaining categories not in CATEGORY_ORDER (sorted)
    for cat in sorted(skills.keys()):
        entries = skills[cat]
        lines.append(f"### {cat}\n")
        lines.append("| Skill | Description |")
        lines.append("|-------|-------------|")
        for display, dirname, tagline in entries:
            lines.append(f"| [{display}](skills/{dirname}/) | {tagline} |")
        lines.append("")

    return "\n".join(lines)


def main():
    table = generate_table()

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    if BEGIN_MARKER not in readme or END_MARKER not in readme:
        print(f"ERROR: markers {BEGIN_MARKER} / {END_MARKER} not found in README.md", file=sys.stderr)
        sys.exit(1)

    pattern = re.compile(
        re.escape(BEGIN_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    new_readme = pattern.sub(f"{BEGIN_MARKER}\n\n{table}\n{END_MARKER}", readme)

    if new_readme == readme:
        print("README.md is already up to date.")
        return

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)
    print("README.md updated.")


if __name__ == "__main__":
    main()
