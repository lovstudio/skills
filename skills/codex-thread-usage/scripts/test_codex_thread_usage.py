#!/usr/bin/env python3
"""Unit tests for codex_thread_usage.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from codex_thread_usage import UsageError, parse_thread_id, scan_rollout


THREAD_ID = "01900000-0000-7000-8000-000000000001"


def token_record(total: int, input_tokens: int, output_tokens: int) -> dict:
    return {
        "timestamp": "2026-08-14T00:00:00Z",
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {
                "total_token_usage": {
                    "total_tokens": total,
                    "input_tokens": input_tokens,
                    "cached_input_tokens": 0,
                    "cache_write_input_tokens": 0,
                    "output_tokens": output_tokens,
                    "reasoning_output_tokens": 0,
                }
            },
        },
    }


class CodexThreadUsageTests(unittest.TestCase):
    def test_parse_deeplink(self) -> None:
        self.assertEqual(parse_thread_id(f"codex://threads/{THREAD_ID}"), THREAD_ID)
        self.assertEqual(parse_thread_id(THREAD_ID.upper()), THREAD_ID)

    def test_rejects_invalid_deeplink(self) -> None:
        with self.assertRaises(UsageError):
            parse_thread_id(f"codex://projects/{THREAD_ID}")

    def test_segments_on_counter_decrease_and_null(self) -> None:
        records = [
            {"type": "session_meta", "payload": {"id": THREAD_ID}},
            token_record(100, 90, 10),
            token_record(150, 130, 20),
            token_record(40, 35, 5),
            {
                "type": "event_msg",
                "payload": {"type": "token_count", "info": None},
            },
            token_record(20, 18, 2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            rollout = Path(directory) / "rollout.jsonl"
            rollout.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )
            scan = scan_rollout(rollout)
        self.assertEqual(len(scan.segments), 3)
        self.assertEqual(scan.historical_total().total_tokens, 210)
        self.assertEqual(scan.null_token_count_events, 1)


if __name__ == "__main__":
    unittest.main()
