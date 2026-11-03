from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
AUDIT_SCRIPTS = (
    ROOT / "scripts" / "audit_bp.py",
    ROOT / "skills" / "bp-polish" / "scripts" / "audit_bp.py",
)
TEMPLATE = ROOT / "skills" / "bp-outline" / "assets" / "templates" / "outline.md"
FINANCING_SLIDE = """
## Slide 16 — 融资计划

Headline: 本轮融资 ¥500 万，用 18 个月验证四城复制
Use of funds: 讲师认证 40%｜软件付费版 35%｜运营 25%
Milestones: 18 个月内四城每月开班、软件付费用户 300
Evidence: E-020
Visual: 资金用途环形图 + 里程碑闸门
"""


def run_audit(script: Path, outline: Path, *extra: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(script), "--input", str(outline), "--format", "json", *extra],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class AuditScopeTests(unittest.TestCase):
    def test_root_copy_matches_the_polish_module(self) -> None:
        root_copy, module_copy = AUDIT_SCRIPTS
        self.assertEqual(root_copy.read_bytes(), module_copy.read_bytes())

    def test_preamble_and_closing_notes_earn_no_financing_credit(self) -> None:
        # v0.4 scored 10/10: the change notes name 融资/资金用途/里程碑 and the
        # closing slide says 不设融资页, yet the deck has no financing slide.
        for script in AUDIT_SCRIPTS:
            with self.subTest(script=str(script.relative_to(ROOT))):
                result = run_audit(script, FIXTURES / "outline-v0.4-closing-page.md")
                self.assertEqual(result["scorecard"]["financing_delivery"], 0)
                self.assertEqual(result["missing_beats"], ["financing"])
                self.assertIn("No clear financing ask.", result["blockers"])

    def test_financial_projection_is_not_a_financing_slide(self) -> None:
        # v0.5 scored 7/10 from the preamble and the SOM line "18–24 个月".
        for script in AUDIT_SCRIPTS:
            with self.subTest(script=str(script.relative_to(ROOT))):
                result = run_audit(script, FIXTURES / "outline-v0.5-standard-order.md")
                self.assertEqual(result["scorecard"]["financing_delivery"], 0)
                self.assertEqual(result["missing_beats"], ["financing"])
                self.assertIn("No clear financing ask.", result["blockers"])

    def test_why_now_is_recognised_without_an_english_gloss(self) -> None:
        result = run_audit(AUDIT_SCRIPTS[1], FIXTURES / "outline-v0.5-standard-order.md")
        self.assertIn("why now", result["coverage"])

    def test_a_financing_slide_earns_delivery_only_with_an_amount(self) -> None:
        source = (FIXTURES / "outline-v0.5-standard-order.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "outline.md"
            outline.write_text(source + FINANCING_SLIDE, encoding="utf-8")
            result = run_audit(AUDIT_SCRIPTS[1], outline, "--max-slides", "16")
            self.assertEqual(result["scorecard"]["financing_delivery"], 10)
            self.assertEqual(result["missing_beats"], [])
            self.assertEqual(result["blockers"], [])

            outline.write_text(source + FINANCING_SLIDE.replace("¥500 万", "金额另议"), encoding="utf-8")
            result = run_audit(AUDIT_SCRIPTS[1], outline, "--max-slides", "16")
            self.assertEqual(result["scorecard"]["financing_delivery"], 6)
            self.assertIn("The financing slide states no amount.", result["blockers"])

    def test_ascii_terms_match_whole_words(self) -> None:
        slides = "\n".join(
            f"## Slide {number} — {title}\n\nHeadline: x\nEvidence: E-1\nVisual: y\n"
            for number, title in enumerate(("Go-to-market", "Same-day demo"), start=1)
        )
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "outline.md"
            outline.write_text(slides, encoding="utf-8")
            coverage = run_audit(AUDIT_SCRIPTS[1], outline)["coverage"]
        self.assertEqual(coverage, ["product demo", "growth"])

    def test_the_outline_template_names_all_twelve_beats(self) -> None:
        result = run_audit(AUDIT_SCRIPTS[1], TEMPLATE)
        self.assertEqual(result["missing_beats"], [])


if __name__ == "__main__":
    unittest.main()
