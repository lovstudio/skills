#!/usr/bin/env python3
"""Regressions for content-adaptive theme selection."""

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "md2pdf.py"
SPEC = importlib.util.spec_from_file_location("any2pdf_md2pdf_adaptive", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AdaptiveThemeTests(unittest.TestCase):
    def test_strategy_report_uses_consulting_theme(self):
        markdown = "# 行业研究\n\n这是一份市场研究与经营分析报告。"
        self.assertEqual(
            MODULE.select_theme_from_content(markdown),
            "consulting-navy",
        )

    def test_code_heavy_document_uses_github_theme(self):
        markdown = """# Python API 指南

```python
print("hello")
```

```bash
python app.py
```
"""
        self.assertEqual(
            MODULE.select_theme_from_content(markdown),
            "github-light",
        )

    def test_literary_document_uses_ink_wash_theme(self):
        markdown = "# 山中随笔\n\n这是一篇关于诗歌、文学与东方美学的散文。"
        self.assertEqual(
            MODULE.select_theme_from_content(markdown),
            "ink-wash",
        )

    def test_neutral_chinese_prose_uses_reading_theme(self):
        markdown = "# 日常记录\n\n今天整理了房间，也重新安排了下周的工作。"
        self.assertEqual(
            MODULE.select_theme_from_content(markdown),
            "songti-reading",
        )

    def test_neutral_english_prose_uses_paper_theme(self):
        markdown = "# Field Notes\n\nA short reflection on a quiet afternoon."
        self.assertEqual(
            MODULE.select_theme_from_content(markdown),
            "paper-classic",
        )

    def test_ascii_keywords_do_not_match_inside_words(self):
        markdown = "# Capital Notes\n\nA short reflection on capital allocation."
        self.assertEqual(
            MODULE.select_theme_from_content(markdown),
            "paper-classic",
        )


if __name__ == "__main__":
    unittest.main()
