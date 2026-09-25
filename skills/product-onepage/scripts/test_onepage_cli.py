#!/usr/bin/env python3
"""Regression tests for Product OnePage scaffolding and contracts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "onepage_cli",
    ROOT / "scripts" / "onepage_cli.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load onepage_cli.py")
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def args_for(output: Path, source: Path) -> argparse.Namespace:
    return argparse.Namespace(
        title="让每个产品想法，都有一张能被记住的发布海报",
        tagline="把产品真相、品牌叙事、真实证据与转化行动编排在同一张 OnePage 上。",
        category="Product marketing system",
        audience="独立开发者与产品团队",
        viewing_moment="产品发布与社交分享",
        market="domestic",
        lang="zh-CN",
        cta_label="查看产品示例",
        cta_url="https://example.com",
        source=str(source),
        source_note="来源：产品说明与真实工作流",
        attribution=None,
        layout="launch-story",
        style="editorial-tech",
        aspect="4:5",
        feature=[
            "先讲清楚|从产品真相提炼一个公开主张。",
            "再让人相信|把真实产品、机制与证据放在主舞台。",
            "最后能行动|让 CTA 指向真实可达的下一步。",
        ],
        proof=[
            "文字可编辑|标题、卖点与 CTA 保留在 HTML 中|S1",
            "交付可审计|源文件、提示词和审计报告共同保存|S2",
        ],
        hero_image=None,
        hero_alt=None,
        product_authenticity="conceptual",
        brand_profile=str(ROOT / "assets" / "brand-profile.template.json"),
        output_dir=str(output),
        force=False,
    )


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_writes_complete_portable_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.md"
            source.write_text("# 产品资料\n\n真实来源内容。\n", encoding="utf-8")
            output = root / "onepage"

            self.assertEqual(CLI.scaffold(args_for(output, source)), 0)

            expected = {
                "onepage.html",
                "source.md",
                "brief.md",
                "content.md",
                "project.json",
                "prompts/hero-visual.md",
            }
            actual = {
                str(path.relative_to(output))
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertTrue(expected.issubset(actual))

            markup = (output / "onepage.html").read_text(encoding="utf-8")
            project = json.loads((output / "project.json").read_text(encoding="utf-8"))
            self.assertIn('data-layout="launch-story"', markup)
            self.assertIn('data-style="editorial-tech"', markup)
            self.assertIn('data-aspect="4:5"', markup)
            self.assertIn('href="https://example.com"', markup)
            self.assertIn("data:image/svg+xml;base64,", markup)
            self.assertNotRegex(markup, CLI.PLACEHOLDER_RE)
            self.assertEqual(project["schema_version"], 1)
            self.assertEqual(project["cta"]["label"], "查看产品示例")
            self.assertEqual(project["product_authenticity"], "conceptual")

    def test_scaffold_escapes_visible_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.md"
            source.write_text("source", encoding="utf-8")
            args = args_for(root / "output", source)
            args.title = "A < B & C"
            CLI.scaffold(args)
            markup = (root / "output" / "onepage.html").read_text(encoding="utf-8")
            self.assertIn("A &lt; B &amp; C", markup)
            self.assertNotIn("<h1 class=\"headline\" data-role=\"headline\" data-audit=\"headline\">A < B", markup)

    def test_feature_and_proof_syntax_is_strict(self) -> None:
        with self.assertRaises(CLI.CliError):
            CLI.parse_feature("missing separator")
        with self.assertRaises(CLI.CliError):
            CLI.parse_proof("claim|detail|source-one")

    def test_semantic_units_count_cjk_and_latin_words(self) -> None:
        self.assertEqual(CLI.semantic_units("产品 Product OnePage 2026"), 5)


if __name__ == "__main__":
    unittest.main()
