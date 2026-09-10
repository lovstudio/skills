#!/usr/bin/env python3
"""Deterministic tests for the mobile info card CLI.

These cover template assembly, brand resolution, canvas math, and the audit
scoring rules. Browser-dependent checks stay in the Skill workflow because they
need Playwright and a real render.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import infographic_cli as cli  # noqa: E402


def good_measurement(**overrides):
    measurement = {
        "canvas": {
            "w": 1080,
            "h": 1440,
            "ratio": "3:4",
            "template": "single-claim",
            "series_index": "1",
            "series_size": "1",
            "background": "rgb(247, 244, 239)",
        },
        "text_entries": [
            {"role": "title", "text": "标题", "font_size": 72, "font_weight": "700",
             "contrast": 12.0, "lines": [8], "max_units": 8, "rect": {"x": 88, "y": 96, "w": 900, "h": 90}},
            {"role": "body", "text": "正文", "font_size": 40, "font_weight": "450",
             "contrast": 7.0, "lines": [18], "max_units": 18, "rect": {"x": 88, "y": 300, "w": 900, "h": 60}},
        ],
        "overflow": [],
        "out_of_bounds": [],
        "safe_violations": [],
        "counts": {
            "claims": 1,
            "sources": 3,
            "encodings": 1,
            "encodings_linked": 1,
            "annotations": 1,
            "skeletons": 0,
            "blocks": 2,
        },
        "logo": {"present": True, "natural_w": 320, "natural_h": 109},
        "attribution": "Powered by · lovstudio.ai/skills/mobile-infographic",
        "page_mark": "1/3",
        "visible_text_length": 120,
        "title": "标题",
    }
    measurement.update(overrides)
    return measurement


class CanvasMathTests(unittest.TestCase):
    def test_ratios_use_fixed_1080_width(self):
        for ratio, (width, height) in cli.RATIOS.items():
            self.assertEqual(width, 1080, ratio)
            if ratio == "long":
                self.assertEqual(height, 0, ratio)
            else:
                self.assertGreaterEqual(height, width, ratio)

    def test_page_mark(self):
        self.assertEqual(cli.page_mark(2, 3), "2/3")
        self.assertEqual(cli.page_mark(1, 1), "1/1")

    def test_png_size_reads_case_asset(self):
        asset = cli.SKILL_ROOT / "cases" / "assets" / "harness-action-guide-01.png"
        self.assertEqual(cli.png_size(asset), (2160, 2880))


class TemplateAssemblyTests(unittest.TestCase):
    def test_every_template_renders_without_leftover_tokens(self):
        brand = json.loads((cli.ASSETS_DIR / "brand-profile.json").read_text(encoding="utf-8"))
        for template in cli.TEMPLATES:
            html = cli.build_card_html(
                template=template,
                ratio="3:4",
                title="标题",
                claim="结论",
                eyebrow="标签",
                source="来源",
                source_id="S1",
                brand=brand,
                series_index=1,
                series_size=3,
            )
            self.assertNotIn("{{", html, template)
            self.assertIn("data-card", html)
            self.assertIn('data-ratio="3:4"', html)
            self.assertIn('data-series-size="3"', html)
            self.assertEqual(html.count("data-claim"), 1, template)
            self.assertIn("data:image/png;base64,", html)

    def test_long_ratio_leaves_height_to_content(self):
        brand = json.loads((cli.ASSETS_DIR / "brand-profile.json").read_text(encoding="utf-8"))
        html = cli.build_card_html(
            template="single-claim",
            ratio="long",
            title="标题",
            claim="结论",
            eyebrow="标签",
            source="来源",
            source_id="S1",
            brand=brand,
            series_index=1,
            series_size=1,
        )
        self.assertIn("--canvas-height: 0px", html)

    def _build(self, brand: dict) -> str:
        return cli.build_card_html(
            template="single-claim",
            ratio="3:4",
            title="标题",
            claim="结论",
            eyebrow="标签",
            source="来源：群聊记录",
            source_id="S1",
            brand=brand,
            series_index=1,
            series_size=1,
        )

    def test_credit_link_is_opt_in_and_drops_scheme(self):
        brand = dict(json.loads((cli.ASSETS_DIR / "brand-profile.json").read_text(encoding="utf-8")))
        brand["credit_link"] = True
        html = self._build(brand)
        self.assertNotIn("https://lovstudio.ai", html)  # scheme is stripped
        self.assertIn("lovstudio.ai/skills/mobile-infographic", html)
        self.assertNotIn("<a href", html)  # a PNG cannot be clicked

    def test_default_footer_is_logo_only(self):
        # provenance lives in the appendix block, so the packaged footer stays empty
        brand = dict(json.loads((cli.ASSETS_DIR / "brand-profile.json").read_text(encoding="utf-8")))
        html = self._build(brand)
        self.assertIn('<span class="attribution" data-attribution></span>', html)

    def test_credit_can_be_omitted(self):
        brand = dict(json.loads((cli.ASSETS_DIR / "brand-profile.json").read_text(encoding="utf-8")))
        brand["credit"] = ""
        brand["credit_link"] = False
        html = self._build(brand)
        self.assertIn('<span class="attribution" data-attribution></span>', html)

    def test_bar_rows_become_bars_with_length_encoding(self):
        brand = dict(json.loads((cli.ASSETS_DIR / "brand-profile.json").read_text(encoding="utf-8")))
        html = cli.build_card_html(
            template="bar-ranking",
            ratio="long",
            title="最受欢迎的是继续做事的那类城",
            claim="前三类合计 41 人",
            eyebrow="调研",
            source="来源：群聊记录",
            source_id="S1",
            brand=brand,
            series_index=1,
            series_size=1,
            rows=cli.build_bar_rows(
                [
                    "01 新海|25|New Harbor · AI 进入工作|早＊ · 南艺 89|voice",
                    "04 新界|13|Nexus · 低税低监管|刘＊畅 · Cakinna|civic",
                ],
                "S1",
            ),
        )
        self.assertIn('data-encoding="长度 = 数值"', html)
        self.assertIn("bar-head", html)
        self.assertIn("bar-desc", html)
        self.assertIn("bar-note", html)
        self.assertIn('style="width:100.0%"', html)
        self.assertIn('style="width:52.0%"', html)
        self.assertIn("（25 人）", html)
        self.assertIn('bar-track"><span class="bar-fill" style="width:100.0%"></span></span>\n            <span class="bar-value"', html)
        # three stacked full-width lines: head, metric, roster (no side-by-side columns)
        self.assertNotIn("bar-line", html)
        self.assertNotIn("data-source-ref=\"{{SOURCE_ID}}\"", html)


class BrandResolutionTests(unittest.TestCase):
    def test_explicit_profile_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "brand.json"
            path.write_text(json.dumps({"name": "测试品牌", "accent": "#123456"}), encoding="utf-8")
            brand, origin = cli.resolve_brand(str(path))
            self.assertEqual(brand["name"], "测试品牌")
            self.assertEqual(brand["accent"], "#123456")
            self.assertTrue(origin.startswith("flag:"))

    def test_env_profile_is_used_when_no_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "brand.json"
            path.write_text(json.dumps({"name": "环境品牌"}), encoding="utf-8")
            os.environ["SKILL_MOBILE_INFOGRAPHIC_BRAND_PROFILE"] = str(path)
            try:
                brand, origin = cli.resolve_brand(None)
            finally:
                os.environ.pop("SKILL_MOBILE_INFOGRAPHIC_BRAND_PROFILE", None)
            self.assertEqual(brand["name"], "环境品牌")
            self.assertTrue(origin.startswith("env:"))

    def test_shared_profile_brand_scope_overrides_packaged_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            shared = Path(tmp) / "profile.json"
            shared.write_text(
                json.dumps({"brand": {"name": "共享品牌", "site": "https://example.com"}}),
                encoding="utf-8",
            )
            os.environ["SKILL_PROFILE_PATH"] = str(shared)
            try:
                brand, origin = cli.resolve_brand(None)
            finally:
                os.environ.pop("SKILL_PROFILE_PATH", None)
            self.assertEqual(brand["name"], "共享品牌")
            self.assertEqual(brand["site"], "https://example.com")
            self.assertTrue(origin.startswith("shared-profile:"))

    def test_logo_resolves_to_data_url(self):
        brand = json.loads((cli.ASSETS_DIR / "brand-profile.json").read_text(encoding="utf-8"))
        self.assertTrue(cli.logo_data_url(brand).startswith("data:image/png;base64,"))


class AuditScoringTests(unittest.TestCase):
    def audit(self, measurement, **kwargs):
        defaults = {"ratio_expected": cli.RATIOS["3:4"], "image_px": (2160, 2880), "scale": 2}
        defaults.update(kwargs)
        checks, _ = cli.audit_measurements(measurement, **defaults)
        return {check["id"]: check for check in checks}

    def test_clean_card_passes_every_check(self):
        checks = self.audit(good_measurement())
        failed = [check_id for check_id, check in checks.items() if check["status"] == "fail"]
        self.assertEqual(failed, [])

    def test_small_text_is_critical(self):
        measurement = good_measurement()
        measurement["text_entries"][1]["font_size"] = 24
        checks = self.audit(measurement)
        self.assertEqual(checks["font_floor"]["status"], "fail")
        self.assertEqual(checks["font_floor"]["level"], "critical")

    def test_overlong_line_fails(self):
        measurement = good_measurement()
        measurement["text_entries"][1]["max_units"] = 40
        checks = self.audit(measurement)
        self.assertEqual(checks["line_length"]["status"], "fail")

    def test_ellipsis_truncation_is_a_warning_not_overflow(self):
        measurement = good_measurement()
        measurement["overflow"] = [
            {"tag": "span", "cls": "attribution", "ellipsis": True, "dy": 0, "dx": 12}
        ]
        checks = self.audit(measurement)
        self.assertEqual(checks["overflow"]["status"], "pass")
        self.assertEqual(checks["truncation"]["status"], "fail")
        self.assertEqual(checks["truncation"]["level"], "warning")

    def test_clipping_is_critical(self):
        measurement = good_measurement()
        measurement["overflow"] = [
            {"tag": "div", "cls": "card-body", "ellipsis": False, "clips": True, "dy": 40, "dx": 0}
        ]
        checks = self.audit(measurement)
        self.assertEqual(checks["overflow"]["status"], "fail")
        self.assertEqual(checks["overflow"]["level"], "critical")

    def test_glyph_overflow_without_clipping_is_a_warning(self):
        measurement = good_measurement()
        measurement["overflow"] = [
            {"tag": "span", "cls": "metric-value", "ellipsis": False, "clips": False, "dy": 18, "dx": 0}
        ]
        checks = self.audit(measurement)
        self.assertEqual(checks["overflow"]["status"], "pass")
        self.assertEqual(checks["glyph_overflow"]["status"], "fail")
        self.assertEqual(checks["glyph_overflow"]["level"], "warning")

    def test_two_claims_fail_the_single_claim_rule(self):
        measurement = good_measurement()
        measurement["counts"]["claims"] = 2
        checks = self.audit(measurement)
        self.assertEqual(checks["single_claim"]["status"], "fail")

    def test_unlinked_encoding_fails_evidence_linkage(self):
        measurement = good_measurement()
        measurement["counts"]["encodings"] = 3
        measurement["counts"]["encodings_linked"] = 2
        checks = self.audit(measurement)
        self.assertEqual(checks["evidence_linkage"]["status"], "fail")

    def test_series_page_must_match_declared_index(self):
        measurement = good_measurement()
        measurement["canvas"]["series_size"] = "3"
        measurement["page_mark"] = "1/2"
        checks = self.audit(measurement)
        self.assertEqual(checks["series_page"]["status"], "fail")

    def test_image_size_mismatch_fails(self):
        checks = self.audit(good_measurement(), image_px=(1080, 1440))
        self.assertEqual(checks["image_size"]["status"], "fail")

    def test_score_threshold_and_deductions(self):
        self.assertEqual(cli.SCORE_THRESHOLD, 85)
        self.assertEqual(cli.SCORE_DEDUCTION["critical"], 12)
        measurement = good_measurement()
        measurement["counts"]["skeletons"] = 2
        checks = self.audit(measurement)
        self.assertEqual(checks["skeleton_replaced"]["status"], "fail")


class CliParserTests(unittest.TestCase):
    def test_subcommands_exist(self):
        parser = cli.build_parser()
        for command in ("init-brand", "scaffold", "render", "audit"):
            args = parser.parse_args(
                {
                    "init-brand": ["init-brand", "--name", "brand"],
                    "scaffold": ["scaffold", "--title", "t", "--output-dir", "out"],
                    "render": ["render", "--input", "a.html", "--output", "a.png"],
                    "audit": ["audit", "--input", "a.html"],
                }[command]
            )
            self.assertEqual(args.command, command)

    def test_scaffold_rejects_unknown_template(self):
        parser = cli.build_parser()
        with tempfile.TemporaryFile(mode="w") as sink, redirect_stderr(sink):
            with self.assertRaises(SystemExit):
                parser.parse_args(
                    ["scaffold", "--template", "nope", "--title", "t", "--output-dir", "out"]
                )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the mobile-infographic CLI regression suite")
    parser.add_argument("-v", "--verbose", type=int, default=2, choices=(0, 1, 2),
                        help="unittest verbosity (default 2)")
    parser.add_argument("pattern", nargs="?", help="only run test names containing this substring")
    args = parser.parse_args()
    argv = [sys.argv[0]] + ([args.pattern] if args.pattern else [])
    unittest.main(verbosity=args.verbose, argv=argv)
