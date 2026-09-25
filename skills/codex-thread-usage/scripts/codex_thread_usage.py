#!/usr/bin/env python3
"""Inspect token usage for a local Codex thread without reading message bodies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


THREAD_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


class UsageError(RuntimeError):
    """Expected, user-actionable failure."""


def parse_thread_id(value: str) -> str:
    candidate = value.strip()
    if candidate.lower().startswith("codex://"):
        parsed = urlparse(candidate)
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.netloc not in {"thread", "threads"} or len(parts) != 1:
            raise UsageError(
                "invalid Codex deeplink; expected codex://threads/<uuid>"
            )
        candidate = parts[0]
    if not THREAD_ID_RE.fullmatch(candidate):
        raise UsageError("invalid thread id; expected a UUID")
    return candidate.lower()


def compact_path(path: Path, codex_home: Path) -> str:
    try:
        return f"$CODEX_HOME/{path.resolve().relative_to(codex_home.resolve())}"
    except (OSError, ValueError):
        return path.name


def table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    except sqlite3.DatabaseError:
        return set()
    return {str(row[1]) for row in rows}


def read_state_row(codex_home: Path, thread_id: str) -> dict[str, Any] | None:
    state_path = codex_home / "state_5.sqlite"
    if not state_path.is_file():
        return None
    try:
        uri = f"file:{state_path}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        columns = table_columns(connection, "threads")
        wanted = [
            name
            for name in (
                "id",
                "rollout_path",
                "tokens_used",
                "model_provider",
                "model",
                "reasoning_effort",
                "cli_version",
                "archived",
                "created_at",
                "updated_at",
            )
            if name in columns
        ]
        if "id" not in wanted:
            return None
        row = connection.execute(
            f"SELECT {', '.join(wanted)} FROM threads WHERE id = ?", (thread_id,)
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.DatabaseError as exc:
        raise UsageError(f"cannot read state_5.sqlite: {exc}") from exc
    finally:
        if "connection" in locals():
            connection.close()


def rollout_candidates(codex_home: Path, thread_id: str) -> Iterable[Path]:
    for base_name in ("sessions", "archived_sessions"):
        base = codex_home / base_name
        if not base.is_dir():
            continue
        yield from base.rglob(f"*{thread_id}*.jsonl")


def resolve_rollout(
    codex_home: Path, thread_id: str, state_row: dict[str, Any] | None
) -> Path:
    if state_row:
        stored = state_row.get("rollout_path")
        if isinstance(stored, str) and stored:
            path = Path(os.path.expandvars(os.path.expanduser(stored)))
            if path.is_file():
                return path
    candidates = sorted(
        {path.resolve() for path in rollout_candidates(codex_home, thread_id)},
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    if not candidates:
        raise UsageError(
            "thread exists neither in state_5.sqlite nor in local session rollouts"
        )
    return candidates[0]


def integer(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


@dataclass
class Usage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_mapping(cls, value: Any) -> "Usage":
        data = value if isinstance(value, dict) else {}
        return cls(
            input_tokens=integer(data.get("input_tokens")),
            cached_input_tokens=integer(data.get("cached_input_tokens")),
            cache_write_input_tokens=integer(data.get("cache_write_input_tokens")),
            output_tokens=integer(data.get("output_tokens")),
            reasoning_output_tokens=integer(data.get("reasoning_output_tokens")),
            total_tokens=integer(data.get("total_tokens")),
        )

    def add(self, other: "Usage") -> None:
        for name in self.__dataclass_fields__:
            setattr(self, name, getattr(self, name) + getattr(other, name))

    @property
    def non_cached_input_tokens(self) -> int:
        return max(self.input_tokens - self.cached_input_tokens, 0)

    @property
    def tui_style_total_tokens(self) -> int:
        return self.non_cached_input_tokens + max(self.output_tokens, 0)

    @property
    def component_total_matches(self) -> bool:
        return self.total_tokens == self.input_tokens + self.output_tokens

    def as_dict(self) -> dict[str, int]:
        return {
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_write_input_tokens": self.cache_write_input_tokens,
            "non_cached_input_tokens": self.non_cached_input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_output_tokens": self.reasoning_output_tokens,
            "tui_style_total_tokens": self.tui_style_total_tokens,
        }


@dataclass
class Segment:
    first_timestamp: str | None
    last_timestamp: str | None
    terminal: Usage
    event_count: int = 1
    contains_estimated_snapshot: bool = False

    def as_dict(self, number: int) -> dict[str, Any]:
        return {
            "number": number,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "token_count_events": self.event_count,
            "contains_estimated_snapshot": self.contains_estimated_snapshot,
            **self.terminal.as_dict(),
        }


@dataclass
class UsageScan:
    thread_id: str | None = None
    segments: list[Segment] = field(default_factory=list)
    current_segment: Segment | None = None
    token_count_events: int = 0
    null_token_count_events: int = 0
    malformed_lines: int = 0
    raw_response_events: int = 0
    raw_response_usage: Usage = field(default_factory=Usage)

    def finish_segment(self) -> None:
        if self.current_segment is not None:
            self.segments.append(self.current_segment)
            self.current_segment = None

    def observe_token_count(self, timestamp: Any, info: Any) -> None:
        self.token_count_events += 1
        if not isinstance(info, dict):
            self.null_token_count_events += 1
            self.finish_segment()
            return
        usage = Usage.from_mapping(info.get("total_token_usage"))
        estimated = not usage.component_total_matches
        timestamp_text = timestamp if isinstance(timestamp, str) else None
        if (
            self.current_segment is not None
            and usage.total_tokens < self.current_segment.terminal.total_tokens
        ):
            self.finish_segment()
        if self.current_segment is None:
            self.current_segment = Segment(
                first_timestamp=timestamp_text,
                last_timestamp=timestamp_text,
                terminal=usage,
                contains_estimated_snapshot=estimated,
            )
            return
        self.current_segment.last_timestamp = timestamp_text
        self.current_segment.terminal = usage
        self.current_segment.event_count += 1
        self.current_segment.contains_estimated_snapshot |= estimated

    def observe_raw_response(self, usage: Any) -> None:
        if not isinstance(usage, dict):
            return
        self.raw_response_events += 1
        self.raw_response_usage.add(Usage.from_mapping(usage))

    def historical_total(self) -> Usage:
        total = Usage()
        for segment in self.segments:
            total.add(segment.terminal)
        return total


def scan_rollout(path: Path) -> UsageScan:
    scan = UsageScan()
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                scan.malformed_lines += 1
                continue
            if not isinstance(record, dict):
                continue
            record_type = record.get("type")
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            if record_type == "session_meta":
                value = payload.get("id")
                if isinstance(value, str):
                    scan.thread_id = value.lower()
                continue
            if record_type != "event_msg":
                continue
            event_type = payload.get("type")
            if event_type == "token_count":
                scan.observe_token_count(record.get("timestamp"), payload.get("info"))
            elif event_type == "raw_response_completed":
                scan.observe_raw_response(payload.get("token_usage"))
    scan.finish_segment()
    return scan


def build_report(value: str, codex_home: Path) -> dict[str, Any]:
    thread_id = parse_thread_id(value)
    state_row = read_state_row(codex_home, thread_id)
    rollout_path = resolve_rollout(codex_home, thread_id, state_row)
    scan = scan_rollout(rollout_path)
    if scan.thread_id and scan.thread_id != thread_id:
        raise UsageError(
            f"rollout session id mismatch: expected {thread_id}, found {scan.thread_id}"
        )
    if not scan.segments:
        raise UsageError("rollout contains no usable token_count events")

    total = scan.historical_total()
    estimated_segments = sum(
        1 for segment in scan.segments if segment.contains_estimated_snapshot
    )
    warnings = [
        "total_tokens includes cached input; cached_input_tokens is a subset of input_tokens",
        "reasoning_output_tokens is a subset of output_tokens and must not be added again",
        "tui_style_total_tokens excludes cached input but is not a billing-cost estimate",
    ]
    if len(scan.segments) > 1:
        warnings.append(
            "the in-memory cumulative counter reset; SQLite therefore shows only the latest segment"
        )
    if estimated_segments:
        warnings.append(
            "at least one token_count snapshot was estimated or replayed; historical total is not exact API billing"
        )
    if scan.malformed_lines:
        warnings.append(
            f"ignored {scan.malformed_lines} malformed rollout line(s)"
        )

    latest_snapshot = None
    if state_row and "tokens_used" in state_row:
        latest_snapshot = integer(state_row.get("tokens_used"))

    report: dict[str, Any] = {
        "schema": "lov-codex-thread-usage/v1",
        "thread_id": thread_id,
        "rollout": {
            "path": compact_path(rollout_path, codex_home),
            "token_count_events": scan.token_count_events,
            "null_token_count_events": scan.null_token_count_events,
            "malformed_lines": scan.malformed_lines,
        },
        "state_snapshot": {
            "found": state_row is not None,
            "tokens_used": latest_snapshot,
            "model_provider": state_row.get("model_provider") if state_row else None,
            "model": state_row.get("model") if state_row else None,
            "reasoning_effort": state_row.get("reasoning_effort") if state_row else None,
            "cli_version": state_row.get("cli_version") if state_row else None,
        },
        "historical": {
            "method": "sum_of_terminal_total_token_usage_per_monotonic_segment",
            "quality": (
                "accumulated_with_estimated_or_replayed_snapshots"
                if estimated_segments
                else "codex_accumulated_provider_reported_snapshots"
            ),
            "segments": len(scan.segments),
            "counter_resets": max(len(scan.segments) - 1, 0),
            "estimated_segments": estimated_segments,
            **total.as_dict(),
        },
        "raw_response_completed": {
            "events": scan.raw_response_events,
            **scan.raw_response_usage.as_dict(),
            "note": (
                "exact per-response events are partial unless every upstream completion emitted one"
            ),
        },
        "segment_details": [
            segment.as_dict(index)
            for index, segment in enumerate(scan.segments, start=1)
        ],
        "warnings": warnings,
    }
    return report


def format_text(report: dict[str, Any], details: bool) -> str:
    historical = report["historical"]
    state = report["state_snapshot"]
    lines = [
        f"Codex thread: {report['thread_id']}",
        f"Historical processed tokens: {historical['total_tokens']:,}",
        (
            "  input: {input_tokens:,} (cached subset: {cached_input_tokens:,}; "
            "non-cached: {non_cached_input_tokens:,})"
        ).format(**historical),
        (
            "  output: {output_tokens:,} (reasoning subset: "
            "{reasoning_output_tokens:,})"
        ).format(**historical),
        f"TUI-style non-cached total: {historical['tui_style_total_tokens']:,}",
        (
            f"Latest SQLite snapshot: {state['tokens_used']:,}"
            if isinstance(state.get("tokens_used"), int)
            else "Latest SQLite snapshot: unavailable"
        ),
        (
            f"Counter segments: {historical['segments']} "
            f"(resets: {historical['counter_resets']})"
        ),
        f"Rollout: {report['rollout']['path']}",
        f"Quality: {historical['quality']}",
    ]
    if details:
        lines.append("Segments:")
        for segment in report["segment_details"]:
            lines.append(
                "  #{number}: {total_tokens:,} tokens, {first_timestamp} -> "
                "{last_timestamp}".format(**segment)
            )
    lines.append("Warnings:")
    lines.extend(f"  - {warning}" for warning in report["warnings"])
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Inspect local Codex thread token usage from a deeplink or UUID."
    )
    result.add_argument("thread", help="codex://threads/<uuid> or a raw thread UUID")
    result.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
        help="Codex data directory (default: CODEX_HOME or ~/.codex)",
    )
    result.add_argument("--json", action="store_true", help="emit JSON")
    result.add_argument(
        "--details", action="store_true", help="include each counter segment in text output"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        report = build_report(args.thread, args.codex_home.expanduser())
    except UsageError as exc:
        print(f"lov-codex-thread-usage: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_text(report, args.details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
