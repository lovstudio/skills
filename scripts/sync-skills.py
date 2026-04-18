#!/usr/bin/env python3
"""Mirror every free skill repo into ./skills/<name>/.

This is what lets `npx skills add lovstudio/skills` discover all free skills:
the vercel-labs/skills CLI clones this repo and scans for SKILL.md files
locally — it does NOT follow external `github` sources in marketplace.json.

Strategy: shallow clone each free repo into a tempdir, then rsync the
contents into ./skills/<name>/ with a blacklist (drops .git, binaries,
build artifacts). Idempotent: re-running only changes what upstream changed.

Env:
    SKIP_CLONE=1   # reuse existing ./skills/<name>/ without re-cloning
                   # (useful for local iteration; CI always clones fresh)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "skills.yaml"
MIRROR_ROOT = ROOT / "skills"

# Drop during rsync. Keep list short — false-positives cost more than repo bloat.
RSYNC_EXCLUDES = [
    ".git",
    ".github",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".DS_Store",
]


def load_free_skills() -> list[dict]:
    with YAML_PATH.open() as f:
        data = yaml.safe_load(f)
    return [s for s in data["skills"] if not s.get("paid")]


def clone_shallow(repo: str, dest: Path) -> None:
    subprocess.check_call(
        ["git", "clone", "--depth=1", f"https://github.com/{repo}.git", str(dest)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def rsync_mirror(src: Path, dst: Path) -> None:
    """Rsync src/ into dst/ with --delete so removed files upstream disappear here."""
    dst.mkdir(parents=True, exist_ok=True)
    cmd = ["rsync", "-a", "--delete"]
    for pat in RSYNC_EXCLUDES:
        cmd += ["--exclude", pat]
    cmd += [f"{src}/", f"{dst}/"]
    subprocess.check_call(cmd)


def prune_stale(free_names: set[str]) -> None:
    """Remove ./skills/<name>/ dirs for skills no longer in the free list.

    Happens when a skill switches to paid: true or is deleted from skills.yaml.
    Without this, stale mirrors leak into `npx skills` as uncategorized "Other".
    """
    if not MIRROR_ROOT.exists():
        return
    for child in MIRROR_ROOT.iterdir():
        if child.is_dir() and child.name not in free_names:
            print(f"  - {child.name} (stale, pruning)")
            shutil.rmtree(child)


def mirror_one(skill: dict, skip_clone: bool) -> None:
    name = skill["name"]
    repo = skill["repo"]
    dest = MIRROR_ROOT / name

    if skip_clone and dest.exists():
        print(f"  skip {name} (SKIP_CLONE=1)")
        return

    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = Path(tmp) / "clone"
        try:
            clone_shallow(repo, clone_dir)
        except subprocess.CalledProcessError:
            print(f"  ✗ {name}: clone failed (private? renamed?), skipping", file=sys.stderr)
            return
        skill_root = clone_dir / skill.get("skill_path", "")
        if not (skill_root / "SKILL.md").exists():
            print(f"  ⚠ {name}: SKILL.md not found at {skill_root.relative_to(clone_dir) or '.'}, skipping", file=sys.stderr)
            return
        rsync_mirror(skill_root, dest)
        print(f"  ✓ {name}")


def main() -> int:
    skip_clone = os.environ.get("SKIP_CLONE") == "1"
    skills = load_free_skills()
    print(f"Mirroring {len(skills)} free skills into {MIRROR_ROOT.relative_to(ROOT)}/")
    MIRROR_ROOT.mkdir(exist_ok=True)
    prune_stale({s["name"] for s in skills})
    for s in skills:
        mirror_one(s, skip_clone)
    return 0


if __name__ == "__main__":
    sys.exit(main())
