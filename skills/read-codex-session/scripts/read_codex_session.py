#!/usr/bin/env python3
"""Read a local Codex thread's status and recent turns (read-only).

The inspector resolves a thread UUID or ``codex://threads/<uuid>`` deeplink to
the matching rollout JSONL under the local Codex data directory and prints a
compact status summary. It never writes to the Codex data directory, never
prints full transcripts, and requires only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

UUID_RE = re.compile(
    r"([0-9a-fA-F]{8})-?([0-9a-fA-F]{4})-?([0-9a-fA-F]{4})-?"
    r"([0-9a-fA-F]{4})-?([0-9a-fA-F]{12})"
)
CONTEXT_BLOCK_RE = re.compile(
    r"<(INSTRUCTIONS|environment_context|app-context|skill)>.*?</\1>",
    re.DOTALL,
)
EXIT_CODE_RE = re.compile(r"Process exited with code (-?\d+)")


def normalize_uuid(value: str) -> str | None:
    match = UUID_RE.search(value or "")
    if not match:
        return None
    return "-".join(part.lower() for part in match.groups())


def codex_home(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex"


def resolve_session(target: str, home: Path) -> tuple[Path, str, bool]:
    """Return (session_file, thread_id, archived)."""
    direct = Path(target).expanduser()
    if direct.is_file():
        thread_id = normalize_uuid(target)
        if thread_id is None:
            thread_id = normalize_uuid(direct.stem) or direct.stem
        archived = "archived_sessions" in direct.parts
        return direct, thread_id, archived

    thread_id = normalize_uuid(target)
    if thread_id is None:
        raise SystemExit(
            f"error: could not find a thread UUID in {target!r}; "
            "pass a Codex thread UUID, a codex://threads/<uuid> deeplink, "
            "or a rollout JSONL path"
        )

    matches: list[Path] = []
    for root, archived in ((home / "sessions", False), (home / "archived_sessions", True)):
        if not root.is_dir():
            continue
        matches.extend(root.glob(f"*/*/*/rollout-*-{thread_id}.jsonl"))
        if not matches:
            matches.extend(root.rglob(f"rollout-*-{thread_id}.jsonl"))
        if not matches:
            matches.extend(root.rglob(f"*{thread_id}*.jsonl"))
        if matches:
            unique = sorted({path.resolve() for path in matches}, key=lambda p: p.stat().st_mtime, reverse=True)
            return unique[0], thread_id, archived
    raise SystemExit(f"error: no local Codex rollout found for thread {thread_id} under {home}")


def message_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in payload.get("content") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"input_text", "output_text", "text"}:
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts).strip()


def clean_user_text(text: str) -> str:
    cleaned = CONTEXT_BLOCK_RE.sub("", text)
    cleaned = re.sub(r"^# AGENTS\.md instructions\s*", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def one_line(text: str, limit: int) -> str:
    collapsed = re.sub(r"\s+", " ", text or "").strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def output_is_error(output: str) -> bool:
    match = EXIT_CODE_RE.search(output or "")
    if match:
        return int(match.group(1)) != 0
    return (output or "").lstrip().lower().startswith(("error:", "exception:"))


def new_turn(turn_id: str | None, timestamp: str | None, cwd: str | None) -> dict[str, Any]:
    return {
        "turn_id": turn_id,
        "status": "unknown",
        "started_at": timestamp,
        "completed_at": None,
        "cwd": cwd,
        "user": None,
        "final": None,
        "last_assistant": None,
        "tool_calls": 0,
        "tool_errors": 0,
        "pending_calls": [],
    }


def inspect(session_file: Path, thread_id: str, max_turns: int) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    turns: list[dict[str, Any]] = []
    turns_by_id: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    current_cwd: str | None = None
    pending: dict[str, dict[str, Any]] = {}
    created_at: str | None = None
    updated_at: str | None = None
    bad_lines = 0

    def ensure_turn(turn_id: str | None) -> dict[str, Any]:
        nonlocal current
        key = turn_id or (current or {}).get("turn_id") or f"turn-{len(turns) + 1}"
        existing = turns_by_id.get(key)
        if existing is None:
            existing = new_turn(key, updated_at, current_cwd)
            turns_by_id[key] = existing
            turns.append(existing)
        current = existing
        return existing

    with session_file.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                bad_lines += 1
                continue
            if not isinstance(entry, dict):
                bad_lines += 1
                continue

            timestamp = entry.get("timestamp")
            if timestamp:
                updated_at = timestamp
                if created_at is None:
                    created_at = timestamp
            kind = entry.get("type")
            payload = entry.get("payload") or {}
            if not isinstance(payload, dict):
                payload = {}

            if kind == "session_meta":
                meta = payload
                current_cwd = payload.get("cwd") or current_cwd
                created_at = payload.get("timestamp") or created_at
                continue

            if kind == "turn_context":
                current_cwd = payload.get("cwd") or current_cwd
                ensure_turn(payload.get("turn_id"))
                continue

            if kind == "event_msg":
                event = payload.get("type")
                if event == "task_started":
                    turn = ensure_turn(payload.get("turn_id"))
                    turn["status"] = "running"
                    turn["started_at"] = timestamp or turn["started_at"]
                elif event == "task_complete":
                    turn = ensure_turn(payload.get("turn_id"))
                    turn["status"] = "completed"
                    turn["completed_at"] = timestamp
                    final = payload.get("last_agent_message")
                    if isinstance(final, str) and final.strip():
                        turn["final"] = final.strip()
                        turn["last_assistant"] = final.strip()
                elif event in {"turn_aborted", "task_aborted"}:
                    turn = ensure_turn(payload.get("turn_id"))
                    turn["status"] = "aborted"
                    turn["completed_at"] = timestamp
                continue

            if kind != "response_item":
                continue

            item_type = payload.get("type")
            turn = current or ensure_turn(None)
            if item_type == "message":
                role = payload.get("role")
                text = message_text(payload)
                if not text:
                    continue
                if role == "user":
                    cleaned = clean_user_text(text)
                    if cleaned and turn["user"] is None:
                        turn["user"] = cleaned
                elif role == "assistant":
                    turn["last_assistant"] = text
                    if payload.get("phase") == "final_answer":
                        turn["final"] = text
            elif item_type == "function_call":
                call_id = payload.get("call_id") or payload.get("id")
                turn["tool_calls"] += 1
                if isinstance(call_id, str):
                    record = {"call_id": call_id, "name": payload.get("name"), "turn_id": turn["turn_id"]}
                    turn["pending_calls"].append(record)
                    pending[call_id] = record
            elif item_type == "function_call_output":
                call_id = payload.get("call_id")
                record = pending.pop(call_id, None) if isinstance(call_id, str) else None
                owner = turns_by_id.get((record or {}).get("turn_id")) if record else turn
                output = payload.get("output")
                if isinstance(output, str) and output_is_error(output):
                    (owner or turn)["tool_errors"] += 1
                if record:
                    for candidate in (owner, turn):
                        if candidate and record in candidate["pending_calls"]:
                            candidate["pending_calls"].remove(record)

    if not turns:
        turns.append(ensure_turn(None))
    for turn in turns:
        if pending:
            turn["pending_calls"] = [call for call in turn["pending_calls"] if call["call_id"] in pending]

    latest = turns[-1]
    status = latest.get("status") or "unknown"
    if pending and status == "running":
        status = "running"
    title = None
    for turn in turns:
        if turn.get("user"):
            title = one_line(turn["user"], 80)
            break

    selected = turns[-max_turns:] if max_turns > 0 else []
    return {
        "thread_id": meta.get("id") or meta.get("session_id") or thread_id,
        "title": title or "(untitled)",
        "status": status,
        "cwd": current_cwd or meta.get("cwd"),
        "provider": meta.get("model_provider"),
        "originator": meta.get("originator"),
        "cli_version": meta.get("cli_version"),
        "created_at": created_at,
        "updated_at": updated_at,
        "session_file": str(session_file),
        "pending_tool_calls": len(pending),
        "turn_count": len(turns),
        "malformed_lines": bad_lines,
        "turns": [
            {
                "turn_id": turn.get("turn_id"),
                "status": turn.get("status"),
                "started_at": turn.get("started_at"),
                "completed_at": turn.get("completed_at"),
                "user": turn.get("user"),
                "final": turn.get("final"),
                "last_assistant": turn.get("last_assistant"),
                "tool_calls": turn.get("tool_calls"),
                "tool_errors": turn.get("tool_errors"),
                "pending_tool_calls": len(turn.get("pending_calls") or []),
            }
            for turn in selected
        ],
    }


def render_text(report: dict[str, Any], max_turns: int) -> str:
    lines = [
        f"Thread: {report['thread_id']}",
        f"Title: {report['title']}",
        f"Status: {report['status']}",
        f"Workspace: {report['cwd'] or 'unknown'}",
        "Provider: {provider} | Origin: {origin} | Updated: {updated}".format(
            provider=report.get("provider") or "unknown",
            origin=report.get("originator") or "unknown",
            updated=report.get("updated_at") or "unknown",
        ),
        f"Turns: {report['turn_count']} (showing last {len(report['turns'])})",
    ]
    if report.get("pending_tool_calls"):
        lines.append(f"Pending tool calls: {report['pending_tool_calls']}")
    if report.get("malformed_lines"):
        lines.append(f"Unreadable JSONL lines skipped: {report['malformed_lines']}")

    for turn in report["turns"]:
        lines.append("")
        lines.append(f"## {one_line(turn.get('turn_id') or 'turn', 40)} — {turn.get('status')}")
        if turn.get("user"):
            lines.append(f"User: {one_line(turn['user'], 300)}")
        final = turn.get("final") or turn.get("last_assistant")
        if final:
            lines.append(f"Latest: {one_line(final, 600)}")
        lines.append(
            "Activity: {calls} tool calls, {errors} errors, {pending} pending".format(
                calls=turn.get("tool_calls") or 0,
                errors=turn.get("tool_errors") or 0,
                pending=turn.get("pending_tool_calls") or 0,
            )
        )
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read a local Codex thread's status and recent turns (read-only)."
    )
    parser.add_argument("target", help="Codex thread UUID, codex://threads/<uuid> deeplink, or rollout JSONL path")
    parser.add_argument("--turns", type=int, default=3, help="number of recent turns to show (default: 3)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="print a machine-readable report")
    parser.add_argument("--codex-home", help="Codex data directory (default: $CODEX_HOME or ~/.codex)")
    args = parser.parse_args(list(argv) if argv is not None else None)

    home = codex_home(args.codex_home)
    session_file, thread_id, _archived = resolve_session(args.target, home)
    report = inspect(session_file, thread_id, max(args.turns, 0))
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_text(report, args.turns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
