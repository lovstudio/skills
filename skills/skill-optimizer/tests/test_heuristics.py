import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

FEEDBACK_GATE = """
## 通用反馈闭环

5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
"""

PROFILE = """
## User Profile (cross-session)

用户直接说出长期值时，用 `scripts/profile_store.py record` 写回并报告保存路径。
"""

INTERACTION = """id: lov-demo
version: "0.1.0"
context:
  interaction:
    ask_missing: {ask_missing}
    max_questions: {max_questions}
"""


def skill_md(description, body, depends_on=""):
    return (
        "---\nname: lov-demo\ndescription: >\n  "
        + description
        + "\nlicense: MIT\ncompatibility: Python 3.8+\n"
        + depends_on
        + 'metadata:\n  author: lovstudio\n  version: "0.1.0"\n  tags: demo\n---\n\n# Demo\n\n'
        + body
    )


def write_skill(skill, spec, manifest=None):
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(spec, encoding="utf-8")
    (skill / "README.md").write_text("# Demo\n", encoding="utf-8")
    if manifest is not None:
        (skill / "skill.yaml").write_text(manifest, encoding="utf-8")


def run_lint(skill):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "lint_skill.py"), "--path", str(skill), "--json"],
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)["findings"]


def lint(spec, manifest=None):
    with tempfile.TemporaryDirectory() as tmp:
        skill = Path(tmp) / "demo-skill"
        write_skill(skill, spec, manifest)
        return run_lint(skill)


def codes(findings, code):
    return [f for f in findings if f["code"] == code]


class BrandingDependencyTests(unittest.TestCase):
    def test_boilerplate_negative_triggers_and_identifiers_do_not_imply_authored_output(self):
        cases = {
            # The feedback gate's "发布" used to pair with any artifact word.
            "feedback gate": skill_md(
                "从本地缓存检索公众号文章并返回命中列表。Use when the user mentions searching saved articles.",
                "## Workflow\n\n返回标题、链接与命中片段。\n" + PROFILE + FEEDBACK_GATE,
            ),
            "negative trigger": skill_md(
                "把视频压缩到更小体积并保留画质。Use when the user mentions compressing a video.",
                "## Triggers\n\n### Do not activate when\n\n- 用户要生成活动海报：交给海报能力。\n" + FEEDBACK_GATE,
            ),
            "identifiers and code": skill_md(
                "旧兼容入口，新任务统一路由到 lov-publish-wechat-article。Use when a legacy task names this Skill.",
                "## Workflow\n\n运行 `python3 scripts/generate-poster.py --check` 确认交接。\n" + FEEDBACK_GATE,
            ),
            "status report": skill_md(
                "Generate a JSON status report and copy the document path. Use when the user mentions index status.",
                "## Workflow\n\n生成 JSON 报告，并报告保存路径。\n" + FEEDBACK_GATE,
            ),
        }
        for name, spec in cases.items():
            with self.subTest(name):
                self.assertEqual(codes(lint(spec), "MISSING_BRANDING_DEP"), [])

    def test_article_poster_and_copy_skills_are_still_reported(self):
        cases = {
            "article": skill_md(
                "撰写并排版公众号文章。Use when the user asks to write a WeChat article.",
                "## Workflow\n\n按大纲写正文。\n" + FEEDBACK_GATE,
            ),
            "poster": skill_md(
                "Create event posters and flyers from a brief. Use when the user mentions an event poster.",
                "## Workflow\n\nLay out the headline and QR code.\n" + FEEDBACK_GATE,
            ),
            "copy": skill_md(
                "把近期项目更新写成朋友圈文案。Use when the user mentions a daily update post.",
                "## Workflow\n\n选取三条真实更新。\n" + FEEDBACK_GATE,
            ),
        }
        for name, spec in cases.items():
            with self.subTest(name):
                hits = codes(lint(spec), "MISSING_BRANDING_DEP")
                self.assertEqual(len(hits), 1, hits)
                self.assertEqual(hits[0]["severity"], "warn")
                self.assertIn("matched '", hits[0]["message"])

    def test_declared_dependency_satisfies_the_gate(self):
        spec = skill_md(
            "撰写并排版公众号文章。Use when the user asks to write a WeChat article.",
            "## Workflow\n\n按大纲写正文。\n",
            depends_on="depends_on:\n  - lov-branding-consistency\n",
        )
        self.assertEqual(codes(lint(spec), "MISSING_BRANDING_DEP"), [])


class AskUserTests(unittest.TestCase):
    WORKFLOW = skill_md(
        "Rebuild the local cache and verify it. Use when the user mentions a stale cache.",
        "## Workflow\n\n1. Read the current state.\n2. Rebuild and read it back.\n",
    )

    def test_workflow_without_declared_interaction_is_reported(self):
        for name, manifest in {"no manifest": None, "manifest without interaction": 'id: lov-demo\nversion: "0.1.0"\n'}.items():
            with self.subTest(name):
                self.assertEqual(len(codes(lint(self.WORKFLOW, manifest), "BODY_NO_ASKUSER")), 1)

    def test_manifest_interaction_policy_exempts_the_body(self):
        for ask_missing, max_questions in (("true", "1"), ("false", "0")):
            with self.subTest(ask_missing=ask_missing):
                manifest = INTERACTION.format(ask_missing=ask_missing, max_questions=max_questions)
                self.assertEqual(codes(lint(self.WORKFLOW, manifest), "BODY_NO_ASKUSER"), [])

    def test_embedded_kit_module_uses_the_kit_interaction_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            kit = Path(tmp) / "demo-kit-skill"
            write_skill(kit, self.WORKFLOW, INTERACTION.format(ask_missing="true", max_questions="1"))
            module = kit / "skills" / "demo-module"
            write_skill(module, self.WORKFLOW)
            self.assertEqual(codes(run_lint(module), "BODY_NO_ASKUSER"), [])
            (kit / "skill.yaml").write_text('id: lov-demo\nversion: "0.1.0"\n', encoding="utf-8")
            self.assertEqual(len(codes(run_lint(module), "BODY_NO_ASKUSER")), 1)

    def test_chinese_non_interactive_statement_exempts_the_body(self):
        spec = self.WORKFLOW.replace("## Workflow\n", "## Workflow\n\n本流程非交互执行，缺少信息时使用安全默认值。\n")
        self.assertEqual(codes(lint(spec), "BODY_NO_ASKUSER"), [])


if __name__ == "__main__":
    unittest.main()
