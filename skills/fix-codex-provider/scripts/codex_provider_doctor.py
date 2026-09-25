#!/usr/bin/env python3
"""Diagnose and repair Codex provider mismatches that block opening threads.

Codex persists one model provider id per thread. Launch paths disagree about
which providers exist: the desktop app and a plain CLI read the user's
config.toml, while an editor integration can inject provider flags at launch.
A thread whose persisted provider is missing from the active configuration
fails to open with a message such as:

    can't load config.toml, so this thread can't resume.
    Fix config.toml: Model provider `yoda` not found.

This tool is read-only by default. Two write modes exist and both create
backups first:

    --fix-retag TARGET   retag threads whose provider is unavailable
    --restore BACKUP_DIR restore a previous repair from its backup

No network access and no credential values are read or printed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.8-3.10
    tomllib = None


BUILTIN_PROVIDERS = ("openai", "ollama", "lmstudio")
# Provider ids used as long-lived history buckets by integrations. They keep
# their id while the underlying route changes, so a missing definition is
# usually repaired by defining the provider, not by retagging history.
SHARED_BUCKET_PROVIDERS = ("yoda", "custom")
PROVIDER_NOT_FOUND_RE = re.compile(r"Model provider `([^`]+)` not found")
BACKUP_DIRNAME = "provider-repair-backups"
STATE_DB = "state_5.sqlite"
LOGS_DB = "logs_2.sqlite"
DESKTOP_LOG_ROOT = ("Library", "Logs", "com.openai.codex")
ISO_TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")


def resolve_codex_home(value):
    if value:
        return Path(value).expanduser()
    env_home = os.environ.get("CODEX_HOME")
    return Path(env_home).expanduser() if env_home else Path.home() / ".codex"


def abbrev(path):
    text = str(path)
    home = str(Path.home())
    return text.replace(home, "~", 1) if text.startswith(home) else text


def read_text(path):
    return path.read_text(encoding="utf-8")


def connect_readonly(path):
    """Open a SQLite database without writing to it.

    A WAL database whose -shm file is absent (a cold copy, for example) cannot
    be opened with mode=ro, so the fallback opens the existing file read-write
    while the caller only executes SELECT statements.
    """
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        con.execute("SELECT 1").fetchone()
        return con
    except sqlite3.Error:
        pass
    return sqlite3.connect(f"file:{path}?mode=rw", uri=True)


def _parse_scalar(raw):
    raw = raw.strip()
    if raw.startswith(('"', "'")):
        quote = raw[0]
        end = raw.find(quote, 1)
        return raw[1:end] if end > 0 else raw.strip(quote)
    if raw in ("true", "false"):
        return raw == "true"
    if raw.startswith("[") and raw.endswith("]"):
        items = []
        for chunk in raw[1:-1].split(","):
            chunk = chunk.strip()
            if chunk:
                items.append(_parse_scalar(chunk))
        return items
    return raw


def parse_toml_lite(text):
    """Read the scalar keys Codex provider configuration uses.

    Only used when the running interpreter has no tomllib. Nested tables are
    returned as nested dicts; arrays and inline tables are kept as raw text.
    """
    tree = {}
    section_path = []
    key_re = re.compile(r'^([A-Za-z0-9_\-."]+)\s*=\s*(.+)$')
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            inner = line[1:-1].strip()
            parts = [part.strip().strip('"') for part in inner.split(".") if part.strip()]
            section_path = parts
            continue
        match = key_re.match(line)
        if not match:
            continue
        key = match.group(1).strip().strip('"')
        value = _parse_scalar(match.group(2))
        node = tree
        for part in section_path:
            node = node.setdefault(part, {})
        node[key] = value
    return tree


def load_config(codex_home):
    path = codex_home / "config.toml"
    info = {
        "path": path,
        "exists": path.is_file(),
        "parse_mode": None,
        "model_provider": None,
        "providers": {},
    }
    if not info["exists"]:
        return info
    text = read_text(path)
    data = None
    if tomllib is not None:
        try:
            data = tomllib.loads(text)
            info["parse_mode"] = "tomllib"
        except Exception:
            data = None
    if data is None:
        data = parse_toml_lite(text)
        info["parse_mode"] = "lite"
    provider = data.get("model_provider")
    if isinstance(provider, str):
        info["model_provider"] = provider
    blocks = data.get("model_providers")
    if isinstance(blocks, dict):
        for provider_id, block in blocks.items():
            if not isinstance(block, dict):
                continue
            info["providers"][str(provider_id)] = {
                "name": str(block.get("name") or ""),
                "base_url": str(block.get("base_url") or ""),
                "wire_api": str(block.get("wire_api") or ""),
                "env_key": str(block.get("env_key") or ""),
                "requires_openai_auth": bool(block.get("requires_openai_auth") or False),
                "has_inline_token": bool(
                    block.get("experimental_bearer_token") or block.get("api_key")
                ),
            }
    return info


def load_threads(db_path):
    if not db_path.is_file():
        return None
    try:
        con = connect_readonly(db_path)
    except sqlite3.Error:
        return None
    try:
        columns = {row[1] for row in con.execute("PRAGMA table_info(threads)")}
        if "model_provider" not in columns:
            return None
        archived_expr = (
            "SUM(CASE WHEN archived = 1 THEN 1 ELSE 0 END)"
            if "archived" in columns
            else "0"
        )
        created_expr = "MIN(created_at)" if "created_at" in columns else "NULL"
        updated_expr = "MAX(COALESCE(updated_at, created_at))" if "created_at" in columns else "NULL"
        sql = (
            "SELECT model_provider, COUNT(*), "
            "SUM(CASE WHEN COALESCE(archived, 0) = 1 THEN 0 ELSE 1 END), "
            f"{archived_expr}, {created_expr}, {updated_expr} "
            "FROM threads GROUP BY model_provider ORDER BY COUNT(*) DESC"
        )
        stats = {}
        for provider, total, active, archived, first_seen, last_seen in con.execute(sql):
            stats[str(provider)] = {
                "total": int(total),
                "active": int(active or 0),
                "archived": int(archived or 0),
                "first_seen": first_seen,
                "last_seen": last_seen,
            }
        return stats
    except sqlite3.DatabaseError:
        return None
    finally:
        con.close()


def affected_threads(db_path, providers, active_only=False):
    """Return rows of threads whose provider is in the given set."""
    providers = [p for p in providers if p]
    if not providers:
        return []
    try:
        con = connect_readonly(db_path)
    except sqlite3.Error:
        return []
    try:
        columns = {row[1] for row in con.execute("PRAGMA table_info(threads)")}
        wanted = ["id", "model_provider", "rollout_path"]
        select = [c for c in wanted if c in columns]
        where = "model_provider IN (%s)" % ",".join("?" for _ in providers)
        if active_only and "archived" in columns:
            where += " AND COALESCE(archived, 0) = 0"
        rows = con.execute(
            f"SELECT {', '.join(select)} FROM threads WHERE {where}", providers
        ).fetchall()
        return [dict(zip(select, row)) for row in rows]
    except sqlite3.DatabaseError:
        return []
    finally:
        con.close()


def scan_logs(db_path, days):
    if not db_path.is_file():
        return {}
    cutoff = time.time() - days * 86400
    try:
        con = connect_readonly(db_path)
    except sqlite3.Error:
        return {}
    try:
        rows = con.execute(
            "SELECT ts, feedback_log_body FROM logs "
            "WHERE ts > ? AND level IN ('WARN', 'ERROR') "
            "AND feedback_log_body LIKE '%failed to load configuration%' "
            "AND feedback_log_body LIKE '%not found%'",
            (cutoff,),
        ).fetchall()
    except sqlite3.DatabaseError:
        return {}
    finally:
        con.close()
    evidence = {}
    for ts, body in rows:
        match = PROVIDER_NOT_FOUND_RE.search(body or "")
        if not match:
            continue
        provider = match.group(1)
        entry = evidence.setdefault(provider, {"count": 0, "first": ts, "last": ts})
        entry["count"] += 1
        entry["first"] = min(entry["first"], ts)
        entry["last"] = max(entry["last"], ts)
    return evidence


def default_desktop_log_root():
    root = Path.home().joinpath(*DESKTOP_LOG_ROOT)
    return root if root.is_dir() else None


def scan_desktop_logs(root, days):
    """Count resume failures in the desktop app's own log files."""
    if root is None or not root.is_dir():
        return {}
    cutoff = time.time() - days * 86400
    evidence = {}
    for path in sorted(root.rglob("*.log")):
        try:
            if path.stat().st_mtime < cutoff:
                continue
            handle = path.open("r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                match = PROVIDER_NOT_FOUND_RE.search(line)
                if not match:
                    continue
                provider = match.group(1)
                entry = evidence.setdefault(
                    provider, {"count": 0, "resume_failures": 0, "files": 0, "last": None}
                )
                entry["count"] += 1
                if "Failed to resume conversation" in line:
                    entry["resume_failures"] += 1
                stamp = ISO_TS_RE.search(line)
                if stamp:
                    entry["last"] = stamp.group(1)
                entry.setdefault("_files", set()).add(str(path))
    for entry in evidence.values():
        entry["files"] = len(entry.pop("_files", ()))
    return evidence


def rollout_provider(path):
    """Return (provider, error) from a rollout file's first JSONL record."""
    try:
        with open(path, "rb") as handle:
            first = handle.readline()
        meta = json.loads(first.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    payload = meta.get("payload")
    if not isinstance(payload, dict):
        return None, "first record has no payload object"
    provider = payload.get("model_provider")
    return (str(provider) if provider is not None else None), None


def rollout_parity(db_path, providers, sample):
    """Compare sampled rollout session metadata with the thread index."""
    rows = affected_threads(db_path, providers)
    checked = []
    mismatches = []
    for row in rows[: max(0, sample)]:
        path = row.get("rollout_path")
        if not path:
            continue
        provider, error = rollout_provider(Path(path).expanduser())
        record = {
            "thread_id": row.get("id"),
            "index_provider": row.get("model_provider"),
            "rollout_provider": provider,
            "rollout_path": path,
            "error": error,
        }
        checked.append(record)
        if error or provider != row.get("model_provider"):
            mismatches.append(record)
    return {"checked": len(checked), "mismatches": mismatches}


def format_ts(value):
    if not value:
        return "unknown"
    try:
        return dt.datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return "unknown"


def build_report(codex_home, log_days, sample, desktop_log_root=None):
    config = load_config(codex_home)
    state_path = codex_home / STATE_DB
    threads = load_threads(state_path)
    logs = scan_logs(codex_home / LOGS_DB, log_days)
    if desktop_log_root is None:
        desktop_log_root = default_desktop_log_root()
    desktop_logs = scan_desktop_logs(desktop_log_root, log_days)
    available = set(config["providers"]) | set(BUILTIN_PROVIDERS)
    active_provider = config["model_provider"]
    findings = []

    if not config["exists"]:
        findings.append(
            {
                "severity": "error",
                "code": "config_missing",
                "message": f"config.toml not found at {abbrev(config['path'])}",
            }
        )
    if active_provider and active_provider not in available:
        findings.append(
            {
                "severity": "error",
                "code": "active_provider_undefined",
                "message": (
                    f"config.toml selects model_provider = {active_provider!r} "
                    "but does not define it; Codex fails at startup"
                ),
            }
        )
    unavailable = {
        provider: stats
        for provider, stats in (threads or {}).items()
        if provider not in available
    }
    if unavailable:
        total = sum(stats["total"] for stats in unavailable.values())
        findings.append(
            {
                "severity": "error",
                "code": "history_provider_missing",
                "message": (
                    f"{total} thread(s) reference providers missing from this "
                    "configuration; opening them fails with Model provider not found"
                ),
            }
        )
    for provider, entry in logs.items():
        severity = "warn" if provider in available else "error"
        findings.append(
            {
                "severity": severity,
                "code": "log_provider_not_found",
                "message": (
                    f"logs show Model provider `{provider}` not found "
                    f"{entry['count']} time(s), {format_ts(entry['first'])} "
                    f"to {format_ts(entry['last'])}"
                ),
            }
        )
    for provider, entry in desktop_logs.items():
        resolved = provider in available
        findings.append(
            {
                "severity": "info" if resolved else "error",
                "code": "desktop_resume_failed",
                "message": (
                    f"desktop app logged {entry['resume_failures']} resume failure(s) "
                    f"with Model provider `{provider}` not found "
                    f"({entry['count']} log hit(s) in {entry['files']} file(s), "
                    f"last {entry['last']})"
                    + (
                        "; the current configuration defines this provider, so "
                        "restart the desktop app to pick it up"
                        if resolved
                        else ""
                    )
                ),
            }
        )
    for provider, block in config["providers"].items():
        if block["wire_api"] and block["wire_api"] != "responses":
            findings.append(
                {
                    "severity": "warn",
                    "code": "unsupported_wire_api",
                    "message": (
                        f"model_providers.{provider} uses wire_api = "
                        f"{block['wire_api']!r}; current Codex releases accept "
                        "responses here"
                    ),
                }
            )
        if block["env_key"] and not os.environ.get(block["env_key"]):
            findings.append(
                {
                    "severity": "info",
                    "code": "env_key_missing_in_shell",
                    "message": (
                        f"model_providers.{provider} reads {block['env_key']} from "
                        "its launch environment; GUI-launched apps may not see it"
                    ),
                }
            )
        if block["requires_openai_auth"] and not (codex_home / "auth.json").is_file():
            findings.append(
                {
                    "severity": "error",
                    "code": "auth_missing",
                    "message": (
                        f"model_providers.{provider} requires OpenAI auth but "
                        "auth.json is absent"
                    ),
                }
            )
    parity = rollout_parity(state_path, list(unavailable), sample) if unavailable else {
        "checked": 0,
        "mismatches": [],
    }
    for provider, stats in unavailable.items():
        if provider in SHARED_BUCKET_PROVIDERS:
            strategy = "define_provider"
        else:
            strategy = "retag_threads"
        stats["suggested_strategy"] = strategy
    return {
        "codex_home": abbrev(codex_home),
        "config": {
            "path": abbrev(config["path"]),
            "exists": config["exists"],
            "parse_mode": config["parse_mode"],
            "model_provider": active_provider,
            "providers": config["providers"],
        },
        "builtin_providers": list(BUILTIN_PROVIDERS),
        "threads": threads,
        "unavailable_history": unavailable,
        "log_evidence": logs,
        "desktop_log_evidence": desktop_logs,
        "rollout_parity": parity,
        "findings": findings,
        "available_providers": sorted(available),
    }


def print_human(report):
    config = report["config"]
    print("Codex provider doctor")
    print(f"  codex home      : {report['codex_home']}")
    print(f"  config.toml     : {config['path']}")
    print(f"  parse mode      : {config['parse_mode'] or 'n/a'}")
    print(f"  active provider : {config['model_provider'] or 'unset'}")
    defined = ", ".join(sorted(config["providers"])) or "none"
    print(f"  defined         : {defined}")
    print(f"  built-in        : {', '.join(report['builtin_providers'])}")
    threads = report["threads"]
    if threads:
        print("\nThread index by persisted provider")
        width = max(len(provider) for provider in threads)
        for provider, stats in threads.items():
            known = provider in report["available_providers"]
            mark = "ok " if known else "MISSING"
            print(
                f"  [{mark}] {provider:<{width}} total={stats['total']:<6} "
                f"active={stats['active']:<6} archived={stats['archived']:<6} "
                f"last={format_ts(stats['last_seen'])}"
            )
    else:
        print("\nThread index: state database not readable")
    if report["log_evidence"]:
        print("\nCodex core log evidence: Model provider ... not found")
        for provider, entry in sorted(
            report["log_evidence"].items(), key=lambda item: -item[1]["count"]
        ):
            print(
                f"  {provider:<12} {entry['count']:<4} hit(s)  "
                f"{format_ts(entry['first'])} to {format_ts(entry['last'])}"
            )
    if report["desktop_log_evidence"]:
        print("\nDesktop app log evidence: failed to resume conversation")
        for provider, entry in sorted(
            report["desktop_log_evidence"].items(),
            key=lambda item: -item[1]["resume_failures"],
        ):
            print(
                f"  {provider:<12} resume failures={entry['resume_failures']:<4} "
                f"hits={entry['count']:<4} files={entry['files']:<3} last={entry['last']}"
            )
    parity = report["rollout_parity"]
    if parity["checked"]:
        print(
            f"\nRollout metadata sample: {parity['checked']} checked, "
            f"{len(parity['mismatches'])} mismatch(es)"
        )
        for item in parity["mismatches"][:5]:
            detail = item["error"] or (
                f"index={item['index_provider']} rollout={item['rollout_provider']}"
            )
            print(f"  - {item['thread_id']}: {detail}")
    if report["findings"]:
        print("\nFindings")
        for finding in report["findings"]:
            print(f"  [{finding['severity'].upper()}] {finding['message']}")
    unavailable = report["unavailable_history"]
    if unavailable:
        print("\nRecommended repair")
        for provider, stats in unavailable.items():
            if stats["suggested_strategy"] == "define_provider":
                print(
                    f"  - {provider}: define it in config.toml so history keeps its "
                    "bucket; for example\n"
                    f"      python3 \"$SKILL_DIR/scripts/codex_provider_doctor.py\" "
                    f"--print-provider-snippet {provider} --like custom "
                    "--env-key DEEPSEEK_API_KEY"
                )
            else:
                print(
                    f"  - {provider}: retag its {stats['total']} thread(s) to an "
                    "available provider\n"
                    f"      python3 \"$SKILL_DIR/scripts/codex_provider_doctor.py\" "
                    f"--fix-retag {report['config']['model_provider'] or 'openai'} "
                    f"--only-provider {provider}"
                )
        print(
            "  Both branches need an explicit confirmation step; the tool never "
            "edits config.toml itself."
        )
    if not report["findings"] and not unavailable:
        print("\nNo provider mismatch detected.")


def running_codex_processes():
    found = []
    probes = (["pgrep", "-x", "Codex"], ["pgrep", "-f", "codex app-server"])
    for probe in probes:
        try:
            result = subprocess.run(
                probe, capture_output=True, text=True, timeout=5
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode == 0 and result.stdout.strip():
            found.append(" ".join(probe[1:]))
    return found


def make_backup_dir(codex_home):
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = codex_home / BACKUP_DIRNAME / stamp
    backup.mkdir(parents=True, exist_ok=True)
    return backup


def backup_state_db(db_path, backup):
    target = backup / Path(db_path).name
    source = sqlite3.connect(str(db_path))
    try:
        destination = sqlite3.connect(str(target))
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()
    return target


def rollout_backup_path(backup, codex_home, path):
    try:
        relative = path.resolve().relative_to(codex_home.resolve())
    except ValueError:
        relative = Path(path.name)
    return backup / "rollouts" / (str(relative) + ".firstline")


def rewrite_rollout_provider(path, provider, backup, codex_home):
    """Rewrite a rollout's session metadata provider; returns a status word."""
    current, error = rollout_provider(path)
    if error:
        return f"error: {error}"
    if current == provider:
        return "unchanged"
    backup_path = rollout_backup_path(backup, codex_home, path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "rb") as handle:
        first_line = handle.readline()
    if not backup_path.exists():
        backup_path.write_bytes(first_line + b"\n")
    meta = json.loads(first_line.decode("utf-8"))
    payload = meta.get("payload")
    if not isinstance(payload, dict):
        return "error: first record has no payload object"
    payload["model_provider"] = provider
    new_first = json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + "\n"
    temp_path = path.with_name(path.name + ".providerfix.tmp")
    with open(path, "rb") as source, open(temp_path, "wb") as target:
        source.readline()
        target.write(new_first.encode("utf-8"))
        shutil.copyfileobj(source, target)
    shutil.copymode(path, temp_path)
    os.replace(temp_path, path)
    return "rewritten"


def apply_retag(
    codex_home, target, only_providers, active_only, force, skip_rollouts, confirm
):
    config = load_config(codex_home)
    available = set(config["providers"]) | set(BUILTIN_PROVIDERS)
    if target not in available:
        print(
            f"ERROR: target provider {target!r} is not defined; available: "
            f"{', '.join(sorted(available))}",
            file=sys.stderr,
        )
        return 2
    state_path = codex_home / STATE_DB
    threads = load_threads(state_path)
    if threads is None:
        print(f"ERROR: cannot read thread index at {abbrev(state_path)}", file=sys.stderr)
        return 2
    selected = (
        [p for p in only_providers if p in threads]
        if only_providers
        else [p for p in threads if p not in available]
    )
    selected = [p for p in selected if p not in available]
    if not selected:
        print("Nothing to repair: every persisted provider is already available.")
        return 0
    rows = affected_threads(state_path, selected, active_only=active_only)
    rollouts = [r for r in rows if r.get("rollout_path")]
    print("Planned repair")
    print(f"  target provider : {target}")
    print(f"  providers       : {', '.join(selected)}")
    print(f"  threads         : {len(rows)}")
    print(f"  rollout files   : {len(rollouts) if not skip_rollouts else 0}")
    if active_only:
        print("  scope           : active threads only")
    if not confirm:
        print("Dry run: re-run with --yes to apply this repair.")
        return 0
    if not force:
        running = running_codex_processes()
        if running:
            print(
                "ERROR: Codex is running ("
                + "; ".join(running)
                + "). Quit the app first, or pass --force if you know the daemon "
                "does not hold this state database.",
                file=sys.stderr,
            )
            return 3
    backup = make_backup_dir(codex_home)
    backup_state_db(state_path, backup)
    print(f"  backup          : {abbrev(backup)}")
    con = sqlite3.connect(str(state_path))
    con.execute("PRAGMA busy_timeout=10000")
    try:
        with con:
            if active_only:
                for row in rows:
                    con.execute(
                        "UPDATE threads SET model_provider = ? WHERE id = ?",
                        (target, row.get("id")),
                    )
            else:
                for provider in selected:
                    con.execute(
                        "UPDATE threads SET model_provider = ? WHERE model_provider = ?",
                        (target, provider),
                    )
    finally:
        con.close()
    rewritten = unchanged = failures = 0
    if not skip_rollouts:
        for index, row in enumerate(rollouts, start=1):
            path = Path(row["rollout_path"]).expanduser()
            if not path.is_file():
                failures += 1
                continue
            status = rewrite_rollout_provider(path, target, backup, codex_home)
            if status == "rewritten":
                rewritten += 1
            elif status == "unchanged":
                unchanged += 1
            else:
                failures += 1
            if index % 250 == 0:
                print(f"  rollouts        : {index}/{len(rollouts)} processed")
    print("Applied")
    print(f"  threads updated : {len(rows)}")
    print(f"  rollouts        : {rewritten} rewritten, {unchanged} unchanged, {failures} failed")
    if failures:
        print(
            "  note            : failed files were left untouched; restore with "
            f"--restore {abbrev(backup)}",
        )
    after = load_threads(state_path) or {}
    remaining = [p for p in after if p not in available]
    if remaining:
        print(f"  remaining       : {', '.join(remaining)}")
    else:
        print("  remaining       : none")
    return 0


def apply_restore(codex_home, backup, force, confirm):
    state_backup = backup / STATE_DB
    if not state_backup.is_file():
        print(f"ERROR: {abbrev(state_backup)} is missing", file=sys.stderr)
        return 2
    if not confirm:
        print(
            f"Dry run: re-run with --yes to restore {abbrev(codex_home / STATE_DB)} "
            f"and rollout first lines from {abbrev(backup)}."
        )
        return 0
    if not force:
        running = running_codex_processes()
        if running:
            print(
                "ERROR: Codex is running ("
                + "; ".join(running)
                + "). Quit the app first, or pass --force.",
                file=sys.stderr,
            )
            return 3
    shutil.copy2(state_backup, codex_home / STATE_DB)
    restored = 0
    for firstline in (backup / "rollouts").rglob("*.firstline"):
        relative = firstline.relative_to(backup / "rollouts")
        target = codex_home / str(relative)[: -len(".firstline")]
        if not target.is_file():
            continue
        stored = firstline.read_bytes()
        with open(target, "rb") as handle:
            handle.readline()
            rest = handle.read()
        temp_path = target.with_name(target.name + ".providerfix.tmp")
        with open(temp_path, "wb") as handle:
            handle.write(stored)
            handle.write(rest)
        shutil.copymode(target, temp_path)
        os.replace(temp_path, target)
        restored += 1
    print(f"Restored state database and {restored} rollout first line(s) from {abbrev(backup)}")
    return 0


def print_provider_snippet(args, config):
    like = config["providers"].get(args.like or "", {})
    base_url = args.base_url or like.get("base_url", "")
    name = args.name or like.get("name", args.provider)
    wire_api = args.wire_api or like.get("wire_api", "responses")
    lines = [
        f"[model_providers.{args.provider}]",
        f'name = "{name}"',
        f'base_url = "{base_url}"',
        f'wire_api = "{wire_api}"',
        "requires_openai_auth = false",
    ]
    if args.env_key:
        lines.append(f'env_key = "{args.env_key}"')
        lines.append(
            "# GUI-launched apps may not inherit shell variables. Either set this "
            "variable for the app or replace it with an inline bearer token."
        )
    lines.append(
        '# experimental_bearer_token = "<paste the key used by the matching provider>"'
    )
    print("\n".join(lines))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", help="Codex home directory (default: CODEX_HOME or ~/.codex)")
    parser.add_argument("--json", action="store_true", help="print the structured report")
    parser.add_argument(
        "--logs-days",
        type=int,
        default=30,
        help="how many days of Codex logs to scan (default: 30)",
    )
    parser.add_argument(
        "--sample-rollouts",
        type=int,
        default=25,
        help="how many affected rollout files to compare with the index (default: 25)",
    )
    parser.add_argument(
        "--desktop-log-root",
        help="desktop app log directory (default: ~/Library/Logs/com.openai.codex)",
    )
    parser.add_argument(
        "--fix-retag",
        metavar="TARGET",
        help="retag unavailable threads to TARGET provider (writes)",
    )
    parser.add_argument(
        "--only-provider",
        action="append",
        default=[],
        help="limit repair to a persisted provider id (repeatable)",
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="repair only threads that are not archived",
    )
    parser.add_argument(
        "--skip-rollouts",
        action="store_true",
        help="update the thread index only; leave rollout metadata untouched",
    )
    parser.add_argument("--restore", metavar="BACKUP_DIR", help="restore a previous repair")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm a write operation; without it the tool only prints the plan",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="skip the running-app check for write operations",
    )
    parser.add_argument(
        "--print-provider-snippet",
        metavar="PROVIDER",
        dest="provider",
        help="print a config.toml provider block instead of editing anything",
    )
    parser.add_argument("--like", help="copy route fields from an existing provider block")
    parser.add_argument("--base-url", help="override base_url for the printed snippet")
    parser.add_argument("--name", help="override name for the printed snippet")
    parser.add_argument("--wire-api", help="override wire_api for the printed snippet")
    parser.add_argument("--env-key", help="env_key for the printed snippet")
    args = parser.parse_args(argv)

    codex_home = resolve_codex_home(args.codex_home)
    if args.provider:
        return print_provider_snippet(args, load_config(codex_home))
    if args.restore:
        return apply_restore(
            codex_home, Path(args.restore).expanduser(), args.force, args.yes
        )
    if args.fix_retag:
        return apply_retag(
            codex_home,
            args.fix_retag,
            args.only_provider,
            args.active_only,
            args.force,
            args.skip_rollouts,
            args.yes,
        )
    desktop_root = (
        Path(args.desktop_log_root).expanduser()
        if args.desktop_log_root
        else None
    )
    report = build_report(codex_home, args.logs_days, args.sample_rollouts, desktop_root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
