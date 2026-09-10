#!/usr/bin/env python3
"""Read-only inventory and safe same-volume organization for storage volumes.

Subcommands:
  inventory   read-only snapshot of a root
  plan        validate a proposed old -> new move map
  apply       execute a validated plan with --confirm
  verify      check source gone, destination present, sidecars paired

This tool never deletes, overwrites, or moves across filesystems.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SCHEMA = "lov-organize-storage"
INVENTORY_SCHEMA = SCHEMA + "/inventory/v1"
PLAN_SCHEMA = SCHEMA + "/move-plan/v1"
LOG_SCHEMA = SCHEMA + "/move-log/v1"

SYSTEM_DIRS = {
    ".Trashes",
    ".Spotlight-V100",
    ".fseventsd",
    ".DocumentRevisions-V100",
    ".TemporaryItems",
    "$RECYCLE.BIN",
    "System Volume Information",
}
TRASH_DIRS = {".Trashes", "$RECYCLE.BIN"}
APP_NAMES = {"JianyingPro", "com.lemon.database"}
APP_SUFFIXES = (".tvlibrary", ".fcpbundle")
PROJECT_FILES = {
    ".git",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Package.swift",
}
PROJECT_SUFFIXES = (
    ".xcodeproj",
    ".xcworkspace",
    ".prproj",
    ".drp",
    ".fcpxml",
    ".screenstudio",
    ".tvlibrary",
)
INSTALLER_SUFFIXES = (".dmg", ".pkg", ".exe", ".msi", ".zip", ".7z", ".tar.gz")
COPY_SUFFIX_RE = re.compile(r"^(?P<base>.+) (?P<number>\d+)(?P<ext>\.[^.]+)$")
RECENT_SECONDS = 48 * 3600


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def expand_path(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser()


def lexists(path: Path) -> bool:
    return os.path.lexists(str(path))


def lstat(path: Path) -> Optional[os.stat_result]:
    try:
        return os.lstat(str(path))
    except OSError:
        return None


def kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "dir"
    return "file"


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def normalize_rel(value: str) -> str:
    text = str(value).strip().replace("\\", "/")
    if not text or text.startswith("/") or re.match(r"^[A-Za-z]:", text):
        raise ValueError("paths must be relative to the target root")
    normalized = posixpath.normpath(text)
    if normalized in ("", ".") or normalized == ".." or normalized.startswith("../"):
        raise ValueError("path escapes the target root")
    return normalized


def system_component(rel_path: str) -> Optional[str]:
    for part in rel_path.split("/"):
        if part in SYSTEM_DIRS:
            return part
    return None


def top_component(rel_path: str) -> str:
    return rel_path.split("/", 1)[0]


def human_kib(value: Optional[int]) -> str:
    if value is None:
        return "unknown"
    units = ["KiB", "MiB", "GiB", "TiB"]
    number = float(value)
    for unit in units:
        if number < 1024 or unit == units[-1]:
            return f"{number:.1f}{unit}"
        number /= 1024
    return f"{value}KiB"


def run_du(path: Path, timeout: int = 900) -> Optional[int]:
    try:
        result = subprocess.run(
            ["du", "-sk", str(path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return int(result.stdout.split()[0])
    except (ValueError, IndexError):
        return None


def open_handles_under(path: Path) -> List[str]:
    """Return open paths under path using lsof when available."""
    try:
        result = subprocess.run(
            ["lsof", "-Fn"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode not in (0, 1):
        return []
    prefix = str(path)
    found: List[str] = []
    for line in result.stdout.splitlines():
        if not line.startswith("n/"):
            continue
        candidate = line[1:]
        if candidate == prefix or candidate.startswith(prefix + os.sep):
            found.append(candidate)
    return found


def sample_dir(path: Path, max_files: int = 20000) -> Dict[str, Any]:
    """Sample a directory for recent files, zero-byte-only signal, and sidecars."""
    now = time.time()
    total = 0
    zero = 0
    recent = 0
    sidecars = 0
    truncated = False
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as iterator:
                for entry in iterator:
                    total += 1
                    if total > max_files:
                        truncated = True
                        stack = []
                        break
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    if entry.name.startswith("._"):
                        sidecars += 1
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    else:
                        if st.st_size == 0:
                            zero += 1
                        if now - st.st_mtime <= RECENT_SECONDS:
                            recent += 1
        except OSError:
            continue
    return {
        "sampled_files": total,
        "zero_byte_files": zero,
        "recent_files": recent,
        "appledouble_sidecars": sidecars,
        "truncated": truncated,
    }


def copy_suffix_signal(path: Path, max_entries: int = 50000) -> int:
    names: set = set()
    try:
        with os.scandir(path) as iterator:
            for entry in iterator:
                names.add(entry.name)
                if len(names) >= max_entries:
                    break
    except OSError:
        return 0
    count = 0
    for name in names:
        match = COPY_SUFFIX_RE.match(name)
        if not match:
            continue
        base = match.group("base") + match.group("ext")
        if base in names:
            count += 1
    return count


def classify_entry(path: Path, rel_path: str) -> List[str]:
    warnings: List[str] = []
    name = path.name
    lower = name.lower()
    if name in SYSTEM_DIRS:
        warnings.append("SYSTEM_DIR")
    if name in TRASH_DIRS:
        warnings.append("TRASH_DIR")
    if path.is_symlink() and not lexists(path):
        warnings.append("BROKEN_SYMLINK")
    if path.is_file():
        if lower.endswith(INSTALLER_SUFFIXES):
            warnings.append("INSTALLER")
    if name in APP_NAMES or lower.endswith(APP_SUFFIXES):
        warnings.append("APP_LIBRARY")
    if name in PROJECT_FILES or lower.endswith(PROJECT_SUFFIXES):
        warnings.append("PROJECT_MARKER")
    return warnings


def inventory(root: Path, max_depth: int, sizes: bool) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {
        "top_level_entries": 0,
        "system_dirs": [],
        "trash_dirs": [],
        "app_libraries": [],
        "project_markers": [],
        "installers": [],
        "broken_symlinks": [],
        "zero_byte_only_dirs": [],
        "copy_suffix_candidates": 0,
    }

    def walk(current: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            children = sorted(os.scandir(current), key=lambda item: item.name)
        except OSError:
            return
        for entry in children:
            path = Path(entry.path)
            rel_path = rel_posix(path, root)
            item_kind = kind(path)
            st = lstat(path)
            warnings = classify_entry(path, rel_path)
            size_kib: Optional[int] = None
            if sizes and depth == 1 and item_kind == "dir":
                size_kib = run_du(path)
            elif st is not None:
                size_kib = (st.st_size + 1023) // 1024
            item: Dict[str, Any] = {
                "path": rel_path,
                "kind": item_kind,
                "depth": depth,
                "size_kib": size_kib,
                "mtime": st.st_mtime if st else None,
                "warnings": warnings,
            }
            if item_kind == "symlink":
                try:
                    item["target"] = os.readlink(str(path))
                except OSError:
                    item["target"] = None
            if depth == 1:
                summary["top_level_entries"] += 1
                if "SYSTEM_DIR" in warnings:
                    summary["system_dirs"].append(rel_path)
                if "TRASH_DIR" in warnings:
                    summary["trash_dirs"].append(rel_path)
                if "APP_LIBRARY" in warnings:
                    summary["app_libraries"].append(rel_path)
                if "PROJECT_MARKER" in warnings:
                    summary["project_markers"].append(rel_path)
                if "INSTALLER" in warnings:
                    summary["installers"].append(rel_path)
                if "BROKEN_SYMLINK" in warnings:
                    summary["broken_symlinks"].append(rel_path)
                if item_kind == "dir" and not any(
                    part in SYSTEM_DIRS for part in rel_path.split("/")
                ):
                    sample = sample_dir(path)
                    item["sample"] = sample
                    if sample["sampled_files"] > 0 and sample["zero_byte_files"] == sample["sampled_files"]:
                        summary["zero_byte_only_dirs"].append(rel_path)
                        item["warnings"].append("ZERO_BYTE_ONLY")
                    if sample["recent_files"] > 0:
                        item["warnings"].append("RECENT_ACTIVITY")
                    suffix = copy_suffix_signal(path)
                    item["copy_suffix_candidates"] = suffix
                    summary["copy_suffix_candidates"] += suffix
            entries.append(item)
            if item_kind == "dir" and depth < max_depth:
                walk(path, depth + 1)

    walk(root, 1)
    disk = None
    try:
        usage = os.statvfs(str(root))
        disk = {
            "total_bytes": usage.f_blocks * usage.f_frsize,
            "free_bytes": usage.f_bavail * usage.f_frsize,
            "filesystem": "statvfs",
        }
    except OSError:
        pass
    return {
        "schema": INVENTORY_SCHEMA,
        "root": str(root),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "max_depth": max_depth,
        "disk": disk,
        "summary": summary,
        "entries": entries,
    }


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_map(path: Path) -> List[Tuple[str, str]]:
    data = load_json(path)
    raw_moves = data.get("moves") if isinstance(data, dict) else data
    if not isinstance(raw_moves, list) or not raw_moves:
        raise ValueError("move map must contain a non-empty moves list")
    moves: List[Tuple[str, str]] = []
    for index, item in enumerate(raw_moves):
        if isinstance(item, dict):
            src, dst = item.get("src"), item.get("dst")
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            src, dst = item
        else:
            raise ValueError(f"moves[{index}] must be an object or a two-item list")
        if not isinstance(src, str) or not isinstance(dst, str):
            raise ValueError(f"moves[{index}] src and dst must be strings")
        moves.append((normalize_rel(src), normalize_rel(dst)))
    return moves


def nearest_existing_ancestor(path: Path) -> Path:
    current = path
    while not lexists(current):
        parent = current.parent
        if parent == current:
            return current
        current = parent
    return current


def validate_move(
    root: Path,
    src: str,
    dst: str,
    allow_app_libraries: bool,
    sizes: bool = False,
    check_open: bool = False,
) -> Dict[str, Any]:
    src_abs = root / src
    dst_abs = root / dst
    hard_blocks: List[str] = []
    warnings: List[str] = []

    if not lexists(src_abs):
        hard_blocks.append(f"MISSING_SOURCE:{src}")
    if lexists(dst_abs):
        hard_blocks.append(f"DESTINATION_EXISTS:{dst}")

    blocked_system = system_component(src)
    if blocked_system:
        hard_blocks.append(f"SYSTEM_PATH_DENYLIST:{blocked_system}")
    if top_component(src) in TRASH_DIRS:
        hard_blocks.append("TRASH_SEALED: trash directories are never moved")

    st_root = lstat(root)
    root_device = st_root.st_dev if st_root is not None else None
    st_src = lstat(src_abs)
    src_device = st_src.st_dev if st_src is not None else None
    if root_device is not None and src_device is not None and root_device != src_device:
        hard_blocks.append("CROSS_DEVICE_SOURCE")

    destination_device = None
    destination_parent = dst_abs.parent
    ancestor = destination_parent if lexists(destination_parent) else nearest_existing_ancestor(destination_parent)
    st_ancestor = lstat(ancestor)
    if st_ancestor is not None:
        destination_device = st_ancestor.st_dev
    if destination_device is not None and root_device is not None and destination_device != root_device:
        hard_blocks.append("CROSS_DEVICE_DESTINATION")

    item_kind = kind(src_abs) if lexists(src_abs) else "missing"
    item: Dict[str, Any] = {
        "src": src,
        "dst": dst,
        "kind": item_kind,
        "hard_blocks": hard_blocks,
        "warnings": warnings,
    }

    sidecar_src = src_abs.parent / ("._" + src_abs.name)
    sidecar_dst = dst_abs.parent / ("._" + dst_abs.name)
    if lexists(sidecar_src):
        item["sidecar_src"] = rel_posix(sidecar_src, root)
        item["sidecar_dst"] = rel_posix(sidecar_dst, root)
        item["sidecar_note"] = "macOS may move the sidecar automatically; apply verifies both cases"

    if lexists(src_abs) and sizes and item_kind == "dir":
        item["size_kib"] = run_du(src_abs)

    if lexists(src_abs) and item_kind == "dir":
        sample = sample_dir(src_abs)
        item["sample"] = sample
        if sample["sampled_files"] > 0 and sample["zero_byte_files"] == sample["sampled_files"]:
            warnings.append("ZERO_BYTE_ONLY")
        if sample["recent_files"] > 0:
            warnings.append("RECENT_ACTIVITY")
        suffix_count = copy_suffix_signal(src_abs)
        if suffix_count:
            item["copy_suffix_candidates"] = suffix_count
            warnings.append("COPY_SUFFIX_SIGNAL")
        if check_open:
            handles = open_handles_under(src_abs)
            if handles:
                item["open_handles"] = handles[:20]
                warnings.append("OPEN_HANDLE")

    name = src_abs.name
    if not allow_app_libraries and (name in APP_NAMES or name.lower().endswith(APP_SUFFIXES)):
        hard_blocks.append("APP_LIBRARY_REQUIRES_ACK")
    return item


def validate_plan(
    root: Path,
    moves: List[Tuple[str, str]],
    allow_app_libraries: bool,
    sizes: bool = False,
    check_open: bool = False,
) -> Dict[str, Any]:
    items = [validate_move(root, src, dst, allow_app_libraries, sizes, check_open) for src, dst in moves]
    hard_blocks: List[str] = []
    warnings: List[str] = []
    for index, item in enumerate(items):
        hard_blocks.extend(f"moves[{index}]:{code}" for code in item["hard_blocks"])
        warnings.extend(f"moves[{index}]:{code}" for code in item["warnings"])
    for i, (src_a, dst_a) in enumerate(moves):
        for j, (src_b, dst_b) in enumerate(moves):
            if i == j:
                continue
            if src_a == src_b:
                hard_blocks.append(f"moves[{i}] and moves[{j}] share the same source")
            if src_a.startswith(src_b + "/"):
                hard_blocks.append(f"moves[{i}] source is inside moves[{j}] source")
            if dst_a.startswith(dst_b + "/"):
                hard_blocks.append(f"moves[{i}] destination is inside moves[{j}] destination")
            if dst_a == src_b or dst_a.startswith(src_b + "/"):
                hard_blocks.append(f"moves[{i}] destination is inside moves[{j}] moving source")
            if src_a == dst_b or src_a.startswith(dst_b + "/"):
                hard_blocks.append(f"moves[{i}] source is inside moves[{j}] destination")
    return {
        "schema": PLAN_SCHEMA,
        "root": str(root),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "allow_app_libraries": allow_app_libraries,
        "blocked": bool(hard_blocks),
        "hard_blocks": hard_blocks,
        "warnings": warnings,
        "moves": items,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_rollback(log: Dict[str, Any], path: Path) -> None:
    lines = ["#!/bin/zsh", "set -e", f'cd "{log["root"]}"', ""]
    for record in reversed(log.get("moves", [])):
        src, dst = record["src"], record["dst"]
        lines.append(f'if [ -e "{dst}" ] && [ ! -e "{src}" ]; then')
        lines.append(f'  mkdir -p "$(dirname "{src}")"')
        lines.append(f'  mv -n -- "{dst}" "{src}"')
        sidecar = record.get("sidecar", {})
        if sidecar.get("mode") == "manual":
            sc_dst, sc_src = sidecar["dst"], sidecar["src"]
            lines.append(
                f'  if [ -e "{sc_dst}" ] && [ ! -e "{sc_src}" ]; then '
                f'mkdir -p "$(dirname "{sc_src}")"; mv -n -- "{sc_dst}" "{sc_src}"; fi'
            )
        lines.append("fi")
    lines.append("")
    lines.append('echo "rollback complete (best effort; mapping.json is source of truth)"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o755)


def apply_plan(plan: Dict[str, Any], log_dir: Path, accept_warnings: bool) -> Dict[str, Any]:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("plan schema mismatch")
    if plan.get("blocked"):
        raise ValueError("plan is blocked: " + "; ".join(plan.get("hard_blocks", [])))
    if plan.get("warnings") and not accept_warnings:
        raise ValueError("plan has warnings; pass --accept-warnings after reviewing them")
    allow_app_libraries = bool(plan.get("allow_app_libraries"))
    root = Path(plan["root"]).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    log: Dict[str, Any] = {
        "schema": LOG_SCHEMA,
        "root": str(root),
        "plan_generated_at": plan.get("generated_at"),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "allow_app_libraries": allow_app_libraries,
        "moves": [],
        "ok": False,
    }
    try:
        for item in plan["moves"]:
            src_rel, dst_rel = item["src"], item["dst"]
            src_abs, dst_abs = root / src_rel, root / dst_rel
            if not lexists(src_abs):
                raise ValueError(f"source disappeared: {src_rel}")
            if lexists(dst_abs):
                raise ValueError(f"destination appeared: {dst_rel}")
            if system_component(src_rel) or top_component(src_rel) in TRASH_DIRS:
                raise ValueError(f"refusing protected path: {src_rel}")
            log_real = Path(os.path.realpath(str(log_dir)))
            src_real = Path(os.path.realpath(str(src_abs)))
            if is_inside(log_real, src_real):
                raise ValueError("log directory must not be inside a moving source")
            name = src_abs.name
            if not allow_app_libraries and (name in APP_NAMES or name.lower().endswith(APP_SUFFIXES)):
                raise ValueError(f"app library requires explicit allow: {src_rel}")
            pre = lstat(src_abs)
            sidecar_src = src_abs.parent / ("._" + src_abs.name)
            sidecar_dst = dst_abs.parent / ("._" + dst_abs.name)
            sidecar_present = lexists(sidecar_src)
            dst_abs.parent.mkdir(parents=True, exist_ok=True)
            os.rename(str(src_abs), str(dst_abs))
            post = lstat(dst_abs)
            record: Dict[str, Any] = {
                "src": src_rel,
                "dst": dst_rel,
                "kind": kind(dst_abs),
                "size_kib": item.get("size_kib"),
                "pre": {
                    "ino": getattr(pre, "st_ino", None),
                    "size": getattr(pre, "st_size", None),
                    "mtime_ns": getattr(pre, "st_mtime_ns", None),
                } if pre else None,
                "post": {
                    "ino": getattr(post, "st_ino", None),
                    "size": getattr(post, "st_size", None),
                    "mtime_ns": getattr(post, "st_mtime_ns", None),
                } if post else None,
                "source_gone": not lexists(src_abs),
                "destination_present": lexists(dst_abs),
            }
            sidecar: Dict[str, Any] = {
                "src": rel_posix(sidecar_src, root),
                "dst": rel_posix(sidecar_dst, root),
            }
            if lexists(sidecar_src) and not lexists(sidecar_dst):
                os.rename(str(sidecar_src), str(sidecar_dst))
                sidecar["mode"] = "manual"
            elif lexists(sidecar_dst):
                sidecar["mode"] = "auto"
            elif sidecar_present:
                sidecar["mode"] = "missing"
            else:
                sidecar["mode"] = "none"
            record["sidecar"] = sidecar
            log["moves"].append(record)
        log["ok"] = True
    except (OSError, ValueError) as exc:
        log["ok"] = False
        log["error"] = str(exc)
    log["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    return log


def verify_plan(plan: Dict[str, Any], log: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    root = Path(plan["root"]).resolve()
    results = []
    failures = []
    log_by_src = {}
    if log:
        log_by_src = {item["src"]: item for item in log.get("moves", [])}
    for item in plan.get("moves", []):
        src_rel, dst_rel = item["src"], item["dst"]
        src_abs, dst_abs = root / src_rel, root / dst_rel
        result = {
            "src": src_rel,
            "dst": dst_rel,
            "destination_present": lexists(dst_abs),
            "source_gone": not lexists(src_abs),
            "sidecar_src_present": lexists(src_abs.parent / ("._" + src_abs.name)),
            "sidecar_dst_present": lexists(dst_abs.parent / ("._" + dst_abs.name)),
        }
        if not result["destination_present"]:
            failures.append(f"DESTINATION_MISSING:{dst_rel}")
        if not result["source_gone"]:
            failures.append(f"SOURCE_STILL_PRESENT:{src_rel}")
        if result["sidecar_src_present"] and not result["sidecar_dst_present"]:
            failures.append(f"SIDECAR_SOURCE_ONLY:{src_rel}")
        results.append(result)
    return {
        "schema": SCHEMA + "/verify/v1",
        "root": str(root),
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "ok": not failures,
        "failures": failures,
        "results": results,
    }


def command_inventory(args: argparse.Namespace) -> int:
    root = expand_path(args.root).resolve()
    if not root.is_dir():
        eprint(f"ERROR: root is not a directory: {root}")
        return 2
    data = inventory(root, args.max_depth, args.sizes)
    if args.out:
        write_json(expand_path(args.out), data)
        print(f"inventory written: {args.out}")
    else:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        print()
    summary = data["summary"]
    print(
        "top_level={} system={} trash={} apps={} broken_symlinks={} copy_suffix_candidates={}".format(
            summary["top_level_entries"],
            len(summary["system_dirs"]),
            len(summary["trash_dirs"]),
            len(summary["app_libraries"]),
            len(summary["broken_symlinks"]),
            summary["copy_suffix_candidates"],
        ),
        file=sys.stderr,
    )
    return 0


def command_plan(args: argparse.Namespace) -> int:
    root = expand_path(args.root).resolve()
    if not root.is_dir():
        eprint(f"ERROR: root is not a directory: {root}")
        return 2
    try:
        moves = parse_map(expand_path(args.map))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        eprint(f"ERROR: invalid move map: {exc}")
        return 2
    plan = validate_plan(root, moves, args.allow_app_libraries, args.sizes, args.check_open)
    if args.out:
        write_json(expand_path(args.out), plan)
        print(f"plan written: {args.out}")
    else:
        json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
        print()
    for code in plan["hard_blocks"]:
        eprint(f"HARD BLOCK: {code}")
    for code in plan["warnings"]:
        eprint(f"WARNING: {code}")
    return 1 if plan["blocked"] else 0


def command_apply(args: argparse.Namespace) -> int:
    plan_path = expand_path(args.plan)
    try:
        plan = load_json(plan_path)
    except (OSError, json.JSONDecodeError) as exc:
        eprint(f"ERROR: cannot read plan: {exc}")
        return 2
    log_dir = expand_path(args.log_dir)
    try:
        log = apply_plan(plan, log_dir, args.accept_warnings)
    except (OSError, ValueError) as exc:
        eprint(f"ERROR: apply failed: {exc}")
        return 1
    write_json(log_dir / "mapping.json", log)
    write_rollback(log, log_dir / "rollback.sh")
    if not log.get("ok"):
        eprint(f"ERROR: apply stopped: {log.get('error')}")
        eprint(f"partial log written: {log_dir / 'mapping.json'}")
        return 1
    print(f"applied={len(log['moves'])} log_dir={log_dir}")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    try:
        plan = load_json(expand_path(args.plan))
    except (OSError, json.JSONDecodeError) as exc:
        eprint(f"ERROR: cannot read plan: {exc}")
        return 2
    log = None
    log_path = expand_path(args.log_dir) / "mapping.json"
    if log_path.is_file():
        try:
            log = load_json(log_path)
        except (OSError, json.JSONDecodeError) as exc:
            eprint(f"ERROR: cannot read log: {exc}")
            return 2
    result = verify_plan(plan, log)
    if args.out:
        write_json(expand_path(args.out), result)
        print(f"verification written: {args.out}")
    else:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
    for failure in result["failures"]:
        eprint(f"FAIL: {failure}")
    return 0 if result["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    inventory_parser = sub.add_parser("inventory", help="read-only inventory of a storage root")
    inventory_parser.add_argument("--root", required=True)
    inventory_parser.add_argument("--max-depth", type=int, default=1)
    inventory_parser.add_argument("--sizes", action="store_true", help="run du -sk for top-level directories")
    inventory_parser.add_argument("--out", default="")
    inventory_parser.set_defaults(func=command_inventory)

    plan_parser = sub.add_parser("plan", help="validate a proposed old -> new move map")
    plan_parser.add_argument("--root", required=True)
    plan_parser.add_argument("--map", required=True)
    plan_parser.add_argument("--out", default="")
    plan_parser.add_argument("--allow-app-libraries", action="store_true")
    plan_parser.add_argument("--sizes", action="store_true", help="run du -sk for source directories")
    plan_parser.add_argument("--check-open", action="store_true", help="scan lsof for open handles (slower)")
    plan_parser.set_defaults(func=command_plan)

    apply_parser = sub.add_parser("apply", help="execute a validated plan with --confirm")
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--log-dir", required=True)
    apply_parser.add_argument("--confirm", action="store_true", required=True)
    apply_parser.add_argument("--accept-warnings", action="store_true")
    apply_parser.set_defaults(func=command_apply)

    verify_parser = sub.add_parser("verify", help="verify source gone, destination present, sidecars paired")
    verify_parser.add_argument("--plan", required=True)
    verify_parser.add_argument("--log-dir", required=True)
    verify_parser.add_argument("--out", default="")
    verify_parser.set_defaults(func=command_verify)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
