#!/usr/bin/env python3
"""Regression test for the local Codex session inspector."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "read_codex_session.py"
THREAD_ID = "11111111-2222-3333-4444-555555555555"


def build_fixture(home: Path) -> Path:
    folder = home / "sessions" / "2026" / "09" / "12"
    folder.mkdir(parents=True)
    session = folder / f"rollout-2026-09-12T00-00-00-{THREAD_ID}.jsonl"
    entries = [
        {
            "timestamp": "2026-09-12T00:00:00.000Z",
            "type": "session_meta",
            "payload": {
                "id": THREAD_ID,
                "timestamp": "2026-09-12T00:00:00.000Z",
                "cwd": "/tmp/demo",
                "model_provider": "custom",
                "originator": "Codex Desktop",
                "cli_version": "0.0.0",
            },
        },
        {"timestamp": "2026-09-12T00:00:01.000Z", "type": "turn_context", "payload": {"turn_id": "turn-1", "cwd": "/tmp/demo"}},
        {"timestamp": "2026-09-12T00:00:02.000Z", "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-1"}},
        {
            "timestamp": "2026-09-12T00:00:03.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "<environment_context>noise</environment_context>\n请检查这个演示任务"}],
            },
        },
        {
            "timestamp": "2026-09-12T00:00:04.000Z",
            "type": "response_item",
            "payload": {"type": "function_call", "call_id": "call-1", "name": "exec_command", "arguments": "{}"},
        },
        {
            "timestamp": "2026-09-12T00:00:05.000Z",
            "type": "response_item",
            "payload": {"type": "function_call_output", "call_id": "call-1", "output": "Process exited with code 1\nboom"},
        },
        {
            "timestamp": "2026-09-12T00:00:06.000Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "phase": "final_answer",
                "content": [{"type": "output_text", "text": "演示任务已完成，但有一个工具报错。"}],
            },
        },
        {
            "timestamp": "2026-09-12T00:00:07.000Z",
            "type": "event_msg",
            "payload": {"type": "task_complete", "turn_id": "turn-1", "last_agent_message": "演示任务已完成，但有一个工具报错。"},
        },
    ]
    session.write_text("\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n", encoding="utf-8")
    return session


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        home = Path(temp) / "codex"
        build_fixture(home)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), THREAD_ID, "--codex-home", str(home), "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["thread_id"] == THREAD_ID, report
        assert report["status"] == "completed", report
        assert report["cwd"] == "/tmp/demo", report
        turn = report["turns"][-1]
        assert turn["tool_calls"] == 1 and turn["tool_errors"] == 1, turn
        assert "演示任务" in (turn["user"] or ""), turn
        assert turn["final"].startswith("演示任务已完成"), turn

        text = subprocess.run(
            [sys.executable, str(SCRIPT), f"codex://threads/{THREAD_ID}", "--codex-home", str(home)],
            capture_output=True,
            text=True,
        )
        assert text.returncode == 0, text.stderr
        assert "Status: completed" in text.stdout, text.stdout
        assert "1 tool calls, 1 errors" in text.stdout, text.stdout
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
