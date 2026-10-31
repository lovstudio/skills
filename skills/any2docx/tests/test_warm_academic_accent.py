#!/usr/bin/env python3
"""Regression for the Warm Academic accent restored after the 2026-08-09 sanitizer."""

import contextlib
import importlib.util
import io
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "md2docx.py"
SPEC = importlib.util.spec_from_file_location("any2docx_md2docx_warm_academic", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class WarmAcademicAccentTests(unittest.TestCase):
    def test_builtin_theme_accent_is_terracotta(self):
        self.assertEqual(MODULE.THEMES["warm-academic"]["accent"], "#CC785C")
        self.assertEqual(MODULE.load_theme("warm-academic")["accent"], MODULE._hex_to_rgb("#CC785C"))

    def test_unknown_theme_falls_back_to_terracotta(self):
        with contextlib.redirect_stderr(io.StringIO()):
            theme = MODULE.load_theme("missing-theme")
        self.assertEqual(theme["accent"], MODULE._hex_to_rgb("#CC785C"))


if __name__ == "__main__":
    unittest.main()
