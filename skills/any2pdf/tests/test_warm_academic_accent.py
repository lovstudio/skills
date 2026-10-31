#!/usr/bin/env python3
"""Regressions for the Warm Academic accent restored after the 2026-08-09 sanitizer."""

import importlib.util
import inspect
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "md2pdf.py"
SPEC = importlib.util.spec_from_file_location("any2pdf_md2pdf_warm_academic", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def to_hex(color):
    return f"#{int(color.red * 255):02X}{int(color.green * 255):02X}{int(color.blue * 255):02X}"


class WarmAcademicAccentTests(unittest.TestCase):
    def test_builtin_theme_accent_is_terracotta(self):
        self.assertEqual(MODULE.THEMES["warm-academic"]["accent"], "#CC785C")
        self.assertEqual(to_hex(MODULE.load_theme("warm-academic")["accent"]), "#CC785C")

    def test_inline_markup_defaults_to_terracotta(self):
        default = inspect.signature(MODULE.md_inline).parameters["accent_hex"].default
        self.assertEqual(default, "#CC785C")

    def test_no_sanitizer_placeholder_left_in_renderer(self):
        self.assertEqual(SCRIPT.read_text(encoding="utf-8").upper().count("#4F46E5"), 0)


if __name__ == "__main__":
    unittest.main()
