from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from publish_blog_post import build_payload, inline_image_sources  # noqa: E402


def publishing_args(**overrides: object) -> SimpleNamespace:
    values = {
        "title": "Inline media test",
        "slug": "inline-media-test",
        "excerpt": "Test excerpt",
        "tags": "dev,blog",
        "author": "Mark",
        "cover": "https://example.com/cover.webp",
        "published_at": "",
        "source_kind": "dev-skill",
        "source_path": "",
        "draft": False,
        "hide_from_index": False,
        "require_inline_image": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class PublishBlogPostMediaTests(unittest.TestCase):
    def test_extracts_markdown_and_html_images(self) -> None:
        content = (
            "![Screenshot](https://example.com/screenshot.webp)\n"
            '<img src="https://example.com/diagram.svg" alt="Diagram" />'
        )
        self.assertEqual(
            inline_image_sources(content),
            [
                "https://example.com/screenshot.webp",
                "https://example.com/diagram.svg",
            ],
        )

    def test_requires_inline_image_when_requested(self) -> None:
        with self.assertRaisesRegex(SystemExit, "has no Markdown or HTML image"):
            build_payload(publishing_args(require_inline_image=True), "# Post\n\nText only.")

    def test_rejects_local_inline_image_for_public_post(self) -> None:
        content = "![Local screenshot](./assets/screenshot.webp)"
        with self.assertRaisesRegex(SystemExit, "public HTTP\\(S\\) URLs"):
            build_payload(publishing_args(), content)

    def test_accepts_public_inline_image(self) -> None:
        content = "![Published screenshot](https://example.com/screenshot.webp)"
        payload = build_payload(publishing_args(require_inline_image=True), content)
        self.assertEqual(payload["content_mdx"], content)


if __name__ == "__main__":
    unittest.main()
