#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from voice2srt import Chunk, Cue, canonicalize_text, dashscope_events_to_cues, extract_openless_dashscope, extract_openless_volcengine, load_vocabulary, normalize_cues, srt_timestamp, validate_cues, whisper_output_path


class Voice2SrtTests(unittest.TestCase):
    def test_openless_and_canonical_vocabulary_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            openless = root / "openless.json"
            openless.write_text(json.dumps([
                {"phrase": "OpenLess", "enabled": True},
                {"phrase": "openless", "enabled": True},
                {"phrase": "disabled", "enabled": False},
            ]), encoding="utf-8")
            canonical = root / "canonical.json"
            canonical.write_text(json.dumps({"entries": [
                {"phrase": "LovStudio", "enabled": True},
            ]}), encoding="utf-8")
            self.assertEqual(load_vocabulary(openless), ["OpenLess"])
            self.assertEqual(load_vocabulary(canonical), ["LovStudio"])

    def test_extract_channelized_openless_credentials(self) -> None:
        root = {
            "active": {"asr": "channel-a"},
            "providers": {"asr": {"channel-a": {
                "providerType": "volcengine",
                "authMode": "api_key",
                "volcengineApiKey": "secret",
            }}},
        }
        result = extract_openless_volcengine(root)
        self.assertEqual(result["auth_mode"], "api_key")
        self.assertEqual(result["api_key"], "secret")

    def test_extract_legacy_key_with_channel_provider_type(self) -> None:
        root = {
            "active": {"asr": "volcengine"},
            "providers": {"asr": {"volcengine": {
                "providerType": "bailian-qwen3-realtime",
                "apiKey": "secret",
                "model": "qwen3-asr-flash-realtime",
            }}},
        }
        result = extract_openless_dashscope(root)
        self.assertEqual(result["provider_type"], "bailian-qwen3-realtime")
        self.assertEqual(result["api_key"], "secret")

    def test_normalize_cues_removes_overlap_and_duplicates(self) -> None:
        cues = normalize_cues([
            Cue(100, 1000, " hello  world ", 0),
            Cue(900, 1500, "Next", 0),
            Cue(1550, 1800, "Next", 1),
        ], 2000)
        self.assertEqual([cue.text for cue in cues], ["hello world", "Next"])
        self.assertEqual(cues[0].end_ms, 900)
        self.assertTrue(validate_cues(cues, 2000)["ok"])

    def test_srt_timestamp(self) -> None:
        self.assertEqual(srt_timestamp(3_723_004), "01:02:03,004")

    def test_dashscope_cumulative_events_become_incremental_cues(self) -> None:
        events = [
            {"output": {"sentence": {"sentence_end": True, "text": "第一句。", "words": [
                {"text": "第一句", "punctuation": "。", "begin_time": 100, "end_time": 900}
            ]}}},
            {"output": {"sentence": {"sentence_end": True, "text": "第一句。第二句。", "words": [
                {"text": "第一句", "punctuation": "。", "begin_time": 100, "end_time": 900},
                {"text": "第二句", "punctuation": "。", "begin_time": 1200, "end_time": 2000}
            ]}}},
        ]
        cues = dashscope_events_to_cues(events, Chunk(2, 480000, 240000, Path("x.mp3")))
        self.assertEqual([cue.text for cue in cues], ["第一句。", "第二句。"]) 
        self.assertEqual(cues[1].start_ms, 481200)

    def test_canonicalize_ascii_vocabulary_casing(self) -> None:
        self.assertEqual(
            canonicalize_text("openless 和 typeless", ["OpenLess", "Typeless"]),
            "OpenLess 和 Typeless",
        )

    def test_whisper_output_path_appends_format_suffix(self) -> None:
        self.assertEqual(
            whisper_output_path(Path("chunk-000.whisper"), ".json"),
            Path("chunk-000.whisper.json"),
        )


if __name__ == "__main__":
    unittest.main()
