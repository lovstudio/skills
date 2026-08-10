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
import re
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


# Matches `npx skills add <owner>/<repo>` plus any trailing flag cluster on the
# SAME line (stopping at newline or inline-comment marker `#`). Group 1 = the
# command up to repo, group 2 = remaining flags on that line.
_NPX_CMD_RE = re.compile(
    r"(npx[ \t]+skills[ \t]+add[ \t]+[\w.\-]+/[\w.\-]+)((?:[ \t]+[^\s#]+)*)"
)


def _rewrite_npx_command(match: re.Match) -> str:
    """Inject `--all -g` (bulk) or `-g -y` (single-skill) when missing, so
    non-TTY callers (AI agents, CI) don't hang on the CLI's interactive prompts."""
    prefix, flags = match.group(1), match.group(2)
    existing = set(flags.split())
    has_noninteractive = bool(
        existing & {"-y", "--yes", "--all", "-a", "--agent"}
    )
    has_scope = bool(existing & {"-g", "--global", "-p", "--project"})
    targets_single_skill = bool(existing & {"-s", "--skill"})

    if has_noninteractive and has_scope:
        return match.group(0)

    extra = []
    if not has_noninteractive:
        extra.append("--all" if not targets_single_skill else "-y")
    if not has_scope:
        extra.append("-g")
    return f"{prefix}{flags} {' '.join(extra)}"


def harden_npx_commands(root: Path) -> int:
    """Rewrite `npx skills add …` occurrences under `root/` to always carry
    non-interactive flags. Returns count of files modified."""
    modified = 0
    for path in root.rglob("*.md"):
        original = path.read_text()
        patched = _NPX_CMD_RE.sub(_rewrite_npx_command, original)
        if patched != original:
            path.write_text(patched)
            modified += 1
    return modified


def rewrite_archived_catalog_refs(root: Path) -> int:
    """Point mirrored docs at the unified catalog after split indexes are archived."""
    replacements = (
        ("https://github.com/lovstudio/general-skills", "https://github.com/lovstudio/skills"),
        ("https://github.com/lovstudio/dev-skills", "https://github.com/lovstudio/skills"),
        ("lovstudio/general-skills", "lovstudio/skills"),
        ("lovstudio/dev-skills", "lovstudio/skills"),
        ("lovstudio general skills", "lovstudio skills"),
        ("lovstudio dev skills", "lovstudio skills"),
    )
    modified = 0
    for path in root.rglob("*.md"):
        if path.name == "CHANGELOG.md" or path.as_posix().endswith("references/migration.md"):
            continue
        original = path.read_text()
        patched = original
        for old, new in replacements:
            patched = patched.replace(old, new)
        if patched != original:
            path.write_text(patched)
            modified += 1
    return modified


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
        touched = harden_npx_commands(dest)
        rewritten = rewrite_archived_catalog_refs(dest)
        changes = []
        if touched:
            changes.append(f"hardened {touched} md file{'s' if touched != 1 else ''}")
        if rewritten:
            changes.append(f"updated {rewritten} archived-catalog reference{'s' if rewritten != 1 else ''}")
        suffix = f" ({'; '.join(changes)})" if changes else ""
        print(f"  ✓ {name}{suffix}")


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
