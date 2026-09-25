#!/usr/bin/env python3
"""Focused regressions for the Songti + sans hierarchy reading theme."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "md2pdf.py"
SPEC = importlib.util.spec_from_file_location("any2pdf_md2pdf", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SongtiReadingThemeTests(unittest.TestCase):
    def test_theme_preserves_reading_contract(self):
        theme = MODULE.load_theme("songti-reading")
        layout = theme["layout"]
        self.assertEqual(layout["body_font"], "Serif")
        self.assertEqual(layout["heading_font"], "SansBold")
        self.assertEqual(layout["cjk_bold_style"], "sans")
        self.assertEqual(layout["table_body_font"], "Serif")
        self.assertTrue(layout["continuous_headings"])
        self.assertTrue(layout["fit_width_on_open"])

    def test_songti_regular_is_not_black_face(self):
        self.assertEqual(
            MODULE._FONT_CANDIDATES["CJK"][0],
            ("/System/Library/Fonts/Supplemental/Songti.ttc", 6),
        )

    def test_bold_cjk_and_common_symbols_use_explicit_roles(self):
        wrapped = MODULE._font_wrap("<b>当前状态</b> ✓ ✗ →")
        self.assertIn("name='CJKBold'", wrapped)
        self.assertEqual(wrapped.count("name='Symbols'"), 3)

    def test_all_cover_styles_route_cjk_version_through_mixed_renderer(self):
        class CanvasStub:
            def setFillColor(self, *_args): pass
            def rect(self, *_args, **_kwargs): pass
            def setStrokeColor(self, *_args): pass
            def setLineWidth(self, *_args): pass
            def line(self, *_args): pass

        version = "微信读书投稿审阅版 v0.1"
        builder = MODULE.PDFBuilder({
            "theme": MODULE.load_theme("elegant-book"),
            "page_size": MODULE.A4,
            "title": "Agent Skill 高质量设计指南",
            "version": version,
            "date": "2026-08-27",
        })

        for method_name in ("_cover_centered", "_cover_left_aligned", "_cover_minimal"):
            calls = []

            def draw_mixed(_canvas, _x, y, text, _size, **_kwargs):
                calls.append(text)
                return y

            with self.subTest(method=method_name), patch.object(MODULE, "_draw_mixed", side_effect=draw_mixed):
                getattr(builder, method_name)(CanvasStub(), builder.T, builder.page_w / 2)
                self.assertIn(version, calls)

    def test_image_syntax_inside_inline_code_is_not_rendered_as_an_image(self):
        line = '当读到 `"Add ![Version](https://img.shields.io/badge/version-X.Y.Z)"` 时保留原文。'
        self.assertFalse(MODULE._has_markdown_image(line))
        self.assertTrue(MODULE._has_markdown_image('正文图片：![架构图](assets/diagram.png)'))


if __name__ == "__main__":
    unittest.main()
