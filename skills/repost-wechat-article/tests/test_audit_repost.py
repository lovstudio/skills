from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_repost.py"
SPEC = importlib.util.spec_from_file_location("audit_repost", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AuditRepostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_text = "合作方 原文。"
        self.html = (
            '<section data-repost-block="publisher-intro">开场</section>'
            '<p><a href="https://mp.weixin.qq.com/s/example">来源</a></p>'
            '<section data-repost-source="true" data-source-account="来源号">'
            '合作方 原文。<img data-src="https://mmbiz.qpic.cn/example">'
            "</section>"
            '<section data-repost-block="publisher-outro">收尾</section>'
        )

    def inspect(self, html: str):
        return MODULE.inspect_html(
            html=html,
            source_text=self.source_text,
            source_account="来源号",
            source_url="https://mp.weixin.qq.com/s/example",
            required_blocks=[
                '[data-repost-block="publisher-intro"]',
                '[data-repost-block="publisher-outro"]',
            ],
            expected_source_images=1,
            label="test",
        )

    def test_accepts_source_faithful_edition(self) -> None:
        result = self.inspect(self.html)
        self.assertTrue(result["valid"])
        self.assertEqual(result["sourceImageCount"], 1)

    def test_rejects_changed_source_text(self) -> None:
        result = self.inspect(self.html.replace("合作方 原文。", "被改写的原文。"))
        self.assertFalse(result["valid"])
        self.assertIn("source visible text differs", result["errors"][0])

    def test_rejects_duplicate_editorial_block(self) -> None:
        duplicate = self.html + '<section data-repost-block="publisher-outro">重复</section>'
        result = self.inspect(duplicate)
        self.assertFalse(result["valid"])
        self.assertTrue(any("expected once" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

