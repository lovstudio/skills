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
import re
import subprocess
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

from bump_version import read_version_sources


IGNORED_DIRS = {".git", ".worktrees", "node_modules", "dist", "build", "target", ".venv", "venv", "__pycache__", "output"}
DISCOVERY_IGNORED = IGNORED_DIRS | {"assets", "templates", "examples", "fixtures", "tests", "cases", "references", "scripts", "workbuddy", "skillpay"}
INSTALL_ENV_VARS = ("AGENT_SKILLS_DIR", "CLAUDE_SKILLS_DIR", "CODEX_SKILLS_DIR", "SKILLS_DIR")
# lovstudio/general-skills and lovstudio/dev-skills were archived in 2026-08 and
# lovstudio/skills became the only index, so stale split checkouts are not drift.
LEGACY_CATALOG_NAMES = ("lovstudio-general-skills", "lovstudio-dev-skills", "general-skills", "dev-skills")


def skill_spec(source: Path) -> Path | None:
    for relative in ("SKILL.md", "SKILL.md.disabled", "src/SKILL.md", "public/SKILL.md"):
        path = source / relative
        if path.is_file():
            return path
    return None


@lru_cache(maxsize=None)
def skill_name(source: Path) -> str | None:
    spec = skill_spec(source)
    if spec is None:
        return None
    text = spec.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    frontmatter = text.split("\n---", 1)[0]
    match = re.search(r"^name:\s*['\"]?([a-z0-9][a-z0-9:-]*)['\"]?\s*$", frontmatter, re.M)
    return match.group(1) if match else None


def discover_sources(root: Path) -> list[Path]:
    sources = []
    for base, dirs, _ in os.walk(root, followlinks=False):
        directory = Path(base)
        dirs[:] = sorted(d for d in dirs if d not in DISCOVERY_IGNORED and not d.startswith(".") and not (directory / d).is_symlink())
        if skill_spec(directory) is not None:
            sources.append(directory)
            # A paid source/public pair is one package, while Kit modules remain discoverable.
            dirs[:] = [d for d in dirs if d not in {"src", "public"}]
    return sources


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
    for base, dirs, names in os.walk(directory, followlinks=False):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        files.extend(Path(base) / name for name in dirs if (Path(base) / name).is_symlink())
        files.extend(Path(base) / name for name in names if name != ".DS_Store")
    for path in sorted(files):
        relative = path.relative_to(directory).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        try:
            if path.is_symlink():
                digest.update(b"symlink\0" + os.readlink(path).encode("utf-8"))
            else:
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
        except OSError:
            return None
        digest.update(b"\0")
    return digest.hexdigest()


def distribution_payload(source: Path) -> Path:
    """Use the publishable payload for paid/encrypted source repositories."""
    public = source / "public"
    if (source / "src" / "SKILL.md").exists():
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
        for path in (Path.home() / ".agents" / "skills", Path.home() / ".codex" / "skills", Path.home() / ".claude" / "skills")
        if path.is_dir()
    )
    identity = skill_name(source)
    names = [name for name in (identity, f"lov-{skill_short_name(source)}", source.name, skill_short_name(source)) if name]
    result: list[Path] = []
    for root in dict.fromkeys(roots):
        for name in names:
            candidate = root / name
            if (candidate.is_dir() or candidate.is_symlink()) and candidate != source:
                result.append(candidate)
        if root.is_dir():
            for candidate in sorted(root.iterdir()):
                if candidate == source or not candidate.is_dir():
                    continue
                if (candidate.is_symlink() and candidate.resolve() in {source, distribution_payload(source)}) or (identity and skill_name(candidate) == identity):
                    result.append(candidate)
    return list(dict.fromkeys(result))


def catalog_candidates(source: Path, explicit_roots: list[str]) -> list[tuple[Path, bool]]:
    """Return (catalog, legacy) pairs; an explicitly configured root is never legacy."""
    roots = split_paths(explicit_roots)
    environment = os.environ.get("LOV_SKILL_CATALOG_ROOT")
    if environment:
        roots.extend(split_paths([environment]))
    candidates = {path: False for path in roots if path.is_dir()}
    git_root = run_git(source, "rev-parse", "--show-toplevel")
    anchors = [source.parent, source.parent.parent]
    if git_root:
        git_parent = Path(git_root).parent
        anchors.extend((git_parent, git_parent.parent))
    for anchor in anchors:
        for name in ("lovstudio-skills", *LEGACY_CATALOG_NAMES):
            candidate = anchor / name
            if candidate.is_dir():
                candidates.setdefault(candidate, name in LEGACY_CATALOG_NAMES)
    return list(candidates.items())


@lru_cache(maxsize=None)
def catalog_index(directory: Path) -> tuple:
    paths = discover_sources(directory)
    scripts = []
    for base, dirs, names in os.walk(directory, followlinks=False):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        if "sync-skills.py" in names:
            scripts.append((Path(base) / "sync-skills.py").relative_to(directory).as_posix())
    return paths, sorted(scripts)


