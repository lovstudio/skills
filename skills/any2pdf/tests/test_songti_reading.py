#!/usr/bin/env python3
"""Focused regressions for the Songti + sans hierarchy reading theme."""

import importlib.util
from pathlib import Path
import unittest


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


if __name__ == "__main__":
    unittest.main()
