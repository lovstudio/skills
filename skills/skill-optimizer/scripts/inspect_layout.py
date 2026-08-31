#!/usr/bin/env python3
"""Inspect a Skill's source, installed copies, and nearby catalog checkouts.

This command is read-only. It reports what was discovered and never treats a
missing catalog or a drifted installation as synchronized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


IGNORED_DIRS = {".git", ".worktrees", "node_modules", "dist", "build", "target", ".venv", "__pycache__"}
INSTALL_ENV_VARS = ("AGENT_SKILLS_DIR", "CLAUDE_SKILLS_DIR", "CODEX_SKILLS_DIR", "SKILLS_DIR")


def run_git(directory: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def skill_short_name(skill_dir: Path) -> str:
    name = skill_dir.name
    if name.endswith("-skill"):
        name = name[: -len("-skill")]
    return name.removeprefix("lov-")


def tree_digest(directory: Path) -> str | None:
    if not directory.is_dir():
        return None
    digest = hashlib.sha256()
    files = []
    for path in directory.rglob("*"):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.relative_to(directory).parts):
            continue
        files.append(path)
    for path in sorted(files):
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        try:
            digest.update(path.read_bytes())
        except OSError:
            return None
        digest.update(b"\0")
    return digest.hexdigest()


def distribution_payload(source: Path) -> Path:
    """Use the publishable payload for paid/encrypted source repositories."""
    public = source / "public"
    if (source / "src" / "SKILL.md").exists() and (public / "SKILL.md").exists():
        return public
    return source


def split_paths(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        for item in value.split(os.pathsep):
            if item.strip():
                paths.append(Path(item).expanduser().resolve())
    return paths


def installation_candidates(source: Path, explicit_roots: list[str]) -> list[Path]:
    roots = split_paths(explicit_roots)
    for variable in INSTALL_ENV_VARS:
        value = os.environ.get(variable)
        if value:
            roots.extend(split_paths([value]))
    roots.extend(
        path
        for path in (Path.home() / ".agents" / "skills", Path.home() / ".codex" / "skills")
        if path.is_dir()
    )
    names = [f"lov-{skill_short_name(source)}", source.name, skill_short_name(source)]
    result: list[Path] = []
    for root in dict.fromkeys(roots):
        for name in names:
            candidate = root / name
            if candidate.is_dir() and candidate != source:
                result.append(candidate)
    return list(dict.fromkeys(result))


def catalog_candidates(source: Path, explicit_roots: list[str]) -> list[Path]:
    roots = split_paths(explicit_roots)
    environment = os.environ.get("LOV_SKILL_CATALOG_ROOT")
    if environment:
        roots.extend(split_paths([environment]))
    git_root = run_git(source, "rev-parse", "--show-toplevel")
    anchors = [source.parent, source.parent.parent]
    if git_root:
        git_parent = Path(git_root).parent
        anchors.extend((git_parent, git_parent.parent))
    for anchor in anchors:
        for name in (
            "lovstudio-skills",
            "lovstudio-general-skills",
            "lovstudio-dev-skills",
            "general-skills",
            "dev-skills",
        ):
            candidate = anchor / name
            if candidate.is_dir():
                roots.append(candidate)
    return list(dict.fromkeys(path for path in roots if path.is_dir()))


def catalog_state(directory: Path, short_name: str, source_digest: str | None) -> dict:
    manifest = directory / "skills.yaml"
    sync_scripts = sorted(
        path.relative_to(directory).as_posix()
        for path in directory.rglob("sync-skills.py")
        if not any(part in IGNORED_DIRS for part in path.relative_to(directory).parts)
    )
    matching = []
    for path in directory.rglob("SKILL.md"):
        if any(part in IGNORED_DIRS for part in path.relative_to(directory).parts):
            continue
        if skill_short_name(path.parent) == short_name:
            digest = tree_digest(path.parent)
            matching.append(
                {
                    "path": path.parent.relative_to(directory).as_posix(),
                    "digest": digest,
                    "state": "synced" if digest == source_digest else "drifted",
                }
            )
    state = (
        "synced"
        if matching and all(item["state"] == "synced" for item in matching)
        else "drifted"
        if matching
        else "not_found"
    )
    return {
        "path": str(directory),
        "manifest": str(manifest) if manifest.exists() else None,
        "sync_scripts": sync_scripts,
        "matching_skills": matching,
        "state": state,
    }


def inspect(source: Path, install_roots: list[str], catalog_roots: list[str]) -> dict:
    source = source.expanduser().resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    short_name = skill_short_name(source)
    source_digest = tree_digest(source)
    payload = distribution_payload(source)
    payload_digest = tree_digest(payload)
    installations = []
    for candidate in installation_candidates(source, install_roots):
        resolves_to_payload = candidate.is_symlink() and candidate.resolve() in {source, payload}
        digest = payload_digest if resolves_to_payload else tree_digest(candidate)
        installations.append(
            {
                "path": str(candidate),
                "kind": "symlink" if candidate.is_symlink() else "copy",
                "digest": digest,
                "state": "synced" if digest == payload_digest else "drifted",
            }
        )
    git_root = run_git(source, "rev-parse", "--show-toplevel")
    status = run_git(source, "status", "--porcelain=v1", "--untracked-files=all")
    branch = run_git(source, "branch", "--show-current")
    catalogs = [catalog_state(path, short_name, payload_digest) for path in catalog_candidates(source, catalog_roots)]
    distribution_state = (
        "complete"
        if installations and all(item["state"] == "synced" for item in installations)
        else "partial" if installations else "not_discovered"
    )
    catalog_state_value = (
        "complete"
        if catalogs and all(item["state"] == "synced" for item in catalogs)
        else "partial"
        if catalogs
        else "not_discovered"
    )
    sync_state = (
        "complete"
        if distribution_state == "complete" and catalog_state_value == "complete"
        else "partial"
        if installations or catalogs
        else "not_discovered"
    )
    return {
        "source": {
            "path": str(source),
            "digest": source_digest,
            "git_root": git_root,
            "branch": branch,
            "worktree": "dirty" if status else "clean",
            "status_lines": len(status.splitlines()) if status else 0,
        },
        "payload": {
            "path": str(payload),
            "digest": payload_digest,
            "kind": "public" if payload != source else "source",
        },
        "installations": installations,
        "catalogs": catalogs,
        "distribution_state": distribution_state,
        "catalog_state": catalog_state_value,
        "sync_state": sync_state,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Skill source, installations, and catalog locations")
    parser.add_argument("--path", required=True, help="Path to the canonical Skill directory")
    parser.add_argument("--install-root", action="append", default=[], help="Additional installation root; repeatable")
    parser.add_argument("--catalog-root", action="append", default=[], help="Additional catalog root; repeatable")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    try:
        result = inspect(Path(args.path), args.install_root, args.catalog_root)
    except FileNotFoundError as error:
        print(f"ERROR: skill directory not found: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    source = result["source"]
    print(f"source: {source['path']} ({source['worktree']}, branch={source['branch'] or 'detached'})")
    for installation in result["installations"]:
        print(f"installation: {installation['path']} [{installation['state']}; {installation['kind']}]")
    for catalog in result["catalogs"]:
        print(f"catalog: {catalog['path']} [{catalog['state']}; sync scripts={len(catalog['sync_scripts'])}]")
    print(f"distribution state: {result['distribution_state']}")
    print(f"catalog state: {result['catalog_state']}")
    print(f"sync state: {result['sync_state']}")


if __name__ == "__main__":
    main()