def catalog_state(directory: Path, short_name: str, source_digest: str | None, identity: str | None = None, legacy: bool = False) -> dict:
    manifest = directory / "skills.yaml"
    paths, sync_scripts = catalog_index(directory)
    matching = []
    for path in paths:
        if (identity and skill_name(path) == identity) or (not identity and skill_short_name(path) == short_name):
            digest = tree_digest(distribution_payload(path))
            matching.append(
                {
                    "path": path.relative_to(directory).as_posix(),
                    "digest": digest,
                    "state": "synced" if digest is not None and digest == source_digest else "drifted",
                }
            )
    state = (
        "legacy"
        if legacy
        else "synced"
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
    if not source.is_dir() or skill_spec(source) is None:
        raise FileNotFoundError(source)
    short_name = skill_short_name(source)
    source_digest = tree_digest(source)
    payload = distribution_payload(source)
    payload_digest = tree_digest(payload)
    installations = []
    for candidate in installation_candidates(source, install_roots):
        resolved = candidate.resolve()
        resolves_to_payload = candidate.is_symlink() and resolved == payload
        digest = payload_digest if resolves_to_payload else tree_digest(candidate)
        state = "synced" if digest is not None and digest == payload_digest else "drifted"
        if not candidate.exists():
            state = "broken_link"
        elif candidate.is_symlink() and not resolves_to_payload:
            state = "wrong_target"
        installations.append(
            {
                "path": str(candidate),
                "kind": "symlink" if candidate.is_symlink() else "copy",
                "resolved": str(resolved),
                "digest": digest,
                "state": state,
            }
        )
    git_root = run_git(source, "rev-parse", "--show-toplevel")
    status = run_git(source, "status", "--porcelain=v1", "--untracked-files=all")
    branch = run_git(source, "branch", "--show-current")
    catalogs = [
        catalog_state(path, short_name, payload_digest, skill_name(source), legacy)
        for path, legacy in catalog_candidates(source, catalog_roots)
    ]
    live_catalogs = [item for item in catalogs if item["state"] != "legacy"]
    distribution_state = (
        "complete"
        if installations and all(item["state"] == "synced" for item in installations)
        else "partial" if installations else "not_discovered"
    )
    catalog_state_value = (
        "complete"
        if live_catalogs and all(item["state"] == "synced" for item in live_catalogs)
        else "partial"
        if live_catalogs
        else "not_discovered"
    )
    sync_state = (
        "complete"
        if distribution_state == "complete" and catalog_state_value == "complete"
        else "partial"
        if installations or live_catalogs
        else "not_discovered"
    )
    return {
        "source": {
            "path": str(source),
            "digest": source_digest,
            "version_sources": read_version_sources(source),
            "git_root": git_root,
            "branch": branch,
            "worktree": "not_versioned" if git_root is None else "unknown" if status is None else "dirty" if status else "clean",
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


def inspect_all(root: Path, install_roots: list[str], catalog_roots: list[str]) -> dict:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    entries, failures = [], []
    groups = defaultdict(list)
    for source in discover_sources(root):
        try:
            result = inspect(source, install_roots, catalog_roots)
            result["id"] = skill_name(source)
            result["lifecycle"] = "disabled" if skill_spec(source).name.endswith(".disabled") else "unclassified"
            entries.append(result)
            if result["id"]:
                groups[result["id"]].append(result)
        except (OSError, ValueError) as error:
            failures.append({"path": str(source), "error": str(error)})
    identities = []
    for identity, candidates in sorted(groups.items()):
        linked = [item["source"]["path"] for item in candidates if any(inst["kind"] == "symlink" and inst["state"] == "synced" for inst in item["installations"])]
        identities.append({
            "id": identity,
            "source_candidates": [item["source"]["path"] for item in candidates],
            "canonical_candidate": candidates[0]["source"]["path"] if len(candidates) == 1 else linked[0] if len(linked) == 1 else None,
            "selection_evidence": "unique_source" if len(candidates) == 1 else "unique_installation_target" if len(linked) == 1 else "ambiguous",
        })
    return {
        "schema": "skill-layout-inventory/v1",
        "root": str(root),
        "scope": "local source and distribution evidence; canonical candidates are inferred, never applied",
        "summary": {"source_entries": len(entries), "unique_ids": len(groups), "duplicate_ids": sum(len(v) > 1 for v in groups.values()), "failures": len(failures), "distribution_states": dict(Counter(x["distribution_state"] for x in entries))},
        "identities": identities,
        "entries": entries,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Skill source, installations, and catalog locations")
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument("--path", help="Path to the canonical Skill directory")
    targets.add_argument("--all", action="store_true", help="Inventory source packages, modules, duplicates and installation targets")
    parser.add_argument("--root", help="Source collection root; required with --all")
    parser.add_argument("--install-root", action="append", default=[], help="Additional installation root; repeatable")
    parser.add_argument("--catalog-root", action="append", default=[], help="Additional catalog root; repeatable")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    if args.all and not args.root:
        parser.error("--all requires --root")
    if args.root and not args.all:
        parser.error("--root requires --all")
    try:
        result = inspect_all(Path(args.root), args.install_root, args.catalog_root) if args.all else inspect(Path(args.path), args.install_root, args.catalog_root)
    except (OSError, ValueError) as error:
        print(f"ERROR: skill directory not found: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.all and result["failures"]:
            raise SystemExit(1)
        return
    if args.all:
        print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
        for item in result["identities"]:
            print(f"{item['id']}: {item['canonical_candidate'] or 'ambiguous'} [{item['selection_evidence']}]")
        if result["failures"]:
            raise SystemExit(1)
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
