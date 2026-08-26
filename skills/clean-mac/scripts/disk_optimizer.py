#!/usr/bin/env python3
"""Plan and execute guarded macOS disk-space recovery operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DECIMAL_GB = 1_000_000_000
DEFAULT_DATA_VOLUME = Path("/System/Volumes/Data")


def default_preferences_path() -> Path:
    explicit = os.environ.get("SKILL_PREFERENCES_PATH")
    if explicit:
        return Path(explicit).expanduser()
    config_dir = os.environ.get("SKILLS_CONFIG_DIR")
    if config_dir:
        return Path(config_dir).expanduser() / "preferences.json"
    return Path.home() / ".config" / "agent-skills" / "preferences.json"


DEFAULT_PROFILE = default_preferences_path()
PROFILE_KEY = "macos_disk_optimizer"
PURGE_CONFIRM = "PURGE_STAGED"

REBUILDABLE_NAMES = {
    ".next",
    ".turbo",
    "Caches",
    "DerivedData",
    "DeviceSupport",
    "build",
    "dist",
    "models",
    "node_modules",
    "target",
    "_npx",
}
PROTECTED_PARTS = {
    ".git",
    "Keychains",
    "Mail",
    "Messages",
    "Photos Library.photoslibrary",
    "sessions",
}
BUILTIN_PROTECTED_RELATIVE_PATHS = (
    Path("Library") / "Application Support" / "Screen Studio" / "Screen Studio Recordings",
)
SKIP_DISCOVERY = {".git", ".Trash", "Library", "Photos Library.photoslibrary"}


class OptimizerError(RuntimeError):
    """User-facing operational error."""


def emit(payload: Dict[str, Any], output: Optional[Path] = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output:
        output = output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def decimal_gb(value: int) -> float:
    return round(value / DECIMAL_GB, 2)


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def lexical(path: Path) -> Path:
    """Normalize a path without resolving symlinks."""
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def builtin_protected_paths() -> Tuple[Path, ...]:
    """Return application-managed workspaces that cleanup must never mutate."""
    return tuple(lexical(Path.home() / relative) for relative in BUILTIN_PROTECTED_RELATIVE_PATHS)


def paths_overlap(left: Path, right: Path) -> bool:
    """Return whether either path contains the other."""
    return left == right or is_relative_to(left, right) or is_relative_to(right, left)


def protected(path: Path, extra: Sequence[Path]) -> bool:
    path_variants = {lexical(path), resolved(path)}
    if any(part in PROTECTED_PARTS for variant in path_variants for part in variant.parts):
        return True
    protected_roots = (*builtin_protected_paths(), *extra)
    root_variants = {
        variant
        for root in protected_roots
        for variant in (lexical(root), resolved(root))
    }
    return any(paths_overlap(path_variant, root_variant) for path_variant in path_variants for root_variant in root_variants)


def guard_mutation_target(path: Path) -> Path:
    path = resolved(path)
    forbidden = {Path("/"), Path.home(), DEFAULT_DATA_VOLUME}
    if path in forbidden or len(path.parts) < 4:
        raise OptimizerError(f"拒绝过宽的修改目标：{path}")
    return path


def tree_stats(path: Path) -> Tuple[int, int]:
    """Return logical bytes and file-like entry count without following symlinks."""
    path = path.expanduser()
    if path.is_symlink():
        return 0, 1
    if path.is_file():
        return path.stat().st_size, 1
    total = 0
    count = 0
    for root, dirs, files in os.walk(str(path), followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(root) / name).is_symlink()]
        for name in files:
            item = Path(root) / name
            try:
                total += item.lstat().st_size
                count += 1
            except (FileNotFoundError, PermissionError):
                continue
    return total, count


def du_bytes(path: Path) -> int:
    try:
        result = subprocess.run(
            ["du", "-sk", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.stdout.strip():
            return int(result.stdout.strip().splitlines()[-1].split()[0]) * 1024
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return tree_stats(path)[0]


def classify(path: Path, extra_protected: Sequence[Path]) -> str:
    if protected(path, extra_protected):
        return "protected"
    if path.name in REBUILDABLE_NAMES:
        return "rebuildable"
    return "review-for-archive"


def mounted_volume(path: Path) -> Path:
    current = resolved(path)
    while current != current.parent and not os.path.ismount(str(current)):
        current = current.parent
    return current


def existing_ancestor(path: Path) -> Path:
    current = resolved(path)
    while current != current.parent and not current.exists():
        current = current.parent
    if not current.exists():
        raise OptimizerError(f"找不到可用的目标父目录：{path}")
    return current


def run_status(args: argparse.Namespace) -> int:
    volume = resolved(args.volume)
    usage = shutil.disk_usage(str(volume))
    payload = {
        "volume": str(volume),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "total_gb": decimal_gb(usage.total),
        "used_gb": decimal_gb(usage.used),
        "free_gb": decimal_gb(usage.free),
    }
    emit(payload, args.output)
    return 0


def discover_artifacts(root: Path, minimum_bytes: int, extra_protected: Sequence[Path]) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []
    for current, dirs, _files in os.walk(str(root), followlinks=False):
        current_path = Path(current)
        kept: List[str] = []
        for name in dirs:
            child = current_path / name
            if child.is_symlink() or name in SKIP_DISCOVERY or protected(child, extra_protected):
                continue
            if name in REBUILDABLE_NAMES:
                size = du_bytes(child)
                if size >= minimum_bytes:
                    found.append(candidate(child, size, "rebuildable", "可重新生成的依赖、缓存或构建产物"))
                continue
            kept.append(name)
        dirs[:] = kept
    return found


def candidate(path: Path, size: int, category: str, reason: str) -> Dict[str, Any]:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        mtime = None
    return {
        "path": str(path),
        "size_bytes": size,
        "size_gb": decimal_gb(size),
        "category": category,
        "reason": reason,
        "modified_at": mtime,
    }


def run_inventory(args: argparse.Namespace) -> int:
    roots = [resolved(item) for item in args.root]
    extra_protected = [item.expanduser() for item in args.protected]
    minimum_bytes = int(args.min_gb * DECIMAL_GB)
    items: List[Dict[str, Any]] = []
    seen = set()
    for root in roots:
        if not root.is_dir():
            raise OptimizerError(f"扫描根目录不存在：{root}")
        children = sorted(root.iterdir(), key=lambda item: item.name.lower())
        for child in children:
            if child.is_symlink() or (child.name.startswith(".") and not args.include_hidden):
                continue
            size = du_bytes(child)
            if size < minimum_bytes:
                continue
            category = classify(child, extra_protected)
            reason = {
                "protected": "命中保护路径或敏感数据类型",
                "rebuildable": "可重新生成的依赖、缓存或构建产物",
                "review-for-archive": "体积较大；需结合活跃状态与用户价值判断迁移",
            }[category]
            items.append(candidate(child, size, category, reason))
            seen.add(str(resolved(child)))
        if not args.no_artifacts:
            for item in discover_artifacts(root, minimum_bytes, extra_protected):
                if str(resolved(Path(item["path"]))) not in seen:
                    items.append(item)
    data_volume = resolved(args.volume)
    usage = shutil.disk_usage(str(data_volume))
    items.sort(key=lambda item: item["size_bytes"], reverse=True)
    emit(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "volume": str(data_volume),
            "free_bytes": usage.free,
            "free_gb": decimal_gb(usage.free),
            "roots": [str(item) for item in roots],
            "candidates": items,
            "notes": [
                "修改日期只作判断信号，不自动等同于闲置或可删除。",
                "protected 候选永不进入自动清理计划。",
                "目录大小可能包含嵌套候选，计划值是保守估算而非可相加账单。",
            ],
        },
        args.output,
    )
    return 0


def load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OptimizerError(f"JSON 根节点必须是对象：{path}")
    return data


def run_plan(args: argparse.Namespace) -> int:
    inventory = load_json(args.inventory)
    free_bytes = int(inventory.get("free_bytes", 0))
    target_bytes = int(args.target_free_gb * DECIMAL_GB)
    buffer_bytes = int(args.buffer_gb * DECIMAL_GB)
    need = max(0, target_bytes + buffer_bytes - free_bytes)
    candidates = inventory.get("candidates", [])
    if not isinstance(candidates, list):
        raise OptimizerError("inventory.candidates 必须是数组")
    ordered = sorted(
        (item for item in candidates if item.get("category") != "protected"),
        key=lambda item: (0 if item.get("category") == "rebuildable" else 1, -int(item.get("size_bytes", 0))),
    )
    selected: List[Dict[str, Any]] = []
    estimated = 0
    selected_paths: List[Path] = []
    for item in ordered:
        path = resolved(Path(str(item.get("path", ""))))
        if any(is_relative_to(path, parent) or is_relative_to(parent, path) for parent in selected_paths):
            continue
        if estimated >= need:
            break
        action = "stage-cleanup" if item.get("category") == "rebuildable" else "review-for-archive"
        selected.append({**item, "recommended_action": action})
        selected_paths.append(path)
        estimated += int(item.get("size_bytes", 0))
    emit(
        {
            "target_free_gb": args.target_free_gb,
            "buffer_gb": args.buffer_gb,
            "current_free_gb": decimal_gb(free_bytes),
            "required_reclaim_gb": decimal_gb(need),
            "estimated_selected_gb": decimal_gb(estimated),
            "target_already_met": need == 0,
            "sufficient_candidates": estimated >= need,
            "actions": selected,
            "execution_rule": "先执行 rebuildable；archive 候选需结合上下文确认，计划本身不删除或迁移。",
        },
        args.output,
    )
    return 0 if estimated >= need else 3


def run_preflight(args: argparse.Namespace) -> int:
    root = resolved(args.archive_root)
    if not root.exists() or not root.is_dir():
        raise OptimizerError(f"归档根目录不存在：{root}")
    usage = shutil.disk_usage(str(root))
    mount = mounted_volume(root)
    writable = False
    try:
        with tempfile.NamedTemporaryFile(prefix=".lov-disk-check-", dir=str(root)):
            writable = True
    except OSError:
        writable = False
    payload = {
        "archive_root": str(root),
        "mount_point": str(mount),
        "writable": writable,
        "free_bytes": usage.free,
        "free_gb": decimal_gb(usage.free),
        "required_gb": args.required_gb,
        "enough_space": writable and usage.free >= int(args.required_gb * DECIMAL_GB),
    }
    emit(payload, args.output)
    return 0 if payload["enough_space"] else 3


def metadata_manifest(path: Path) -> Dict[str, Tuple[str, int]]:
    result: Dict[str, Tuple[str, int]] = {}
    if path.is_file():
        result[path.name] = ("file", path.stat().st_size)
        return result
    for root, dirs, files in os.walk(str(path), followlinks=False):
        root_path = Path(root)
        for name in dirs:
            item = root_path / name
            rel = str(item.relative_to(path))
            result[rel] = ("symlink" if item.is_symlink() else "dir", 0)
        for name in files:
            item = root_path / name
            try:
                result[str(item.relative_to(path))] = ("file", item.lstat().st_size)
            except OSError:
                continue
    return result


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_copy(source: Path, destination: Path, level: str) -> Dict[str, Any]:
    source_manifest = metadata_manifest(source)
    destination_manifest = metadata_manifest(destination)
    if source_manifest != destination_manifest:
        missing = sorted(set(source_manifest) - set(destination_manifest))[:20]
        extra = sorted(set(destination_manifest) - set(source_manifest))[:20]
        changed = sorted(
            key for key in set(source_manifest) & set(destination_manifest)
            if source_manifest[key] != destination_manifest[key]
        )[:20]
        raise OptimizerError(f"复制校验差异：missing={missing}, extra={extra}, changed={changed}")
    checked = 0
    if level == "checksum":
        pairs: Iterable[Tuple[Path, Path]]
        if source.is_file():
            pairs = [(source, destination)]
        else:
            pairs = (
                (source / rel, destination / rel)
                for rel, (kind, _size) in source_manifest.items()
                if kind == "file"
            )
        for left, right in pairs:
            if hash_file(left) != hash_file(right):
                raise OptimizerError(f"内容哈希不一致：{left}")
            checked += 1
    total_bytes, file_count = tree_stats(source)
    return {"level": level, "bytes": total_bytes, "files": file_count, "checksummed_files": checked}


def unique_child(root: Path, label: str) -> Path:
    candidate_path = root / label
    index = 2
    while candidate_path.exists() or candidate_path.is_symlink():
        candidate_path = root / f"{label}-{index}"
        index += 1
    return candidate_path


def append_journal(root: Path, event: Dict[str, Any]) -> None:
    journal = root / ".lov-disk-optimizer-journal.jsonl"
    with journal.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def run_migrate(args: argparse.Namespace) -> int:
    source = guard_mutation_target(args.source)
    archive_root = resolved(args.archive_root)
    if not source.exists() or source.is_symlink():
        raise OptimizerError(f"源路径不存在或已经是链接：{source}")
    extra_protected = [item.expanduser() for item in getattr(args, "protected", [])]
    if protected(source, extra_protected):
        raise OptimizerError(f"迁移源命中保护边界：{source}")
    if not archive_root.is_dir():
        raise OptimizerError(f"归档根目录不存在：{archive_root}")
    destination = resolved(args.destination) if args.destination else archive_root / args.category / source.name
    if destination.exists() or destination.is_symlink():
        raise OptimizerError(f"目标已存在，先判断正式归档或不完整副本：{destination}")
    source_bytes, source_files = tree_stats(source)
    destination_ancestor = existing_ancestor(destination.parent)
    free = shutil.disk_usage(str(destination_ancestor)).free
    if free < source_bytes + int(args.reserve_gb * DECIMAL_GB):
        raise OptimizerError("归档卷剩余空间不足")
    same_device = source.stat().st_dev == destination_ancestor.stat().st_dev
    if same_device and not args.allow_same_volume:
        raise OptimizerError("源与归档目标位于同一卷，迁移不会释放该卷空间")
    plan = {
        "operation": "migrate",
        "source": str(source),
        "destination": str(destination),
        "source_bytes": source_bytes,
        "source_gb": decimal_gb(source_bytes),
        "source_files": source_files,
        "verify": args.verify,
        "create_symlink": not args.no_link,
        "execute": args.execute,
    }
    if not args.execute:
        emit(plan, args.output)
        return 0
    if args.confirm_source != str(source):
        raise OptimizerError("执行迁移时 --confirm-source 必须等于规范化源路径")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        destination.mkdir(parents=True)
        command = ["rsync", "-a", "--partial", f"{source}/", f"{destination}/"]
        if args.preserve_xattrs:
            command.insert(2, "-E")
        result = subprocess.run(command, check=False)
        if result.returncode:
            raise OptimizerError(f"复制失败，rsync exit={result.returncode}；源目录保持原状")
    else:
        shutil.copy2(str(source), str(destination))
    verification = verify_copy(source, destination, args.verify)
    rollback_root = resolved(args.rollback_root)
    rollback_root.mkdir(parents=True, exist_ok=True)
    rollback = unique_child(rollback_root, f"{source.name}.migrated")
    shutil.move(str(source), str(rollback))
    if not args.no_link:
        source.symlink_to(destination, target_is_directory=destination.is_dir())
        if not source.exists():
            raise OptimizerError(f"链接验证失败；回滚副本仍在 {rollback}")
    event = {
        **plan,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "rollback": str(rollback),
        "verification": verification,
        "status": "migrated",
    }
    append_journal(archive_root, event)
    emit(event, args.output)
    return 0


def allowed_rebuildable(path: Path) -> bool:
    if path.name in REBUILDABLE_NAMES:
        return True
    suffixes = {
        ("CoreSimulator", "Devices"),
        ("Xcode", "iOS DeviceSupport"),
    }
    return any(tuple(path.parts[-len(suffix):]) == suffix for suffix in suffixes)


def run_stage_cleanup(args: argparse.Namespace) -> int:
    paths = [guard_mutation_target(item) for item in args.path]
    extra_protected = [item.expanduser() for item in args.protected]
    actions: List[Dict[str, Any]] = []
    for path in paths:
        if not path.exists() or path.is_symlink():
            raise OptimizerError(f"清理候选不存在或是链接：{path}")
        if protected(path, extra_protected):
            raise OptimizerError(f"候选命中保护边界：{path}")
        if not allowed_rebuildable(path):
            raise OptimizerError(f"候选名称不在可重建白名单：{path}")
        size, files = tree_stats(path)
        actions.append({"path": str(path), "bytes": size, "gb": decimal_gb(size), "files": files})
    payload: Dict[str, Any] = {
        "operation": "stage-cleanup",
        "execute": args.execute,
        "estimated_gb": decimal_gb(sum(item["bytes"] for item in actions)),
        "items": actions,
        "note": "该操作只把明确的可重建目录移入回滚区，不清空废纸篓。",
    }
    if not args.execute:
        emit(payload, args.output)
        return 0
    if args.confirm != "STAGE_REBUILDABLES":
        raise OptimizerError("执行清理时必须传入 --confirm STAGE_REBUILDABLES")
    rollback_root = resolved(args.rollback_root)
    rollback_root.mkdir(parents=True, exist_ok=True)
    moved_records: List[Tuple[Dict[str, Any], Path, Path]] = []
    try:
        for item, path in zip(actions, paths):
            rollback = unique_child(rollback_root, f"{path.parent.name}-{path.name}.cleanup")
            shutil.move(str(path), str(rollback))
            moved_records.append((item, path, rollback))
            if args.recreate:
                path.mkdir(parents=True, exist_ok=True)
    except (OSError, shutil.Error) as exc:
        rollback_errors: List[Dict[str, str]] = []
        for item, path, rollback in reversed(moved_records):
            try:
                if args.recreate and path.exists() and path.is_dir() and not path.is_symlink():
                    if any(path.iterdir()):
                        raise OSError("重建路径在回滚前已有新内容")
                    path.rmdir()
                shutil.move(str(rollback), str(path))
            except (OSError, shutil.Error) as rollback_exc:
                rollback_errors.append(
                    {
                        "path": str(path),
                        "rollback": str(rollback),
                        "error": str(rollback_exc),
                    }
                )
        payload["status"] = "rolled-back" if not rollback_errors else "partial-failure"
        payload["items"] = [
            {
                **item,
                "status": "rolled-back" if any(record[0] is item for record in moved_records) else "not-started",
            }
            for item in actions
        ]
        payload["error"] = str(exc)
        payload["rollback_errors"] = rollback_errors
        emit(payload, args.output)
        return 2
    moved = [{**item, "rollback": str(rollback), "status": "staged"} for item, _path, rollback in moved_records]
    payload["items"] = moved
    payload["status"] = "staged"
    emit(payload, args.output)
    return 0


def staged_path(path: Path, rollback_root: Path) -> Path:
    """Accept only an explicit top-level cleanup entry under the rollback root."""
    root = lexical(rollback_root)
    candidate = lexical(path if path.is_absolute() else root / path)
    canonical_root = root.resolve(strict=False)
    canonical_candidate = candidate.resolve(strict=False)
    if canonical_candidate.parent != canonical_root:
        raise OptimizerError(f"回滚清理目标必须是回滚根目录的直接子项：{candidate}")
    if not candidate.name.endswith(".cleanup"):
        raise OptimizerError(f"回滚清理目标必须以 .cleanup 结尾：{candidate}")
    if candidate.is_symlink():
        raise OptimizerError(f"回滚清理目标不能是符号链接：{candidate}")
    return candidate


def staged_entry(path: Path) -> Dict[str, Any]:
    exists = path.exists() and not path.is_symlink()
    size, files = tree_stats(path) if exists else (0, 0)
    return {
        "path": str(path),
        "bytes": size,
        "gb": decimal_gb(size),
        "files": files,
        "status": "pending" if exists else "already-absent",
    }


def run_list_staged(args: argparse.Namespace) -> int:
    rollback_root = resolved(args.rollback_root)
    if not rollback_root.is_dir():
        raise OptimizerError(f"回滚根目录不存在：{rollback_root}")
    items = [
        staged_entry(child)
        for child in sorted(rollback_root.iterdir(), key=lambda item: item.name.lower())
        if child.name.endswith(".cleanup") and not child.is_symlink()
    ]
    emit(
        {
            "operation": "list-staged",
            "rollback_root": str(rollback_root),
            "items": items,
            "total_bytes": sum(int(item["bytes"]) for item in items),
            "total_gb": decimal_gb(sum(int(item["bytes"]) for item in items)),
        },
        args.output,
    )
    return 0


def run_purge_staged(args: argparse.Namespace) -> int:
    rollback_root = resolved(args.rollback_root)
    if not rollback_root.is_dir():
        raise OptimizerError(f"回滚根目录不存在：{rollback_root}")
    paths: List[Path] = []
    seen = set()
    for raw_path in args.path:
        candidate_path = staged_path(raw_path, rollback_root)
        if str(candidate_path) in seen:
            raise OptimizerError(f"回滚清理目标重复：{candidate_path}")
        seen.add(str(candidate_path))
        paths.append(candidate_path)

    items = [staged_entry(path) for path in paths]
    payload: Dict[str, Any] = {
        "operation": "purge-staged",
        "execute": args.execute,
        "method": "direct-filesystem",
        "finder": False,
        "retry": False,
        "rollback_root": str(rollback_root),
        "items": items,
        "estimated_gb": decimal_gb(sum(int(item["bytes"]) for item in items)),
        "note": "只处理显式 .cleanup 路径；不会清空其他废纸篓项目。",
    }
    if not args.execute:
        emit(payload, args.output)
        return 0
    if args.confirm != PURGE_CONFIRM:
        raise OptimizerError(f"执行回滚区清理时必须传入 --confirm {PURGE_CONFIRM}")

    errors: List[Dict[str, str]] = []
    for item, path in zip(items, paths):
        if not path.exists():
            item["status"] = "already-absent"
            continue
        try:
            if path.is_dir():
                shutil.rmtree(str(path))
            else:
                path.unlink()
            if path.exists() or path.is_symlink():
                raise OSError("删除后路径仍存在")
            item["status"] = "purged"
        except OSError as exc:
            item["status"] = "error"
            errors.append({"path": str(path), "error": str(exc)})
            break

    payload["status"] = "purged" if not errors else "partial-failure"
    payload["errors"] = errors
    emit(payload, args.output)
    return 0 if not errors else 2


def run_verify(args: argparse.Namespace) -> int:
    volume = resolved(args.volume)
    usage = shutil.disk_usage(str(volume))
    required = int((args.target_free_gb + args.buffer_gb) * DECIMAL_GB)
    link_results = []
    for path in args.link:
        item = path.expanduser()
        link_results.append({
            "path": str(item),
            "is_symlink": item.is_symlink(),
            "resolves": item.exists(),
            "target": os.readlink(str(item)) if item.is_symlink() else None,
        })
    passed = usage.free >= required and all(item["is_symlink"] and item["resolves"] for item in link_results)
    emit(
        {
            "passed": passed,
            "volume": str(volume),
            "free_bytes": usage.free,
            "free_gb": decimal_gb(usage.free),
            "target_free_gb": args.target_free_gb,
            "buffer_gb": args.buffer_gb,
            "required_gb": args.target_free_gb + args.buffer_gb,
            "links": link_results,
        },
        args.output,
    )
    return 0 if passed else 3


def read_profile(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise OptimizerError("共享 profile 根节点必须是对象")
    return data


def run_profile(args: argparse.Namespace) -> int:
    path = resolved(args.profile)
    data = read_profile(path)
    skills = data.get("skills", {})
    if not isinstance(skills, dict):
        raise OptimizerError("profile.skills 必须是对象")
    current = skills.get(PROFILE_KEY, {})
    if not isinstance(current, dict):
        current = {}
    if args.profile_action == "show":
        emit({"profile": str(path), "settings": current}, args.output)
        return 0
    settings = {
        "target_free_gb": args.target_free_gb,
        "buffer_gb": args.buffer_gb,
        "archive_volume": str(args.archive_volume.expanduser()) if args.archive_volume else None,
        "protected_paths": [str(item.expanduser()) for item in args.protected],
        "cleanup_policy": args.cleanup_policy,
    }
    emit({"profile": str(path), "settings_to_persist": settings}, None)
    if not args.write:
        return 0
    skills[PROFILE_KEY] = settings
    data["skills"] = skills
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    emit({"profile": str(path), "status": "saved", "settings": settings}, args.output)
    return 0


def add_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", type=Path, help="可选 JSON 输出文件；默认输出到 stdout")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status", help="读取数据卷真实可用空间")
    status.add_argument("--volume", type=Path, default=DEFAULT_DATA_VOLUME)
    add_output(status)
    status.set_defaults(func=run_status)

    inventory = commands.add_parser("inventory", help="只读扫描大目录和可重建产物")
    inventory.add_argument("--root", type=Path, action="append", required=True)
    inventory.add_argument("--volume", type=Path, default=DEFAULT_DATA_VOLUME)
    inventory.add_argument("--protected", type=Path, action="append", default=[])
    inventory.add_argument("--min-gb", type=float, default=0.5)
    inventory.add_argument("--include-hidden", action="store_true")
    inventory.add_argument("--no-artifacts", action="store_true")
    add_output(inventory)
    inventory.set_defaults(func=run_inventory)

    plan = commands.add_parser("plan", help="按容量缺口生成最小清理与归档建议")
    plan.add_argument("--inventory", type=Path, required=True)
    plan.add_argument("--target-free-gb", type=float, required=True)
    plan.add_argument("--buffer-gb", type=float, default=15.0)
    add_output(plan)
    plan.set_defaults(func=run_plan)

    preflight = commands.add_parser("preflight-volume", help="检查归档卷容量与可写性")
    preflight.add_argument("--archive-root", type=Path, required=True)
    preflight.add_argument("--required-gb", type=float, required=True)
    add_output(preflight)
    preflight.set_defaults(func=run_preflight)

    migrate = commands.add_parser("migrate", help="事务式复制、校验、回滚与原路径链接")
    migrate.add_argument("--source", type=Path, required=True)
    migrate.add_argument("--archive-root", type=Path, required=True)
    migrate.add_argument("--category", default="projects")
    migrate.add_argument("--destination", type=Path)
    migrate.add_argument("--protected", type=Path, action="append", default=[])
    migrate.add_argument("--rollback-root", type=Path, default=Path.home() / ".Trash")
    migrate.add_argument("--verify", choices=("metadata", "checksum"), default="metadata")
    migrate.add_argument("--reserve-gb", type=float, default=10.0)
    migrate.add_argument("--preserve-xattrs", action="store_true")
    migrate.add_argument("--no-link", action="store_true")
    migrate.add_argument("--allow-same-volume", action="store_true", help=argparse.SUPPRESS)
    migrate.add_argument("--execute", action="store_true")
    migrate.add_argument("--confirm-source", default="")
    add_output(migrate)
    migrate.set_defaults(func=run_migrate)

    cleanup = commands.add_parser("stage-cleanup", help="把白名单内可重建目录移入回滚区")
    cleanup.add_argument("--path", type=Path, action="append", required=True)
    cleanup.add_argument("--protected", type=Path, action="append", default=[])
    cleanup.add_argument("--rollback-root", type=Path, default=Path.home() / ".Trash")
    cleanup.add_argument("--recreate", action="store_true")
    cleanup.add_argument("--execute", action="store_true")
    cleanup.add_argument("--confirm", default="")
    add_output(cleanup)
    cleanup.set_defaults(func=run_stage_cleanup)

    staged = commands.add_parser("list-staged", help="列出回滚区内本轮生成的清理项")
    staged.add_argument("--rollback-root", type=Path, default=Path.home() / ".Trash")
    add_output(staged)
    staged.set_defaults(func=run_list_staged)

    purge = commands.add_parser("purge-staged", help="直接回收显式 .cleanup 项，不调用 Finder")
    purge.add_argument("--path", type=Path, action="append", required=True)
    purge.add_argument("--rollback-root", type=Path, default=Path.home() / ".Trash")
    purge.add_argument("--execute", action="store_true")
    purge.add_argument("--confirm", default="")
    add_output(purge)
    purge.set_defaults(func=run_purge_staged)

    verify = commands.add_parser("verify", help="按十进制 GB 与链接状态完成真实验收")
    verify.add_argument("--volume", type=Path, default=DEFAULT_DATA_VOLUME)
    verify.add_argument("--target-free-gb", type=float, required=True)
    verify.add_argument("--buffer-gb", type=float, default=15.0)
    verify.add_argument("--link", type=Path, action="append", default=[])
    add_output(verify)
    verify.set_defaults(func=run_verify)

    profile = commands.add_parser("profile", help="查看或初始化可移植默认配置")
    profile.add_argument("profile_action", choices=("show", "init"))
    profile.add_argument(
        "--profile",
        "--preferences",
        dest="profile",
        type=Path,
        default=DEFAULT_PROFILE,
    )
    profile.add_argument("--target-free-gb", type=float, default=200.0)
    profile.add_argument("--buffer-gb", type=float, default=15.0)
    profile.add_argument("--archive-volume", type=Path)
    profile.add_argument("--protected", type=Path, action="append", default=[])
    profile.add_argument("--cleanup-policy", choices=("conservative", "balanced", "aggressive"), default="balanced")
    profile.add_argument("--write", action="store_true")
    add_output(profile)
    profile.set_defaults(func=run_profile)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OptimizerError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
