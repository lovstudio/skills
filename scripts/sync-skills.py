#!/usr/bin/env python3
"""Mirror skill repos into ./skills/<name>/ for `npx skills add` discovery.

Three classes of skill:

  1. Free skills (paid: false)
     → Shallow-clone public repo → rsync into ./skills/<name>/
     → Fully pruned and re-synced each run.

  2. Paid skills WITHOUT encrypted_bundle
     → Skipped entirely. They show up in the README index for visibility
       but can't be installed via `npx skills add`.

  3. Paid skills WITH encrypted_bundle: true
     → ./skills/<name>/ is hand-maintained (committed directly: placeholder
       SKILL.md + SKILL.md.enc + MANIFEST.enc.json + scripts/*.enc).
     → The sync script protects these dirs from prune and does NOT clone.
     → Publisher workflow: run pack-skill.py in the upstream skill repo,
       copy dist/* here, commit.

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


def load_skills() -> list[dict]:
    with YAML_PATH.open() as f:
        data = yaml.safe_load(f)
    return [s for s in data["skills"] if not s.get("test")]


def free_skills(skills: list[dict]) -> list[dict]:
    return [s for s in skills if not s.get("paid")]


def encrypted_skills(skills: list[dict]) -> list[dict]:
    return [s for s in skills if s.get("paid") and s.get("encrypted_bundle")]


def installable_skill_names(skills: list[dict]) -> set[str]:
    """Names that SHOULD have a directory under ./skills/."""
    return {s["name"] for s in free_skills(skills) + encrypted_skills(skills)}


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


def prune_stale(installable_names: set[str]) -> None:
    """Remove ./skills/<name>/ dirs for skills no longer installable.

    A skill is "installable" if it's free OR it's a paid skill with
    encrypted_bundle:true. Anything else in ./skills/ is stale.
    """
    if not MIRROR_ROOT.exists():
        return
    for child in MIRROR_ROOT.iterdir():
        if child.is_dir() and child.name not in installable_names:
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
    all_skills = load_skills()
    frees = free_skills(all_skills)
    encs  = encrypted_skills(all_skills)
    print(
        f"Syncing {len(frees)} free + {len(encs)} encrypted-paid skills "
        f"into {MIRROR_ROOT.relative_to(ROOT)}/"
    )
    MIRROR_ROOT.mkdir(exist_ok=True)
    prune_stale(installable_skill_names(all_skills))
    for s in frees:
        mirror_one(s, skip_clone)
    # Encrypted paid skills are hand-committed — just verify they're present.
    for s in encs:
        dest = MIRROR_ROOT / s["name"]
        manifest = dest / "MANIFEST.enc.json"
        if manifest.exists():
            print(f"  ✓ {s['name']} (encrypted bundle)")
        else:
            print(
                f"  ⚠ {s['name']}: encrypted_bundle:true but no MANIFEST.enc.json "
                f"at {dest.relative_to(ROOT)}/ — did you forget to commit dist/?",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
