#!/usr/bin/env python3
"""Focused tests for the deterministic Skill logic extractor."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "visualize_skill.py"
SPEC = importlib.util.spec_from_file_location("visualize_skill", SCRIPT)
assert SPEC and SPEC.loader
visualize_skill = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = visualize_skill
SPEC.loader.exec_module(visualize_skill)


FIXTURE = """---
name: lov-demo-flow
description: 给定一个本地输入生成流程结果；触发语包括“画运行逻辑”和 "visualize this skill"。
license: MIT
metadata:
  version: "0.1.0"
  dependencies:
    - python3
---

# Demo

## Triggers

### Activate when

- 用户说“画运行逻辑”。
- The user says "visualize this skill".

### Do not activate when

- 用户只要一张手绘插画。

## Workflow

### Step 0: Resolve input

- Read `references/rules.md`.
- If the file is missing, stop with a diagnostic.

### Step 1: Produce output

- Run `scripts/render.py`.
"""


class VisualizeSkillTests(unittest.TestCase):
    def make_skill(self, root: Path) -> Path:
        skill = root / "demo-skill"
        (skill / "references").mkdir(parents=True)
        (skill / "scripts").mkdir()
        (skill / "SKILL.md").write_text(FIXTURE, encoding="utf-8")
        (skill / "references" / "rules.md").write_text(
            "# Rules\n\nUse `scripts/render.py`.\n", encoding="utf-8"
        )
        (skill / "scripts" / "render.py").write_text(
            "#!/usr/bin/env python3\n", encoding="utf-8"
        )
        return skill

    def test_extracts_routing_steps_conditions_and_resources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary))
            root, skill_file = visualize_skill.resolve_skill(skill)
            model = visualize_skill.build_model(root, skill_file, 2)
            self.assertEqual(model["skill"]["name"], "lov-demo-flow")
            self.assertEqual(model["coverage"]["activation_examples"], 2)
            self.assertEqual(model["coverage"]["workflow_steps"], 2)
            self.assertEqual(model["coverage"]["conditional_rules"], 1)
            self.assertGreaterEqual(len(model["workflow"]["steps"][0]["details"]), 2)
            self.assertEqual(model["trust"]["scope"], "internal_runtime")
            self.assertEqual(model["trust"]["routing_scope"], "external_activation_boundary")
            self.assertEqual(model["trust"]["verification"]["effect_evidence"], "not_observed")
            linked = {item["path"] for item in model["resources"] if item["linked"]}
            self.assertIn("references/rules.md", linked)
            self.assertIn("scripts/render.py", linked)
            self.assertEqual(model["coverage"]["missing_resources"], 0)

    def test_directory_and_skill_file_inputs_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary))
            directory_result = visualize_skill.resolve_skill(skill)
            file_result = visualize_skill.resolve_skill(skill / "SKILL.md")
            self.assertEqual(directory_result, file_result)

    def test_report_and_json_are_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary))
            root, skill_file = visualize_skill.resolve_skill(skill)
            model = visualize_skill.build_model(root, skill_file, 1)
            report = visualize_skill.render_report(model, "TB", "zh")
            self.assertIn("```mermaid\nflowchart TB", report)
            self.assertIn("条件分支", report)
            self.assertIn('join_001_01(["继续"])', report)
            runtime = visualize_skill.render_runtime_mermaid(model, "TB", True)
            self.assertIn("Skill 内部执行开始", runtime)
            self.assertNotIn("匹配 Skill 触发条件", runtime)
            self.assertNotIn("request --> route", runtime)
            self.assertNotIn('((""))', report)
            json.loads(json.dumps(model, ensure_ascii=False))

    def test_standalone_html_embeds_review_model_without_external_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary))
            root, skill_file = visualize_skill.resolve_skill(skill)
            model = visualize_skill.build_model(root, skill_file, 1)
            page = visualize_skill.render_html(model, "TB", "zh")
            self.assertIn("<!doctype html>", page)
            self.assertIn("什么时候该用", page)
            self.assertIn("一句话看懂", page)
            self.assertIn("真实运行逻辑", page)
            self.assertIn("为什么是它", page)
            self.assertIn("可信边界", page)
            self.assertIn("展开技术证据", page)
            self.assertIn('id="logic-model"', page)
            self.assertIn("lovstudio/skill-logic/v1", page)
            self.assertIn('data-vendor="mermaid@11.12.2"', page)
            self.assertIn("mermaid.initialize", page)
            self.assertIn("data-mermaid-host", page)
            self.assertIn('data-source="#runtime-mermaid"', page)
            self.assertIn("这里是复核层，不是理解 Skill 的必经操作", page)
            self.assertIn("查看外部触发边界", page)
            self.assertNotIn("data-diagram-preview", page)
            self.assertNotIn("data-diagram-key", page)
            self.assertNotIn("data-trust-workspace", page)
            self.assertNotIn("data-select-step", page)
            self.assertNotIn("data-zoom", page)
            self.assertNotIn("data-export-svg", page)
            self.assertNotIn("<button", page)
            self.assertNotIn("data-theme-toggle", page)
            self.assertNotIn("<script src=", page)
            self.assertNotIn("<link rel=", page)

    def test_zh_display_localization_preserves_source_model(self) -> None:
        original = "Resolve the real surface"
        self.assertEqual(visualize_skill.display_text(original, True), "确认真实页面范围")
        self.assertEqual(visualize_skill.display_text(original, False), original)
        self.assertEqual(
            visualize_skill.display_text(
                "actual product behavior, repository content, live routes, and real assets;",
                True,
            ),
            "第二层：真实产品行为、代码库内容、线上路由和真实素材。",
        )
        self.assertEqual(visualize_skill.display_resource_kind("script", True), "脚本")

    def test_oh_my_landingpage_brief_leads_with_decisive_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary))
            root, skill_file = visualize_skill.resolve_skill(skill)
            model = visualize_skill.build_model(root, skill_file, 1)
            model["skill"]["name"] = "lov-oh-my-landingpage"
            module_ids = [
                "landing-review",
                "landing-brand",
                "landing-strategy",
                "landing-art-direction",
                "landing-builder",
            ]
            model["kit"] = {
                "modules": [
                    {"id": module_id, "source": f"skills/{module_id}/SKILL.md"}
                    for module_id in module_ids
                ],
                "pipelines": [
                    {
                        "id": "optimize",
                        "steps": [
                            "landing-review",
                            "landing-brand",
                            "landing-strategy",
                            "landing-art-direction",
                            "landing-builder",
                            "landing-review",
                        ],
                    }
                ],
            }
            brief = visualize_skill.build_review_brief(model, True)
            self.assertEqual(brief["scenario_title"], "首页能用，却像任何一家同行时，用它。")
            self.assertEqual(brief["pipeline_id"], "optimize")
            self.assertEqual(len(brief["stages"]), 9)
            self.assertEqual(brief["stages"][0]["title"], "确认真实页面")
            self.assertEqual(brief["stages"][2]["title"], "建立事实账本")
            self.assertIn("证据缺口不得变成公开声明", brief["stages"][2]["basis"])
            self.assertEqual(brief["stages"][-1]["title"], "复审并报告结果")
            page = visualize_skill.render_html(model, "TB", "zh")
            self.assertIn("首页能用，却像任何一家同行时，用它。", page)
            self.assertIn("单独改 CSS、重写 Hero 或换一套模板解决不了", page)
            self.assertIn("判断依据", page)
            self.assertNotIn("data-select-step", page)
            self.assertNotIn("data-zoom", page)

    def test_vendored_mermaid_runtime_and_license_are_packaged(self) -> None:
        self.assertTrue(visualize_skill.MERMAID_BUNDLE.is_file())
        self.assertGreater(visualize_skill.MERMAID_BUNDLE.stat().st_size, 1_000_000)
        license_path = visualize_skill.MERMAID_BUNDLE.parent / "MERMAID-LICENSE.txt"
        self.assertTrue(license_path.is_file())
        self.assertIn("MIT License", license_path.read_text(encoding="utf-8"))

    def test_html_defaults_to_markdown_sibling(self) -> None:
        output = Path("review/skill-flow.md")
        self.assertEqual(
            visualize_skill.default_html_path(output, None),
            Path("review/skill-flow.html"),
        )
        self.assertEqual(
            visualize_skill.default_html_path(output, Path("custom/review.html")),
            Path("custom/review.html"),
        )

    def test_kit_mapping_and_root_manifest_from_module(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = self.make_skill(Path(temporary))
            module = skill / "skills" / "review"
            module.mkdir(parents=True)
            (module / "SKILL.md").write_text(
                "# Review\n\n## Workflow\n\n### Step 1: Inspect result\n\n- Verify the output.\n\n## Quality gate\n\n- The output is traceable.\n",
                encoding="utf-8",
            )
            (skill / "skill.yaml").write_text(
                "runtime: skill-runtime/v1\n", encoding="utf-8"
            )
            (skill / "kit.yaml").write_text(
                """modules:
  - id: review
    skill: lov-review
    path: skills/review
pipelines:
  audit:
    - review
  optimize:
    - review
""",
                encoding="utf-8",
            )
            with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
                handle.write("\nUse `skills/review/SKILL.md` and `kit.yaml`.\n")
            root, skill_file = visualize_skill.resolve_skill(skill)
            model = visualize_skill.build_model(root, skill_file, 2)
            self.assertEqual(model["coverage"]["kit_modules"], 1)
            self.assertEqual(model["coverage"]["kit_pipelines"], 2)
            self.assertEqual(model["coverage"]["missing_resources"], 0)
            self.assertTrue(model["kit"]["modules"][0]["exists"])
            self.assertEqual(len(model["kit"]["modules"][0]["workflow_steps"]), 1)
            self.assertEqual(len(model["kit"]["modules"][0]["quality_gates"]), 1)
            self.assertIn("review", model["workflow"]["steps"][-1]["module_ids"])
            pipeline_ids = [item["id"] for item in model["kit"]["pipelines"]]
            self.assertEqual(pipeline_ids, ["audit", "optimize"])
            report = visualize_skill.render_report(model, "TB", "zh")
            self.assertIn("Kit 管线", report)
            self.assertIn('kit -- "audit" --> module_001', report)


if __name__ == "__main__":
    unittest.main()
