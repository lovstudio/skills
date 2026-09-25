#!/usr/bin/env python3
"""Focused transcript normalization tests."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "share_session.py"
SPEC = importlib.util.spec_from_file_location("share_session", SCRIPT)
assert SPEC and SPEC.loader
share_session = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = share_session
SPEC.loader.exec_module(share_session)


class ShareSessionTests(unittest.TestCase):
    def test_builds_paid_access_without_accepting_a_client_price(self) -> None:
        upload = share_session.build_upload(
            [{"type": "user", "message": {"content": "accepted"}}],
            "concise",
            "Case session",
            paid_skill="lov-media-creator",
            case_id="screen-studio-case",
        )
        self.assertEqual(
            upload["access"],
            {
                "mode": "paid",
                "sourceSkillName": "lov-media-creator",
                "caseId": "screen-studio-case",
            },
        )
        self.assertNotIn("priceCredits", upload["access"])
        self.assertIsNone(upload["blocks"][0]["timestamp"])

    def test_paid_access_requires_target_skill_and_case_together(self) -> None:
        records = [{"type": "user", "message": {"content": "accepted"}}]
        with self.assertRaisesRegex(share_session.ShareError, "--case-id"):
            share_session.build_upload(
                records,
                "concise",
                "Case session",
                paid_skill="lov-media-creator",
            )

    def test_validates_server_authoritative_paid_result(self) -> None:
        payload = share_session.result_payload(
            {
                "url": "https://lovstudio.ai/yoda/session/yss_demo",
                "accessMode": "paid",
                "sourceSkillName": "lov-media-creator",
                "caseId": "screen-studio-case",
                "priceCredits": 140,
                "pricingRule": "ceil(target-skill-price/10)",
            },
            "concise",
            "lov-media-creator",
        )
        self.assertEqual(payload["priceCredits"], 140)
        self.assertEqual(payload["access"], "paid")
        self.assertNotIn("?detail=", payload["targetSkill"])

    def test_normalizes_codex_messages_and_skips_internal_records(self) -> None:
        records = [
            {
                "type": "response_item",
                "timestamp": "2026-08-23T10:00:00Z",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "<recommended_plugins>ambient</recommended_plugins>",
                        },
                        {
                            "type": "input_text",
                            "text": (
                                "# AGENTS.md instructions\n\n"
                                "<INSTRUCTIONS>\nsecret system prompt\n</INSTRUCTIONS>"
                            ),
                        },
                        {
                            "type": "input_text",
                            "text": "<environment_context>ambient</environment_context>",
                        },
                        {"type": "input_text", "text": "分享这个会话"},
                    ],
                },
            },
            {
                "type": "response_item",
                "timestamp": "2026-08-23T10:00:01Z",
                "payload": {
                    "type": "message",
                    "role": "developer",
                    "content": [{"type": "input_text", "text": "internal"}],
                },
            },
            {
                "type": "response_item",
                "timestamp": "2026-08-23T10:00:02Z",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "可以。"},
                        {"type": "reasoning", "text": "hidden"},
                    ],
                },
            },
            {"type": "event_msg", "payload": {"type": "token_count"}},
        ]
        blocks = share_session.normalize_transcript(records, "concise")
        self.assertEqual([item["role"] for item in blocks], ["user", "assistant"])
        self.assertEqual(blocks[0]["content"], "分享这个会话")
        self.assertEqual(blocks[1]["content"], "可以。")
        self.assertEqual(blocks[0]["timestamp"], "2026-08-23T10:00:00+00:00")

    def test_strips_all_known_host_context_envelopes_and_keeps_user_prompt(self) -> None:
        injected = "\n".join(
            [
                "<app-context>desktop internals</app-context>",
                "<skills_instructions>skill catalog</skills_instructions>",
                "<permissions instructions>sandbox policy</permissions instructions>",
                "<collaboration_mode>Default</collaboration_mode>",
                "<apps_instructions>connector policy</apps_instructions>",
                "<plugins_instructions>plugin policy</plugins_instructions>",
                "真正的用户问题",
            ]
        )
        records = [{"type": "user", "message": {"content": injected}}]
        blocks = share_session.normalize_transcript(records, "concise")
        self.assertEqual(blocks[0]["content"], "真正的用户问题")

    def test_fails_closed_on_malformed_internal_context(self) -> None:
        records = [
            {
                "type": "user",
                "message": {
                    "content": "<environment_context>unterminated host data\n真实问题"
                },
            }
        ]
        with self.assertRaisesRegex(share_session.ShareError, "已阻止上传"):
            share_session.normalize_transcript(records, "concise")

    def test_redacts_private_home_paths_and_obvious_tokens(self) -> None:
        records = [
            {
                "type": "user",
                "message": {
                    "content": (
                        "读取 /" + "Users/mark/private.txt，并使用 "
                        "ghp_abcdefghijklmnopqrstuvwxyz123456"
                    )
                },
            }
        ]
        blocks = share_session.normalize_transcript(records, "concise")
        self.assertEqual(
            blocks[0]["content"],
            "读取 $HOME/private.txt，并使用 [REDACTED_GITHUB_TOKEN]",
        )

    def test_claude_tool_calls_become_tool_blocks_and_final_phase_is_marked(self) -> None:
        records = [
            {"type": "user", "timestamp": "2026-09-12T05:47:21Z", "message": {"content": "写一本书"}},
            {
                "type": "assistant",
                "timestamp": "2026-09-12T05:47:25Z",
                "message": {
                    "stop_reason": "tool_use",
                    "content": [
                        {"type": "thinking", "thinking": "private", "signature": "x"},
                        {"type": "text", "text": "我先解密 skill。"},
                        {
                            "type": "tool_use",
                            "id": "toolu_1",
                            "name": "Bash",
                            "input": {"command": "uvx helper decrypt book", "description": "Decrypt"},
                        },
                    ],
                },
            },
            {
                "type": "user",
                "timestamp": "2026-09-12T05:47:30Z",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_1",
                            "content": "Exit code 1\n<system-reminder>host noise</system-reminder>",
                        }
                    ]
                },
            },
            {
                "type": "assistant",
                "timestamp": "2026-09-12T05:48:00Z",
                "message": {"stop_reason": "end_turn", "content": [{"type": "text", "text": "完成。"}]},
            },
        ]
        blocks = share_session.normalize_transcript(records, "verbose")
        self.assertEqual([b["role"] for b in blocks], ["user", "assistant", "tool", "tool", "assistant"])
        self.assertEqual(blocks[1]["agentPhase"], "commentary")
        self.assertEqual(blocks[2]["title"], "Tool · Bash")
        self.assertEqual(blocks[2]["format"], "code")
        self.assertEqual(blocks[2]["content"], "$ uvx helper decrypt book\n# Decrypt")
        self.assertEqual(blocks[3]["title"], "Tool output")
        self.assertEqual(blocks[3]["content"], "Exit code 1")
        self.assertEqual(blocks[4]["agentPhase"], "final")
        self.assertNotIn("private", json.dumps(blocks, ensure_ascii=False))

    def test_tool_output_with_unstrippable_host_context_is_dropped_not_fatal(self) -> None:
        records = [
            {"type": "user", "message": {"content": "hi"}},
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "toolu_2",
                            "content": "Base directory for this skill: /x\n# SKILL body",
                        }
                    ]
                },
            },
        ]
        blocks = share_session.normalize_transcript(records, "verbose")
        self.assertEqual([b["role"] for b in blocks], ["user"])

    def test_unconcluded_turn_promotes_last_reply_to_final(self) -> None:
        records = [
            {"type": "user", "message": {"content": "q"}},
            {"type": "assistant", "message": {"stop_reason": "tool_use", "content": "step one"}},
            {"type": "assistant", "message": {"stop_reason": "tool_use", "content": "step two"}},
        ]
        blocks = share_session.normalize_transcript(records, "concise")
        self.assertEqual(blocks[1]["agentPhase"], "commentary")
        self.assertEqual(blocks[2]["agentPhase"], "final")

    def test_codex_function_calls_become_tool_blocks(self) -> None:
        records = [
            {"type": "response_item", "timestamp": "2026-09-11T02:01:03Z", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "find files"}]}},
            {"type": "response_item", "timestamp": "2026-09-11T02:01:11Z", "payload": {"type": "function_call", "name": "exec_command", "arguments": "{\"cmd\": \"rg --files\"}", "call_id": "c1"}},
            {"type": "response_item", "timestamp": "2026-09-11T02:01:21Z", "payload": {"type": "function_call_output", "call_id": "c1", "output": "a.txt\nb.txt"}},
            {"type": "response_item", "timestamp": "2026-09-11T02:01:30Z", "payload": {"type": "reasoning", "summary": []}},
            {"type": "response_item", "timestamp": "2026-09-11T02:01:31Z", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "两个文件。"}]}},
        ]
        blocks = share_session.normalize_transcript(records, "verbose")
        self.assertEqual([b["role"] for b in blocks], ["user", "tool", "tool", "assistant"])
        self.assertEqual(blocks[1]["content"], "$ rg --files")
        self.assertEqual(blocks[2]["content"], "a.txt\nb.txt")
        self.assertEqual(blocks[3]["agentPhase"], "final")

    def test_long_tool_output_is_truncated_with_marker(self) -> None:
        records = [
            {"type": "user", "message": {"content": "hi"}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t", "content": "x" * 20000}]}},
        ]
        blocks = share_session.normalize_transcript(records, "verbose")
        self.assertIn("[... truncated", blocks[1]["content"])
        self.assertLess(len(blocks[1]["content"]), 17000)

    def test_exclude_tool_pattern_drops_matching_tool_blocks_only(self) -> None:
        share_session.set_tool_exclude_patterns([r"^name: lovstudio:paid-skill"])
        try:
            records = [
                {"type": "user", "message": {"content": "decrypt"}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "a", "content": "---\nname: lovstudio:paid-skill\nbody"}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "b", "content": "ok"}]}},
            ]
            blocks = share_session.normalize_transcript(records, "verbose")
        finally:
            share_session.set_tool_exclude_patterns([])
        self.assertEqual([b["role"] for b in blocks], ["user", "tool"])
        self.assertEqual(blocks[1]["content"], "ok")

    def test_claude_narration_thinking_is_shared_but_real_thinking_is_not(self) -> None:
        import base64
        narration_sig = base64.b64encode(b"\x08\x04\x12\xfd\x06\n\x11\x08\x11\x18\x028\x01B\tnarration\x12\x0c" + b"x" * 40).decode()
        thinking_sig = base64.b64encode(b"\x08\x04\x12\x84\x05\n\x10\x08\x11\x18\x028\x01B\x08thinking\x12\x0c" + b"x" * 40).decode()
        records = [
            {"type": "user", "message": {"content": "go"}},
            {"type": "assistant", "message": {"stop_reason": "tool_use", "content": [
                {"type": "thinking", "thinking": "secret reasoning", "signature": thinking_sig},
                {"type": "thinking", "thinking": "已获取流程，接下来并行读取。\n\n", "signature": narration_sig},
                {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "/x"}},
            ]}},
            {"type": "assistant", "message": {"stop_reason": "end_turn", "content": [{"type": "text", "text": "done"}]}},
        ]
        blocks = share_session.normalize_transcript(records, "verbose")
        self.assertEqual([b["role"] for b in blocks], ["user", "assistant", "tool", "assistant"])
        self.assertEqual(blocks[1]["content"], "已获取流程，接下来并行读取。")
        self.assertEqual(blocks[1]["agentPhase"], "commentary")
        self.assertNotIn("secret reasoning", json.dumps(blocks, ensure_ascii=False))

    def test_resolves_all_codex_segments_in_chronological_order(self) -> None:
        session_id = "01a00000-0000-7000-8000-000000000001"
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary) / ".codex"
            sessions = codex_home / "sessions" / "2026" / "08" / "23"
            sessions.mkdir(parents=True)
            first = sessions / f"rollout-2026-08-23T10-00-00-{session_id}.jsonl"
            second = sessions / f"rollout-2026-08-23T11-00-00-{session_id}_continued.jsonl"
            other = sessions / f"rollout-2026-08-23T12-00-00-{session_id}_other.jsonl"
            first.write_text(json.dumps({"type": "session_meta", "payload": {"id": session_id}}) + "\n", encoding="utf-8")
            second.write_text(json.dumps({"type": "session_meta", "payload": {"id": session_id}}) + "\n", encoding="utf-8")
            other.write_text(json.dumps({"type": "session_meta", "payload": {"id": "different"}}) + "\n", encoding="utf-8")
            os.utime(first, (1, 1))
            os.utime(second, (2, 2))
            args = argparse.Namespace(file=None, session_id=None)
            with patch.dict(
                os.environ,
                {"CODEX_HOME": str(codex_home), "CODEX_SESSION_ID": session_id},
                clear=False,
            ):
                paths = share_session.resolve_transcript_paths(args)
            self.assertEqual(paths, [first, second])

    def test_retries_unauthorized_cached_token_after_refresh(self) -> None:
        unauthorized = share_session.ShareError("unauthorized", 3)
        unauthorized.status = 401
        args = argparse.Namespace(
            token=None,
            profile_path=Path("/tmp/profile.json"),
            base_url="https://lovstudio.ai",
            timeout=60,
        )
        upload_mock = Mock(side_effect=[unauthorized, {"url": "https://lovstudio.ai/s/demo"}])
        with (
            patch.object(share_session, "load_access_token", return_value="stale"),
            patch.object(share_session, "load_refresh_token", return_value="refresh"),
            patch.object(share_session, "run_refresh", return_value="fresh") as refresh_mock,
            patch.object(share_session, "upload_share", upload_mock),
            patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("LOVSTUDIO_ACCESS_TOKEN", None)
            os.environ.pop("YODA_ACCESS_TOKEN", None)
            result = share_session.upload_with_auth_retry({"kind": "demo"}, args)
        self.assertEqual(result["url"], "https://lovstudio.ai/s/demo")
        refresh_mock.assert_called_once_with(
            "https://lovstudio.ai", "refresh", 60, Path("/tmp/profile.json")
        )
        self.assertEqual(
            upload_mock.call_args_list,
            [
                call({"kind": "demo"}, "stale", "https://lovstudio.ai", 60),
                call({"kind": "demo"}, "fresh", "https://lovstudio.ai", 60),
            ],
        )


if __name__ == "__main__":
    unittest.main()
