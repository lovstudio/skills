import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "find_ai_file.py"
SPEC = importlib.util.spec_from_file_location("find_ai_file", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FindAiFileTests(unittest.TestCase):
    def test_extracts_visible_message_paths_but_not_system_payloads(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "output" / "portrait.png"
            output.parent.mkdir()
            output.write_bytes(b"png")
            transcript = root / "rollout-session-123.jsonl"
            rows = [
                {"type": "session_meta", "payload": {"id": "session-123", "cwd": str(root)}},
                {"type": "response_item", "payload": {"type": "message", "role": "developer", "content": [{"text": "/tmp/noise.png"}]}},
                {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"text": "帮我修一下头像"}]}},
                {"type": "response_item", "payload": {"type": "message", "role": "assistant", "phase": "final_answer", "content": [{"text": f"成品：[图片](<{output}>)"}]}},
            ]
            transcript.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

            record = MODULE.parse_transcript(transcript, root)
            paths = [item["path"] for item in record["mentions"]]
            self.assertIn(str(output), paths)
            self.assertNotIn("/tmp/noise.png", paths)
            self.assertGreater(MODULE.relevance_score(record, "P 头像", *MODULE.query_terms("P 头像"), ""), 0)

    def test_kind_inference_and_temporary_durability(self):
        self.assertEqual(MODULE.infer_kind("上次 P 的头像", "auto"), "image")
        self.assertEqual(MODULE.durability("/tmp/result.png", Path.home())[0], "temporary")
        exact, aliases = MODULE.query_terms("P 头像")
        self.assertEqual(MODULE.prefilter_terms(exact, aliases), ["头像", "p图", "修图", "形象照", "磨皮"])

    def test_session_id_is_a_hard_transcript_constraint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wanted = root / "rollout-session-123.jsonl"
            unrelated = root / "rollout-session-999.jsonl"
            wanted.write_text("头像", encoding="utf-8")
            unrelated.write_text("头像", encoding="utf-8")
            hits = MODULE.find_candidate_transcripts([root], ["头像"], "session-123", 20)
            self.assertEqual(hits, [wanted])

    def test_prefilter_ignores_developer_only_matches(self):
        if MODULE.shutil.which("rg") is None:
            self.skipTest("ripgrep unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            visible = root / "visible.jsonl"
            noise = root / "noise.jsonl"
            visible.write_text('{"role":"user","content":"帮我找头像"}\n', encoding="utf-8")
            noise.write_text('{"role":"developer","content":"头像"}\n', encoding="utf-8")
            hits = MODULE.find_candidate_transcripts([root], ["头像"], "", 20)
            self.assertEqual(hits, [visible])


if __name__ == "__main__":
    unittest.main()
