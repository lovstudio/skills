#!/usr/bin/env python3
"""Render README.md (Simplified Chinese, primary) and README.en.md (English) from skills.yaml.

Replaces the block between <!-- SKILLS:START --> and <!-- SKILLS:END -->
and updates the count line between <!-- COUNT:START --> and <!-- COUNT:END -->
in BOTH language README files. Chinese is primary because most contributors
and users of this repo read Chinese first.

Usage:
    python3 scripts/render-readme.py              # render from skills.yaml
    GH_SYNC=1 python3 scripts/render-readme.py    # also refresh descriptions from GitHub
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "skills.yaml"
README_ZH = ROOT / "README.md"          # primary, default view on GitHub
README_EN = ROOT / "README.en.md"       # secondary, linked from the language switcher

FREE_BADGE = "![Free](https://img.shields.io/badge/Free-green)"
PAID_BADGE = "![Paid](https://img.shields.io/badge/Paid-blueviolet)"

# Display category -> (English label, Chinese label)
CATEGORY_LABELS = {
    "General": ("General", "通用"),
    "Business": ("Business", "商务"),
    "Design": ("Design", "设计"),
    "Academic": ("Academic", "学术"),
    "Office Automation": ("Office Automation", "办公"),
    "Finance": ("Finance", "财税"),
    "Content Creation": ("Content Creation", "内容创作"),
    "Dev Tools": ("Dev Tools", "开发工具"),
    "xBTI": ("xBTI", "人格测试"),
}

# Category display order (by canonical English label).
CATEGORY_ORDER_EN = [
    "General",
    "Business",
    "Design",
    "Academic",
    "Office Automation",
    "Finance",
    "Content Creation",
    "Dev Tools",
    "xBTI",
]


def load_skills() -> list[dict]:
    with YAML_PATH.open() as f:
        data = yaml.safe_load(f)
    return data["skills"]


def gh_sync(skills: list[dict]) -> None:
    """Refresh `description` (Agent-facing trigger copy) from each skill's GitHub
    repo description. Never touches tagline_en / tagline_zh — those are human-maintained."""
    for s in skills:
        repo = s["repo"]
        try:
            out = subprocess.check_output(
                ["gh", "repo", "view", repo, "--json", "description"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            desc = (json.loads(out).get("description") or "").strip()
            if desc:
                s["description"] = desc
        except subprocess.CalledProcessError:
            # Private repo, missing perms, or network issue — keep existing value.
            pass


def pick_tagline(skill: dict, lang: str) -> str:
    """Pick the human-facing tagline for the given language, falling back to the
    other language's tagline, then to `description`. README always shows something."""
    key = "tagline_zh" if lang == "zh" else "tagline_en"
    fallback_key = "tagline_en" if lang == "zh" else "tagline_zh"
    return (
        (skill.get(key) or "").strip()
        or (skill.get(fallback_key) or "").strip()
        or (skill.get("description") or "").strip()
    )


def render_table(skills: list[dict], lang: str) -> str:
    """Render skill table. lang='en' or 'zh'."""
    grouped: dict[str, list[dict]] = {}
    for s in skills:
        cat = s.get("category", "Misc")
        labels = CATEGORY_LABELS.get(cat)
        key = labels[0] if labels else cat
        grouped.setdefault(key, []).append(s)

    ordered_keys = [c for c in CATEGORY_ORDER_EN if c in grouped]
    ordered_keys += [c for c in grouped if c not in CATEGORY_ORDER_EN]

    header = {
        "en": "| | Skill | Description |",
        "zh": "| | 技能 | 描述 |",
    }[lang]
    rows = [header, "|---|---|---|"]

    for key in ordered_keys:
        labels = CATEGORY_LABELS.get(key, (key, key))
        display = labels[0] if lang == "en" else labels[1]
        rows.append(f"| **{display}** | | |")
        for s in sorted(grouped[key], key=lambda x: x["name"]):
            badge = PAID_BADGE if s.get("paid") else FREE_BADGE
            link = f"https://github.com/{s['repo']}"
            if lang == "zh" and s.get("name_zh"):
                name_cell = f"[{s['name_zh']} · `{s['name']}`]({link})"
            else:
                name_cell = f"[`{s['name']}`]({link})"
            rows.append(f"| {badge} | {name_cell} | {pick_tagline(s, lang)} |")
    return "\n".join(rows)


def render_count(skills: list[dict], lang: str) -> str:
    total = len(skills)
    paid = sum(1 for s in skills if s.get("paid"))
    free = total - paid
    if lang == "en":
        return f"> **{total} skills** — {free} Free + {paid} Paid."
    return f"> **{total} 个技能** — {free} 个免费 + {paid} 个付费。"


def replace_block(text: str, marker: str, new_body: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    replacement = f"{start}\n{new_body}\n{end}"
    if not pattern.search(text):
        raise SystemExit(f"Marker pair {start} ... {end} not found")
    return pattern.sub(replacement, text)


def render_file(path: Path, skills: list[dict], lang: str) -> None:
    text = path.read_text()
    text = replace_block(text, "COUNT", render_count(skills, lang))
    text = replace_block(text, "SKILLS", render_table(skills, lang))
    path.write_text(text)
    print(f"Rendered {path.name} ({lang}) with {len(skills)} skills.")


def main() -> int:
    skills = load_skills()
    if os.environ.get("GH_SYNC") == "1":
        gh_sync(skills)

    render_file(README_ZH, skills, "zh")
    if README_EN.exists():
        render_file(README_EN, skills, "en")
    return 0


if __name__ == "__main__":
    sys.exit(main())
