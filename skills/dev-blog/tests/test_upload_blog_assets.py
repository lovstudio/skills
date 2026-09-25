from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from upload_blog_assets import build_records, normalize_filename, validate_slug  # noqa: E402


class UploadBlogAssetsTests(unittest.TestCase):
    def test_validates_blog_slug(self) -> None:
        self.assertEqual(validate_slug("inline-media-test"), "inline-media-test")
        with self.assertRaisesRegex(SystemExit, "kebab-case"):
            validate_slug("Inline Media Test")

    def test_normalizes_ascii_filename(self) -> None:
        self.assertEqual(
            normalize_filename(Path("01 Problem Overview.WEBP"), 1),
            "01-problem-overview.webp",
        )

    def test_builds_deterministic_public_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "01 Problem.webp"
            path.write_bytes(b"fixture")
            records = build_records(
                [path],
                "https://example.supabase.co",
                "app-assets",
                "blog-images",
                "inline-media-test",
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["object_path"],
            "blog-images/inline-media-test/01-problem.webp",
        )
        self.assertEqual(
            records[0]["public_url"],
            "https://example.supabase.co/storage/v1/object/public/"
            "app-assets/blog-images/inline-media-test/01-problem.webp",
        )
        self.assertEqual(records[0]["content_type"], "image/webp")
        self.assertEqual(records[0]["bytes"], 7)


if __name__ == "__main__":
    unittest.main()
