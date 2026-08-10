#!/usr/bin/env python3
"""Render .claude-plugin/marketplace.json from skills.yaml.

Plugins are grouped BY CATEGORY — not one plugin per skill. So `General`
becomes a plugin whose `skills` array lists every free General skill.
Reason: the vercel-labs/skills CLI (`npx skills add`) renders its
multiselect UI grouped by plugin name. One-skill-per-plugin produces a
redundant parent-child tree; one-plugin-per-category collapses that into
a useful tree of categories.

Tradeoff: Claude Code's native `/plugin install <name>@lovstudio` now
installs an entire category at a time. `npx lovstudio skills add` is our
primary install path; paid entries are included only after they have an
encrypted bundle and still require account entitlement at runtime.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_deps import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "skills.yaml"
OUT_PATH = ROOT / ".claude-plugin" / "marketplace.json"

MARKETPLACE_NAME = "lovstudio"
OWNER = {"name": "Lovstudio", "email": "shawninjuly@gmail.com"}


def load_installable_skills() -> tuple[list[dict], list[dict]]:
    """Return (installable, all). Installable = free + encrypted-paid.
    All is needed to resolve depends_on targets that may themselves be either class."""
    with YAML_PATH.open() as f:
        data = yaml.safe_load(f)
    all_skills = [s for s in data["skills"] if not s.get("test")]
    errors = validate(data["skills"])
    if errors:
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        raise SystemExit("skills.yaml dependency validation failed")
    installable = [
        s for s in all_skills
        if not s.get("paid") or s.get("encrypted_bundle")
    ]
    return installable, all_skills


def closure(names: list[str], by_name: dict[str, dict]) -> list[str]:
    """Expand depends_on transitively; preserve first-seen order, de-dup."""
    seen: OrderedDict[str, None] = OrderedDict()
    def walk(n: str) -> None:
        if n in seen or n not in by_name:
            return
        seen[n] = None
        for dep in by_name[n].get("depends_on") or []:
            walk(dep)
    for n in names:
        walk(n)
    return list(seen.keys())


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


def category_to_plugin(
    category: str, skills: list[dict], by_name: dict[str, dict]
) -> dict:
    names = closure([s["name"] for s in skills], by_name)
    n_free = sum(1 for s in skills if not s.get("paid"))
    n_paid = sum(1 for s in skills if s.get("paid"))
    if n_paid:
        desc = f"{category} — {n_free} free + {n_paid} paid (Credits redemption required)."
    else:
        desc = f"{category} — {n_free} free skill{'s' if n_free != 1 else ''} bundled together."
    return {
        "name": slug(category),
        "source": "./",
        "description": desc,
        "category": category,
        "skills": [f"./skills/{n}" for n in names],
        "strict": False,
    }


def render() -> dict:
    skills, all_skills = load_installable_skills()
    by_name = {s["name"]: s for s in all_skills}
    grouped = group_by_category(skills)
    plugins = [category_to_plugin(cat, items, by_name) for cat, items in grouped.items()]
    return {
        "name": MARKETPLACE_NAME,
        "owner": OWNER,
        "metadata": {
            "description": "Lovstudio skills — install via `npx lovstudio skills add <name>`; `... add skills` installs the free catalog and paid entries are redeemed individually.",
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
