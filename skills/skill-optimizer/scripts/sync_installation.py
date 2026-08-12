#!/usr/bin/env python3
"""Plan or apply a canonical Skill tree sync to installation copies.

The default mode is read-only. Symlink installations are reported as already
source-backed; copy installations can be updated explicitly with --apply.
Extra target files are retained unless --prune is supplied together with
--apply.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".worktrees",
    "node_modules",
    "dist",
    "build",
    "target",
    ".venv",
    "__pycache__",
}


def payload_files(directory: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not directory.is_dir():
        return files
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_file() and not path.is_symlink():
            files[relative.as_posix()] = path
    return files


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare(source: Path, target: Path) -> dict:
    source_files = payload_files(source)
    target_files = payload_files(target)
    missing = sorted(set(source_files) - set(target_files))
    changed = sorted(
        relative
        for relative in set(source_files) & set(target_files)
        if file_digest(source_files[relative]) != file_digest(target_files[relative])
    )
    extra = sorted(set(target_files) - set(source_files))
    return {"missing": missing, "changed": changed, "extra": extra}


def remove_extra_files(target: Path, relative_paths: list[str]) -> None:
    for relative in relative_paths:
        path = target / relative
        if path.is_file() or path.is_symlink():
            path.unlink()
    directories = sorted(
        {path.parent for path in (target / relative for relative in relative_paths)},
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        if directory == target:
            continue
        try:
            directory.rmdir()
        except OSError:
            pass


def copy_files(source: Path, target: Path, relative_paths: list[str]) -> None:
    for relative in relative_paths:
        source_path = source / relative
        target_path = target / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def sync_target(source: Path, target: Path, apply: bool, prune: bool) -> dict:
    source = source.resolve()
    target_is_symlink = target.is_symlink()
    if target_is_symlink:
        resolved = target.resolve()
        state = "synced" if resolved == source else "drifted"
        return {
            "path": str(target),
            "kind": "symlink",
            "resolved": str(resolved),
            "state": state,
            "action": "none",
        }

    if target.resolve() == source:
        raise ValueError(f"target resolves to source: {target}")

    target.mkdir(parents=True, exist_ok=True)
    before = compare(source, target)
    if apply:
        copy_files(source, target, before["missing"] + before["changed"])
        if prune:
            remove_extra_files(target, before["extra"])
    after = compare(source, target)
    state = "synced" if not any(after.values()) else "drifted"
    return {
        "path": str(target),
        "kind": "copy",
        "state": state,
        "action": "applied" if apply else "planned",
        "before": before,
        "after": after,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or sync a Skill installation copy")
    parser.add_argument("--source", required=True, help="Canonical Skill directory")
    parser.add_argument("--target", action="append", required=True, help="Installation directory; repeatable")
    parser.add_argument("--apply", action="store_true", help="Copy canonical files to targets")
    parser.add_argument("--prune", action="store_true", help="Remove extra target files; requires --apply")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable result")
    args = parser.parse_args()

    if args.prune and not args.apply:
        parser.error("--prune requires --apply")

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        parser.error(f"source directory not found: {source}")

    try:
        targets = [Path(value).expanduser() for value in args.target]
        result = {
            "source": str(source),
            "mode": "apply" if args.apply else "plan",
            "prune": args.prune,
            "targets": [sync_target(source, target, args.apply, args.prune) for target in targets],
        }
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"source: {source}")
        for target in result["targets"]:
            print(f"target: {target['path']} [{target['state']}; {target['kind']}; {target['action']}]")


if __name__ == "__main__":
    main()
