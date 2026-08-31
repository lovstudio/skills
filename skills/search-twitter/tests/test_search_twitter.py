import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import search_twitter as twitter


class DiscoveryTest(unittest.TestCase):
    def test_extracts_and_deduplicates_status_urls(self):
        result = twitter.discover_references(
            "See https://twitter.com/Test_User/status/123 and "
            "https://x.com/Test_User/status/123 plus https://t.co/AbC9"
        )
        self.assertEqual(len(result["posts"]), 1)
        self.assertEqual(result["posts"][0]["status_id"], "123")
        self.assertEqual(result["posts"][0]["url"], "https://x.com/Test_User/status/123")
        self.assertEqual(result["short_urls"], ["https://t.co/AbC9"])


class ExtractionTest(unittest.TestCase):
    def test_prefers_open_graph_description(self):
        body = b'<meta property="og:description" content="full public post">'
        self.assertEqual(twitter.parse_post_text(body), ("full public post", "meta:og:description"))

    def test_extracts_embedded_json(self):
        body = b'<script>{"full_text":"line one\\nline two"}</script>'
        self.assertEqual(twitter.parse_post_text(body), ("line one\nline two", "embedded-json"))

    def test_empty_archive_shell_is_not_recovered(self):
        self.assertEqual(twitter.parse_post_text(b"<div id='react-root'></div>"), (None, None))


class ReconciliationTest(unittest.TestCase):
    def test_two_renderer_match_allows_url_expansion(self):
        text, confidence, variants = twitter.select_text(
            [
                {"ok": True, "text": "post https://t.co/a end"},
                {"ok": True, "text": "post https://example.com/long end"},
            ]
        )
        self.assertEqual(text, "post https://example.com/long end")
        self.assertEqual(confidence, "two-renderer-match")
        self.assertEqual(len(variants), 2)

    def test_conflicting_text_remains_conflict(self):
        _, confidence, variants = twitter.select_text(
            [{"ok": True, "text": "alpha"}, {"ok": True, "text": "beta"}]
        )
        self.assertEqual(confidence, "conflict")
        self.assertEqual(variants, ["alpha", "beta"])

    def test_unrecovered_without_text(self):
        self.assertEqual(twitter.select_text([]), (None, "unrecovered", []))


class RendererTest(unittest.TestCase):
    def test_success_message_is_not_reported_as_error(self):
        original = twitter.safe_request_json
        twitter.safe_request_json = lambda endpoint, timeout: (
            {
                "message": "OK",
                "tweet": {
                    "text": "public post",
                    "created_at": "date",
                    "author": {"screen_name": "example"},
                },
            },
            None,
        )
        try:
            result = twitter.fetch_fx("example", "123", 1)
        finally:
            twitter.safe_request_json = original
        self.assertTrue(result["ok"])
        self.assertIsNone(result["error"])


class EvidenceTest(unittest.TestCase):
    def test_screenshot_hash_and_ocr_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "evidence.png"
            image.write_bytes(b"stable-image-bytes")
            ocr = root / "evidence.txt"
            ocr.write_text("derived OCR", encoding="utf-8")
            record = twitter.screenshot_evidence(
                Namespace(
                    image=str(image),
                    kind="screenshot_copy",
                    source_url="https://example.org/source",
                    ocr_file=str(ocr),
                    parent_sha256=None,
                    truncated=True,
                    notes="fixture",
                )
            )
            self.assertEqual(record["provenance"], "screenshot_copy")
            self.assertEqual(record["confidence"], "partial")
            self.assertTrue(record["ocr_is_derived"])
            self.assertEqual(len(record["sha256"]), 64)


class ArchiveTest(unittest.TestCase):
    def test_builds_capture_from_cdx_row(self):
        capture = twitter.capture_from_row(
            [
                "20260201090444",
                "https://x.com/example/status/2017798141492539642",
                "text/html",
                "200",
                "digest",
            ]
        )
        self.assertIsNotNone(capture)
        assert capture is not None
        self.assertEqual(capture.timestamp, "20260201090444")
        self.assertTrue(capture.archive_url.endswith("/2017798141492539642"))


if __name__ == "__main__":
    unittest.main()
