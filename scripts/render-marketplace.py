#!/usr/bin/env python3
"""Render .claude-plugin/marketplace.json from skills.yaml (free skills only).

Each plugin entry points at a LOCAL path (./skills/<name>/) mirrored by
scripts/sync-skills.py. We use local paths (not external github sources)
because vercel-labs/skills (`npx skills add`) explicitly skips remote
sources in marketplace.json — it only resolves relative paths.

Each skill repo ships a root-level SKILL.md with no plugin.json, so we use
strict:false + skills:["./"] so Claude Code treats the mirrored root as the
skill directory and reads the skill name from SKILL.md frontmatter.

This enables both:
    npx skills add lovstudio/skills             # vercel-labs CLI, scans SKILL.md
    /plugin marketplace add lovstudio/skills    # native Claude Code marketplace

Usage:
    python3 scripts/render-marketplace.py
"""
from __future__ import annotations

import json
import sys
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


def to_plugin_entry(skill: dict) -> dict:
    name = skill["name"]
    entry: dict = {
        "name": name,
        "source": f"./skills/{name}",
        "description": skill.get("description", "").strip(),
        "category": skill.get("category", ""),
        "skills": ["./"],
        "strict": False,
    }
    if "version" in skill:
        entry["version"] = skill["version"]
    return entry


def render() -> dict:
    skills = load_free_skills()
    return {
        "name": MARKETPLACE_NAME,
        "owner": OWNER,
        "metadata": {
            "description": "Free Lovstudio skills — one-command install via `npx skills add lovstudio/skills`.",
        },
        "plugins": [to_plugin_entry(s) for s in skills],
    }


def main() -> int:
    doc = render()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT_PATH.relative_to(ROOT)} with {len(doc['plugins'])} plugins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
