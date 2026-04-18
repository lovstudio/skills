#!/usr/bin/env python3
"""Render README.md skill list from skills.yaml.

Replaces the block between <!-- SKILLS:START --> and <!-- SKILLS:END -->
and updates the count line between <!-- COUNT:START --> and <!-- COUNT:END -->.

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
README_PATH = ROOT / "README.md"

FREE_BADGE = "![Free](https://img.shields.io/badge/Free-green)"
PAID_BADGE = "![Paid](https://img.shields.io/badge/Paid-blueviolet)"

# Display category -> (English title, Chinese title) shown as table section header.
CATEGORY_LABELS = {
    "Document Conversion": "Document Conversion / 格式转换",
    "Content Creation": "Content Processing / 内容处理",
    "Content Processing": "Content Processing / 内容处理",
    "Design": "Image & Design / 图像与设计",
    "Image & Design": "Image & Design / 图像与设计",
    "Academic": "Academic / 学术",
    "xBTI": "xBTI / 人格测试",
    "Finance": "Finance / 财务",
    "Office Automation": "Office Automation / 办公自动化",
    "Authoring": "Authoring / 创作",
    "Meta Skills": "Meta Skills / 元技能",
    "Dev Tools": "Dev Tools / 开发工具",
}

# Category display order (matches CATEGORY_LABELS keys, but via normalized labels).
CATEGORY_ORDER = [
    "Document Conversion / 格式转换",
    "Content Processing / 内容处理",
    "Image & Design / 图像与设计",
    "Academic / 学术",
    "xBTI / 人格测试",
    "Finance / 财务",
    "Office Automation / 办公自动化",
    "Authoring / 创作",
    "Meta Skills / 元技能",
    "Dev Tools / 开发工具",
]


def load_skills() -> list[dict]:
    with YAML_PATH.open() as f:
        data = yaml.safe_load(f)
    return data["skills"]


def gh_sync(skills: list[dict]) -> None:
    """Refresh `description` from each skill's GitHub repo description (best-effort)."""
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


def render_table(skills: list[dict]) -> str:
    grouped: dict[str, list[dict]] = {}
    for s in skills:
        label = CATEGORY_LABELS.get(s.get("category", ""), s.get("category", "Misc"))
        grouped.setdefault(label, []).append(s)

    ordered_labels = [c for c in CATEGORY_ORDER if c in grouped]
    ordered_labels += [c for c in grouped if c not in CATEGORY_ORDER]

    rows = ["| | Skill | Description |", "|---|---|---|"]
    for label in ordered_labels:
        rows.append(f"| **{label}** | | |")
        for s in sorted(grouped[label], key=lambda x: x["name"]):
            badge = PAID_BADGE if s.get("paid") else FREE_BADGE
            link = f"https://github.com/{s['repo']}"
            desc = s.get("description", "").strip()
            rows.append(f"| {badge} | [`{s['name']}`]({link}) | {desc} |")
    return "\n".join(rows)


def render_count(skills: list[dict]) -> str:
    total = len(skills)
    paid = sum(1 for s in skills if s.get("paid"))
    free = total - paid
    return f"> **{total} skills** — {free} Free + {paid} Paid."


def replace_block(text: str, marker: str, new_body: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    replacement = f"{start}\n{new_body}\n{end}"
    if not pattern.search(text):
        raise SystemExit(f"Marker pair {start} ... {end} not found in README.md")
    return pattern.sub(replacement, text)


def main() -> int:
    skills = load_skills()
    if os.environ.get("GH_SYNC") == "1":
        gh_sync(skills)

    readme = README_PATH.read_text()
    readme = replace_block(readme, "COUNT", render_count(skills))
    readme = replace_block(readme, "SKILLS", render_table(skills))
    README_PATH.write_text(readme)
    print(f"Rendered README.md with {len(skills)} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
