#!/usr/bin/env python3
"""Render .claude-plugin/marketplace.json from skills.yaml (free skills only).

Plugins are grouped BY CATEGORY — not one plugin per skill. So `General`
becomes a plugin whose `skills` array lists every free General skill.
Reason: the vercel-labs/skills CLI (`npx skills add`) renders its
multiselect UI grouped by plugin name. One-skill-per-plugin produces a
redundant parent-child tree; one-plugin-per-category collapses that into
a useful tree of categories.

Tradeoff: Claude Code's native `/plugin install <name>@lovstudio` now
installs an entire category at a time (e.g. `/plugin install
dev-tools@lovstudio` pulls all Dev Tools skills). `npx skills add` is our
primary install path, so this is the right call.

Each skill's SKILL.md lives at ./skills/<skill-name>/. Plugins point at
those paths via the `skills` array and use strict:false so Claude Code
doesn't require a plugin.json inside each skill dir.

Usage:
    python3 scripts/render-marketplace.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "skills.yaml"
OUT_PATH = ROOT / ".claude-plugin" / "marketplace.json"

MARKETPLACE_NAME = "lovstudio"
OWNER = {"name": "Lovstudio", "email": "shawninjuly@gmail.com"}


def load_free_skills() -> list[dict]:
    with YAML_PATH.open() as f:
        data = yaml.safe_load(f)
    return [s for s in data["skills"] if not s.get("paid")]


def slug(text: str) -> str:
    """Kebab-case slug used as the plugin name. vercel-labs/skills title-cases
    this for display (e.g. `dev-tools` → `Dev Tools`), so keep it lowercase."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "misc"


def group_by_category(skills: list[dict]) -> "OrderedDict[str, list[dict]]":
    """Preserve yaml order: first occurrence of a category defines its position."""
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for s in skills:
        cat = s.get("category", "Misc")
        grouped.setdefault(cat, []).append(s)
    return grouped


def category_to_plugin(category: str, skills: list[dict]) -> dict:
    names = [s["name"] for s in skills]
    desc_count = len(names)
    return {
        "name": slug(category),
        "source": "./",
        "description": f"{category} — {desc_count} free skill{'s' if desc_count != 1 else ''} bundled together.",
        "category": category,
        "skills": [f"./skills/{n}" for n in names],
        "strict": False,
    }


def render() -> dict:
    skills = load_free_skills()
    grouped = group_by_category(skills)
    plugins = [category_to_plugin(cat, items) for cat, items in grouped.items()]
    return {
        "name": MARKETPLACE_NAME,
        "owner": OWNER,
        "metadata": {
            "description": "Free Lovstudio skills — one-command install via `npx skills add lovstudio/skills`.",
        },
        "plugins": plugins,
    }


def main() -> int:
    doc = render()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    total_skills = sum(len(p["skills"]) for p in doc["plugins"])
    print(
        f"Wrote {OUT_PATH.relative_to(ROOT)} with {len(doc['plugins'])} plugins "
        f"covering {total_skills} skills."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
