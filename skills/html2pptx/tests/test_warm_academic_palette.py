from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("edit_html", ROOT / "scripts" / "edit_html.py")
EDIT_HTML = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EDIT_HTML)

WARM_ACADEMIC_PRIMARY = "#CC785C"
SANITIZER_PLACEHOLDER = "#4F46E5"


class WarmAcademicPaletteTests(unittest.TestCase):
    def test_editor_uses_terracotta_primary(self) -> None:
        self.assertIn(f"--primary: {WARM_ACADEMIC_PRIMARY};", EDIT_HTML.EDITOR_HTML)
        self.assertNotIn(SANITIZER_PLACEHOLDER, EDIT_HTML.EDITOR_HTML)

    def test_starter_deck_uses_terracotta_accents(self) -> None:
        starter = EDIT_HTML._starter_html()
        self.assertEqual(starter.count(WARM_ACADEMIC_PRIMARY), 2)
        self.assertNotIn(SANITIZER_PLACEHOLDER, starter)

    def test_reference_deck_uses_terracotta_accents(self) -> None:
        example = (ROOT / "references" / "example.html").read_text(encoding="utf-8")
        self.assertIn(WARM_ACADEMIC_PRIMARY, example)
        self.assertNotIn(SANITIZER_PLACEHOLDER, example)


if __name__ == "__main__":
    unittest.main()
