#!/usr/bin/env python3
"""Read and verify one Yoda automation record without modifying the database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = (
    "id", "title", "schedule_label", "status", "trigger_kind", "cron_expr",
    "timezone", "next_run_at", "updated_at",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path, help="Yoda SQLite database path")
    parser.add_argument("--id", required=True, help="Automation identifier")
    parser.add_argument("--expect-cron", help="Expected five-field cron expression")
    parser.add_argument("--expect-timezone", help="Expected IANA timezone")
    return parser.parse_args()


def utc_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def main() -> int:
    args = parse_args()
    context_id = f"yoda-automation-{uuid.uuid4()}"
    if not args.db.is_file():
        print(json.dumps({"ok": False, "context_id": context_id, "error": "database file not found"}, ensure_ascii=False))
        return 2

    connection = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT id, title, schedule_label, status, trigger_kind, cron_expr, timezone, next_run_at, updated_at "
            "FROM automations WHERE id = ?",
            (args.id,),
        ).fetchone()
        latest_run = connection.execute(
            "SELECT trigger, status, started_at, finished_at, error "
            "FROM automation_runs WHERE automation_id = ? ORDER BY started_at DESC LIMIT 1",
            (args.id,),
        ).fetchone()
    except sqlite3.Error as exc:
        print(json.dumps({"ok": False, "context_id": context_id, "error": f"SQLite read failed: {exc}"}, ensure_ascii=False))
        return 2
    finally:
        connection.close()

    if row is None:
        print(json.dumps({"ok": False, "context_id": context_id, "error": "automation not found"}, ensure_ascii=False))
        return 1

    automation: dict[str, Any] = {column: row[column] for column in REQUIRED_COLUMNS}
    errors: list[str] = []
    if automation["status"] != "active":
        errors.append("status is not active")
    if automation["trigger_kind"] == "cron":
        cron = automation["cron_expr"] or ""
        if len(cron.split()) != 5:
            errors.append("cron trigger requires a five-field cron_expr")
    if args.expect_cron and automation["cron_expr"] != args.expect_cron:
        errors.append("cron_expr differs from expected value")
    if args.expect_timezone and automation["timezone"] != args.expect_timezone:
        errors.append("timezone differs from expected value")
    next_run = utc_timestamp(automation["next_run_at"])
    if next_run is None:
        errors.append("next_run_at is missing or invalid")
    elif next_run <= datetime.now(timezone.utc):
        errors.append("next_run_at is not in the future")

    result = {
        "ok": not errors,
        "context_id": context_id,
        "automation": automation,
        "latest_run": dict(latest_run) if latest_run else None,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
