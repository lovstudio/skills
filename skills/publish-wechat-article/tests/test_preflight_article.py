from __future__ import annotations

import sys
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from PIL import Image


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from preflight_article import analyze_article  # noqa: E402


class PreflightArticleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cover = self.root / "cover.jpg"
        self.cover.write_bytes(b"cover")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_accepts_simple_markdown_and_infers_title(self) -> None:
        source = self.root / "article.md"
        source.write_text("# 生命的意义在于创作\n\n正文。\n", encoding="utf-8")

        report = analyze_article(source, self.cover)

        self.assertTrue(report["ok"])
        self.assertEqual(report["title"], "生命的意义在于创作")
        self.assertEqual(report["titleOrigin"], "markdown_h1")

    def test_blocks_oneshot_when_body_contains_image(self) -> None:
        image = self.root / "body.png"
        image.write_bytes(b"image")
        source = self.root / "article.md"
        source.write_text("# 标题\n\n![正文图](body.png)\n", encoding="utf-8")

        report = analyze_article(source, self.cover, transport="oneshot")

        self.assertFalse(report["ok"])
        self.assertTrue(any("只上传封面" in item for item in report["errors"]))

    def test_warns_that_remote_images_need_rewriting(self) -> None:
        source = self.root / "article.md"
        source.write_text("# 标题\n\n![图](https://example.com/image.png)\n", encoding="utf-8")

        report = analyze_article(source, self.cover, transport="auto")

        self.assertTrue(report["ok"])
        self.assertEqual(report["remoteImageCount"], 1)
        self.assertTrue(any("media/uploadimg" in item for item in report["warnings"]))

    def test_detects_markdown_reference_and_inline_html_images(self) -> None:
        reference = self.root / "reference.png"
        inline_html = self.root / "inline.jpg"
        reference.write_bytes(b"image")
        inline_html.write_bytes(b"image")
        source = self.root / "article.md"
        source.write_text(
            "# 标题\n\n![引用图][hero]\n\n<img src=\"inline.jpg\" alt=\"内嵌图\">\n\n"
            "[hero]: reference.png \"封面\"\n",
            encoding="utf-8",
        )

        report = analyze_article(source, self.cover, transport="oneshot")

        self.assertFalse(report["ok"])
        self.assertEqual(report["localImageCount"], 2)
        self.assertEqual(
            {Path(item["path"]).name for item in report["images"]},
            {"reference.png", "inline.jpg"},
        )

    def test_rejects_field_limits(self) -> None:
        source = self.root / "article.txt"
        source.write_text("正文", encoding="utf-8")

        report = analyze_article(
            source,
            self.cover,
            title="题" * 33,
            author="作" * 17,
            digest="摘" * 121,
        )

        self.assertFalse(report["ok"])
        self.assertEqual(len(report["errors"]), 3)

    def test_large_source_is_deferred_to_rendered_content_validation(self) -> None:
        source = self.root / "article.md"
        source.write_text("# 标题\n\n" + "<!-- padding -->" * 2_000 + "正文", encoding="utf-8")

        report = analyze_article(source, self.cover)

        self.assertTrue(report["ok"])
        self.assertTrue(any("不按原始 HTML/Markdown 计数" in item for item in report["warnings"]))

    def test_reports_file_read_errors_without_traceback(self) -> None:
        source = self.root / "article.md"
        source.write_text("# 标题\n", encoding="utf-8")

        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            report = analyze_article(source, self.cover)

        self.assertFalse(report["ok"])
        self.assertTrue(any("读取正文文件失败" in item for item in report["errors"]))

    def test_requires_upstream_artifacts_when_requested(self) -> None:
        source = self.root / "article.md"
        source.write_text("# 标题\n\n正文。\n", encoding="utf-8")

        report = analyze_article(
            source,
            self.cover,
            require_lovpen=True,
            require_composed_cover=True,
        )

        self.assertFalse(report["ok"])
        self.assertTrue(any("--lovpen-wechat-html" in item for item in report["errors"]))
        self.assertTrue(any("--cover-composition-receipt" in item for item in report["errors"]))

    def test_requires_independent_4x3_body_hero_for_normal_publish(self) -> None:
        hero = self.root / "hero.jpg"
        Image.new("RGB", (1600, 1200), "white").save(hero)
        source = self.root / "article.md"
        source.write_text("# 标题\n\n![正文首图](hero.jpg)\n\n导语。\n", encoding="utf-8")

        report = analyze_article(source, self.cover, require_body_hero=True)

        self.assertTrue(report["ok"])
        self.assertTrue(report["bodyHeroVerified"])
        self.assertEqual(report["bodyHero"]["width"], 1600)
        self.assertEqual(report["bodyHero"]["height"], 1200)

    def test_rejects_missing_or_portrait_body_hero(self) -> None:
        portrait = self.root / "portrait.jpg"
        Image.new("RGB", (1200, 1600), "white").save(portrait)
        missing = self.root / "missing.md"
        missing.write_text("# 标题\n\n导语。\n", encoding="utf-8")
        wrong_ratio = self.root / "wrong-ratio.md"
        wrong_ratio.write_text("# 标题\n\n![正文首图](portrait.jpg)\n\n导语。\n", encoding="utf-8")

        missing_report = analyze_article(missing, self.cover, require_body_hero=True)
        ratio_report = analyze_article(wrong_ratio, self.cover, require_body_hero=True)

        self.assertFalse(missing_report["ok"])
        self.assertTrue(any("正文第一块" in item for item in missing_report["errors"]))
        self.assertFalse(ratio_report["ok"])
        self.assertTrue(any("4:3" in item for item in ratio_report["errors"]))

    def test_rejects_incomplete_benchmark_article(self) -> None:
        source = self.root / "benchmark.md"
        source.write_text("# 我调研了去 AI 味 Prompt\n\n## 测试结果\n\n第一名。\n", encoding="utf-8")

        report = analyze_article(source, self.cover)

        self.assertFalse(report["ok"])
        self.assertTrue(any("测试方法" in item for item in report["errors"]))

    def test_validates_profile_driven_editorial_components(self) -> None:
        card = self.root / "card.jpg"
        card.write_bytes(b"card")
        profile = self.root / "brand.json"
        profile.write_text(
            json.dumps(
                {
                    "blocks": {
                        "endcap": {
                            "enabled": True,
                            "title": "关于手工川",
                            "paragraphs": ["长期介绍。"],
                            "links": [{"url": "https://example.com/about"}],
                            "card": {"asset": str(card), "marker": "个人介绍卡片"},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        source = self.root / "article.md"
        source.write_text(
            "# 标题\n\n## 关于手工川\n\n长期介绍。\n\n"
            '<img src="card.jpg" aria-label="个人介绍卡片">\n\n'
            "https://example.com/about\n",
            encoding="utf-8",
        )

        report = analyze_article(source, self.cover, brand_profile=profile)

        self.assertTrue(report["ok"])
        self.assertTrue(report["publicationComponentsVerified"])


if __name__ == "__main__":
    unittest.main()
