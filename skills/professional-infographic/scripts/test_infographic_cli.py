#!/usr/bin/env python3
"""Regression tests for infographic title modes and scaffold output."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "infographic_cli",
    ROOT / "scripts" / "infographic_cli.py",
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load infographic_cli.py")
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def scaffold_args(
    output_dir: Path,
    *,
    title_mode: str,
    recommendation: Optional[str],
) -> argparse.Namespace:
    return argparse.Namespace(
        title="开源 MaaS 网关选型指南",
        title_mode=title_mode,
        recommendation=recommendation,
        source=None,
        aspect="16:9",
        template="comparison-matrix",
        mode="qualitative",
        output_dir=str(output_dir),
        brand_profile=str(ROOT / "assets" / "sgc-brand.json"),
    )


class ScaffoldTitleModeTests(unittest.TestCase):
    def test_topic_mode_adds_evidence_linked_tail_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "topic"
            CLI.scaffold(
                scaffold_args(
                    output,
                    title_mode="topic",
                    recommendation="默认选择 LiteLLM；已有 Kubernetes 时评估 Higress。",
                )
            )

            poster = (output / "poster.html").read_text(encoding="utf-8")
            project = json.loads((output / "project.json").read_text(encoding="utf-8"))
            brief = (output / "brief.md").read_text(encoding="utf-8")

            self.assertIn('data-title-mode="topic"', poster)
            self.assertIn('data-region="recommendation"', poster)
            self.assertIn('data-audit="recommendation"', poster)
            self.assertIn('data-source-ref="S1"', poster)
            self.assertLess(
                poster.index('data-region="visual"'),
                poster.index('data-region="recommendation"'),
            )
            self.assertLess(
                poster.index('data-region="recommendation"'),
                poster.index('data-region="footer"'),
            )
            self.assertEqual(project["schema_version"], 3)
            self.assertEqual(project["title_mode"], "topic")
            self.assertIn("Title mode: topic", brief)

    def test_action_mode_omits_tail_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "action"
            CLI.scaffold(
                scaffold_args(
                    output,
                    title_mode="action",
                    recommendation=None,
                )
            )

            poster = (output / "poster.html").read_text(encoding="utf-8")
            project = json.loads((output / "project.json").read_text(encoding="utf-8"))

            self.assertIn('data-title-mode="action"', poster)
            self.assertNotIn('data-region="recommendation"', poster)
            self.assertEqual(project["title_mode"], "action")
            self.assertEqual(project["recommendation"], "")

    def test_action_mode_rejects_duplicate_tail_advice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                CLI.CliError,
                "--recommendation is only valid",
            ):
                CLI.scaffold(
                    scaffold_args(
                        Path(temporary) / "invalid",
                        title_mode="action",
                        recommendation="重复建议",
                    )
                )

    def test_recommendation_copy_is_html_escaped(self) -> None:
        block = CLI.recommendation_block("<b>选择 A</b>")
        self.assertIn("&lt;b&gt;选择 A&lt;/b&gt;", block)
        self.assertNotIn("<b>选择 A</b>", block)


if __name__ == "__main__":
    unittest.main()
