#!/usr/bin/env python3
"""Align Codex thread provider metadata with the current config.toml.

Codex Desktop stores the model provider used by each thread in
``state_*.sqlite`` (``threads.model_provider``). When CC Switch or another
provider manager replaces the active provider in ``config.toml``, older
threads may still point at a provider name whose ``[model_providers.<name>]``
block no longer exists. Opening those threads fails with:

    ChatGPT can't load config.toml, so this thread can't resume.
    Fix config.toml: Model provider `<name>` not found.

This script repairs the SQLite index only. It deliberately does not rewrite
rollout JSONL files: paginated histories store byte offsets that would become
invalid if the file length changes.

The default is a read-only dry run. Use ``--apply`` to write, after backing up
``state_*.sqlite`` with SQLite's consistent backup API.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


STATE_RE = re.compile(r"^state_\d+\.sqlite$")
ROOT_SCALAR_RE = re.compile(
    r"^([A-Za-z0-9_.-]+)\s*=\s*"
    r"(?:\"([^\"]*)\"|'([^']*)'|([^\s#]+))"
)
PROVIDER_SECTION_RE = re.compile(r"^\[\s*model_providers\.([A-Za-z0-9_.-]+)\s*\]\s*$")
BUILTIN_PROVIDERS = {"openai", "chatgpt"}

try:  # Python 3.11+ has the real parser; the regex fallback keeps 3.8 usable.
    import tomllib  # type: ignore
except ImportError:  # pragma: no cover - fallback only
    tomllib = None  # type: ignore


def _read_plain_scalars(text: str) -> Dict[str, str]:
    """Read simple root-level ``key = "value"`` scalars without tomllib."""
    values: Dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = ROOT_SCALAR_RE.match(line)
        if not match:
            continue
        key = match.group(1)
        value = (
            match.group(2)
            if match.group(2) is not None
            else match.group(3)
            if match.group(3) is not None
            else match.group(4)
        )
        values[key] = value.strip()
    return values


def read_config(config_path: Path) -> Tuple[str, Optional[str], List[str]]:
    """Return current provider, model, and configured provider names."""
    text = config_path.read_text(encoding="utf-8")
    data: Optional[Dict[str, Any]] = None
    if tomllib is not None:
        try:
            data = tomllib.loads(text)
        except Exception:
            data = None
    if data is None:
        scalars = _read_plain_scalars(text)
        scalar_provider = scalars.get("model_provider")
        scalar_model = scalars.get("model")
        provider_names = [
            match.group(1)
            for match in (
                PROVIDER_SECTION_RE.match(line.strip())
                for line in text.splitlines()
            )
            if match
        ]
    else:
        scalar_provider = data.get("model_provider")
        scalar_model = data.get("model")
        provider_names = [
            str(name)
            for name in (data.get("model_providers") or {}).keys()
            if name
        ]

    provider = str(scalar_provider).strip() if scalar_provider is not None else ""
    model = str(scalar_model).strip() if scalar_model is not None else None
    return provider, (model or None), sorted(set(provider_names))


def discover_state_db(codex_home: Path, explicit: Optional[Path]) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    candidates = sorted(
        (
            path
            for path in codex_home.glob("state_*.sqlite")
            if path.is_file() and STATE_RE.match(path.name)
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"no state_*.sqlite found under {codex_home}; pass --state-db explicitly"
        )
    return candidates[0]


def check_threads_table(conn: sqlite3.Connection, db_path: Path) -> None:
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(threads)").fetchall()
    }
    if "model_provider" not in columns:
        raise RuntimeError(
            f"{db_path}: threads table has no model_provider column; "
            "this Codex schema may need a different repair path"
        )


def provider_distribution(
    conn: sqlite3.Connection,
) -> List[Dict[str, Any]]:
    return [
        {
            "provider": row[0] if row[0] is not None else "",
            "threads": row[1],
            "archived": row[2],
        }
        for row in conn.execute(
            "SELECT model_provider, COUNT(*) AS thread_count, "
            "COALESCE(SUM(archived), 0) AS archived_count "
            "FROM threads GROUP BY model_provider ORDER BY thread_count DESC"
        ).fetchall()
    ]


def candidate_ids(
    conn: sqlite3.Connection,
    target_provider: str,
    configured: Sequence[str],
    source_providers: Sequence[str],
    all_threads: bool,
) -> Tuple[List[str], str]:
    """Return thread ids to align, plus a short human-readable mode."""
    if all_threads:
        rows = conn.execute(
            "SELECT id FROM threads WHERE model_provider IS NOT ?",
            (target_provider,),
        ).fetchall()
        return [str(row[0]) for row in rows], "all-threads"

    if source_providers:
        placeholders = ",".join("?" for _ in source_providers)
        rows = conn.execute(
            f"SELECT id FROM threads WHERE model_provider IN ({placeholders})",
            tuple(source_providers),
        ).fetchall()
        return [str(row[0]) for row in rows], "source-filter"

    available = set(configured) | BUILTIN_PROVIDERS | {target_provider}
    rows = conn.execute(
        "SELECT id, model_provider FROM threads"
    ).fetchall()
    stale_ids = [
        str(row[0])
        for row in rows
        if row[1] is None or str(row[1]) == "" or str(row[1]) not in available
    ]
    if not stale_ids:
        return [], "stale-only (nothing stale)"
    return stale_ids, "stale-only"


def backup_database(source: sqlite3.Connection, db_path: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = db_path.with_name(f"{db_path.name}.bak-{stamp}")
    destination = sqlite3.connect(str(backup_path))
    try:
        source.backup(destination)
    finally:
        destination.close()
    return backup_path


def apply_ids(
    conn: sqlite3.Connection, ids: Sequence[str], target_provider: str
) -> int:
    if not ids:
        return 0
    conn.execute("BEGIN IMMEDIATE")
    try:
        total = 0
        for start in range(0, len(ids), 500):
            batch = ids[start : start + 500]
            placeholders = ",".join("?" for _ in batch)
            cursor = conn.execute(
                f"UPDATE threads SET model_provider = ? "
                f"WHERE id IN ({placeholders})",
                (target_provider, *batch),
            )
            total += int(cursor.rowcount)
        conn.commit()
        return total
    except Exception:
        conn.rollback()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Align Codex thread provider metadata with config.toml "
        "(read-only by default; never rewrites rollout JSONL)"
    )
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
        help="Codex home directory. Default: ~/.codex",
    )
    parser.add_argument("--config", type=Path, help="config.toml path")
    parser.add_argument(
        "--state-db", type=Path, help="state_*.sqlite path (default: newest under --codex-home)"
    )
    parser.add_argument(
        "--provider",
        help="target provider name (default: current model_provider in config.toml)",
    )
    parser.add_argument(
        "--source-provider",
        action="append",
        default=[],
        help="only migrate threads with this stored provider; repeatable",
    )
    parser.add_argument(
        "--all-threads",
        action="store_true",
        help="migrate every thread, including built-in providers like openai",
    )
    parser.add_argument(
        "--apply", action="store_true", help="write the change (default is dry run)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="apply even when SQLite -wal/-shm sidecars indicate Codex may be running",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    codex_home = Path(args.codex_home).expanduser()
    config_path = (args.config or codex_home / "config.toml").expanduser()
    try:
        state_db = discover_state_db(codex_home, args.state_db)
        current_provider, current_model, configured = read_config(config_path)
        target_provider = (args.provider or current_provider).strip()
        if not target_provider:
            raise ValueError(
                f"{config_path}: cannot read root model_provider; pass --provider explicitly"
            )
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", target_provider):
            raise ValueError(f"invalid provider name: {target_provider!r}")

        available = set(configured) | BUILTIN_PROVIDERS
        if target_provider not in available:
            raise ValueError(
                f"{config_path}: target provider {target_provider!r} is not declared "
                f"(configured: {sorted(configured)}); refusing to write a broken pointer"
            )
        if not state_db.is_file():
            raise FileNotFoundError(f"state database does not exist: {state_db}")

        conn = sqlite3.connect(str(state_db), timeout=5)
        try:
            check_threads_table(conn, state_db)
            before = provider_distribution(conn)
            ids, mode = candidate_ids(
                conn,
                target_provider,
                configured,
                args.source_provider,
                args.all_threads,
            )

            sidecars = [
                str(path)
                for path in (
                    state_db.with_name(state_db.name + "-wal"),
                    state_db.with_name(state_db.name + "-shm"),
                )
                if path.exists()
            ]
            warnings: List[str] = []
            if sidecars:
                warnings.append(
                    "SQLite sidecar files exist; Codex Desktop may be running. "
                    "Quit it before --apply unless you know the thread is idle."
                )
            if not args.all_threads and args.source_provider:
                if any(
                    source not in {row["provider"] for row in before}
                    for source in args.source_provider
                ):
                    warnings.append("one or more --source-provider values matched no threads")

            backup_path: Optional[str] = None
            changed = 0
            if args.apply:
                if sidecars and not args.force:
                    raise RuntimeError(
                        "refusing to write while SQLite sidecars exist; "
                        "quit Codex Desktop or pass --force"
                    )
                backup_path = str(backup_database(conn, state_db))
                changed = apply_ids(conn, ids, target_provider)

            result: Dict[str, Any] = {
                "status": "dry-run" if not args.apply else "applied",
                "codex_home": str(codex_home),
                "config_path": str(config_path),
                "state_db": str(state_db),
                "current_provider": current_provider,
                "current_model": current_model,
                "target_provider": target_provider,
                "configured_providers": configured,
                "migration_mode": mode,
                "threads_before": before,
                "candidate_count": len(ids),
                "candidate_ids": ids,
                "changed": changed,
                "backup_path": backup_path,
                "warnings": warnings,
            }
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0

            print(f"config:    {config_path}")
            print(f"state db:  {state_db}")
            print(f"provider:  {current_provider!r} -> {target_provider!r}")
            print(f"mode:      {mode}")
            for row in before:
                print(
                    f"  before:  provider={row['provider']!r} "
                    f"threads={row['threads']} archived={row['archived']}"
                )
            print(f"candidates: {len(ids)}")
            if ids:
                shown = ", ".join(ids[:8]) + ("…" if len(ids) > 8 else "")
                print(f"  ids:       {shown}")
            print(
                f"changed:   {changed}"
                if args.apply
                else "changed:   (dry run; rerun with --apply)"
            )
            if backup_path:
                print(f"backup:    {backup_path}")
            for warning in warnings:
                print(f"warning:   {warning}")
            return 0
        finally:
            conn.close()
    except (FileNotFoundError, RuntimeError, ValueError, sqlite3.Error) as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
