#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


add_case = load_module("test_add_case_core", SCRIPTS / "add_case.py")
workflow = load_module("test_add_case_workflow", SCRIPTS / "add_case_with_session.py")
public_verifier = load_module(
    "test_add_case_public_verifier",
    SCRIPTS / "verify_public_case.py",
)

SLUG = "yss_" + "A" * 43


def base_case() -> dict:
    return {
        "id": "accepted-result",
        "type": "case",
        "title": "Accepted result",
        "description": "A real accepted result.",
        "input": {"items": ["real input"]},
        "prompt": "Complete the requested work.",
        "output": {"items": ["real output"]},
        "evidence": {
            "acceptance": "user-confirmed",
            "verified_at": "2026-08-27",
            "method": "User reviewed the exact output.",
            "privacy": "Secrets and private paths were redacted.",
        },
    }


def paid_session() -> dict:
    return {
        "url": f"https://lovstudio.ai/yoda/session/{SLUG}?detail=concise",
        "access": "paid",
        "priceCredits": 140,
        "pricingRule": "ceil(target-skill-price/10)",
        "targetSkill": "lov-media-creator",
    }


class AddCaseWithSessionTests(unittest.TestCase):
    def test_direct_case_mutation_requires_a_paid_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skill.yaml").write_text(
                "schema: skill-manifest/v1\nid: lov-media-creator\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(add_case.CaseError, "session is required"):
                add_case.validate_case(root, base_case())

            case = base_case()
            case["session"] = paid_session()
            self.assertEqual(
                add_case.validate_case(root, case)["session"]["priceCredits"],
                140,
            )

            case["session"]["targetSkill"] = "lov-share-session"
            with self.assertRaisesRegex(
                add_case.CaseError,
                "must match the target Skill id",
            ):
                add_case.validate_case(root, case)

    def test_visual_case_requires_the_accepted_output_as_cover(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skill.yaml").write_text(
                "schema: skill-manifest/v1\nid: lov-media-creator\n",
                encoding="utf-8",
            )
            case = base_case()
            case["evidence"]["artifact_type"] = "visual"
            case["session"] = paid_session()

            with self.assertRaisesRegex(
                add_case.CaseError,
                "visual case requires cover",
            ):
                add_case.validate_case(root, case)

            case["cover"] = "https://cdn.example.com/final-output.png"
            self.assertEqual(
                add_case.validate_case(root, case)["cover"],
                case["cover"],
            )

    def test_composed_workflow_uploads_before_writing_the_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "target"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (root / "skill.yaml").write_text(
                "schema: skill-manifest/v1\nid: lov-media-creator\n",
                encoding="utf-8",
            )
            case_path = Path(temporary) / "case.json"
            case_path.write_text(json.dumps(base_case()), encoding="utf-8")
            share_script = Path(temporary) / "share_session.py"
            share_script.write_text("# placeholder\n", encoding="utf-8")
            args = argparse.Namespace(
                target=root,
                case=str(case_path),
                file=None,
                session_id=None,
                share_session_script=share_script,
                session_title=None,
                detail="concise",
                base_url="https://lovstudio.ai",
                profile_path=None,
                timeout=60,
                dry_run=False,
                replace_existing=False,
            )
            share_result = {
                **paid_session(),
                "caseId": "accepted-result",
            }

            with patch.object(workflow, "execute_share", return_value=share_result):
                result = workflow.run(args)

            self.assertEqual(result["session_status"], "uploaded-paid")
            cases = json.loads((root / "cases" / "cases.json").read_text())
            self.assertEqual(cases[0]["session"], paid_session())

    def test_dry_run_uploads_nothing_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "target"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (root / "skill.yaml").write_text(
                "schema: skill-manifest/v1\nid: lov-media-creator\n",
                encoding="utf-8",
            )
            case_path = Path(temporary) / "case.json"
            case_path.write_text(json.dumps(base_case()), encoding="utf-8")
            share_script = Path(temporary) / "share_session.py"
            share_script.write_text("# placeholder\n", encoding="utf-8")
            args = argparse.Namespace(
                target=root,
                case=str(case_path),
                file=None,
                session_id=None,
                share_session_script=share_script,
                session_title=None,
                detail="concise",
                base_url="https://lovstudio.ai",
                profile_path=None,
                timeout=60,
                dry_run=True,
                replace_existing=False,
            )

            with patch.object(
                workflow,
                "execute_share",
                return_value={
                    "access": {
                        "mode": "paid",
                        "sourceSkillName": "lov-media-creator",
                        "caseId": "accepted-result",
                    }
                },
            ):
                result = workflow.run(args)

            self.assertEqual(result["session_status"], "prepared-not-uploaded")
            self.assertFalse((root / "cases" / "cases.json").exists())

    def test_upload_failure_leaves_the_case_registry_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "target"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            (root / "skill.yaml").write_text(
                "schema: skill-manifest/v1\nid: lov-media-creator\n",
                encoding="utf-8",
            )
            case_path = Path(temporary) / "case.json"
            case_path.write_text(json.dumps(base_case()), encoding="utf-8")
            share_script = Path(temporary) / "share_session.py"
            share_script.write_text("# placeholder\n", encoding="utf-8")
            args = argparse.Namespace(
                target=root,
                case=str(case_path),
                file=None,
                session_id=None,
                share_session_script=share_script,
                session_title=None,
                detail="concise",
                base_url="https://lovstudio.ai",
                profile_path=None,
                timeout=60,
                dry_run=False,
                replace_existing=False,
            )

            registry = root / "cases" / "cases.json"
            registry.parent.mkdir()
            registry.write_text("[]\n", encoding="utf-8")
            before = registry.read_bytes()
            with patch.object(
                workflow,
                "execute_share",
                side_effect=workflow.WorkflowError(
                    "Target Skill cannot price a paid session"
                ),
            ):
                with self.assertRaisesRegex(
                    workflow.WorkflowError,
                    "cannot price",
                ):
                    workflow.run(args)
                self.assertEqual(registry.read_bytes(), before)

    def test_public_verifier_requires_rendered_and_reachable_case_images(self) -> None:
        case = base_case()
        case["cover"] = "https://cdn.example.com/final-output.png"
        case_fingerprint = public_verifier.canonical_fingerprint(case)
        args = argparse.Namespace(
            cases_url="https://example.com/cases/cases.json",
            page_url="https://lovstudio.ai/skills/demo",
            case_page_url="https://lovstudio.ai/skills/demo/cases/accepted-result",
            case_id=case["id"],
            fingerprint=case_fingerprint,
            marker=case["title"],
            timeout=15,
        )

        def fake_fetch(url: str, _timeout: float):
            if url == args.cases_url:
                return 200, json.dumps([case]).encode(), "utf-8"
            if url == args.page_url:
                return 200, case["title"].encode(), "utf-8"
            page = (f'<h1>{case["title"]}</h1><article data-testid="skill-case-details">'
                    f'<img src="{case["cover"]}"><h2>Input</h2><h2>Prompt</h2><h2>Output</h2></article>').encode()
            return 200, page, "utf-8"

        with (
            patch.object(public_verifier, "fetch", side_effect=fake_fetch),
            patch.object(
                public_verifier,
                "fetch_public_image",
                return_value={
                    "url": case["cover"],
                    "http_status": 200,
                    "content_type": "image/png",
                    "bytes": 123,
                },
            ) as image_fetch,
        ):
            result = public_verifier.run(args)

        image_fetch.assert_called_once_with(case["cover"], 15)
        self.assertEqual(result["images"][0]["content_type"], "image/png")

        with patch.object(
            public_verifier,
            "fetch",
            side_effect=[
                (200, json.dumps([case]).encode(), "utf-8"),
                (200, case["title"].encode(), "utf-8"),
                (200, f'<h1>{case["title"]}</h1><article data-testid="skill-case-details"><h2>Input</h2><h2>Prompt</h2><h2>Output</h2></article>'.encode(), "utf-8"),
            ],
        ):
            with self.assertRaisesRegex(ValueError, "missing case image"):
                public_verifier.run(args)

    def test_public_verifier_ignores_serialized_script_and_checks_real_headings(self):
        page = public_verifier.PublicPage('<script>Accepted result INPUT PROMPT OUTPUT</script><article data-testid="skill-case-details"><h2>输入 / Input</h2></article>')
        self.assertNotIn("Accepted result", page.text)
        self.assertEqual(page.headings, ["输入 / Input"])
        self.assertTrue(page.has_case)

    def test_relative_uploaded_images_resolve_from_the_skill_root(self):
        case = base_case()
        case["cover"] = "cases/assets/accepted-result/1.png"
        args = argparse.Namespace(cases_url="https://raw.githubusercontent.com/lovstudio/demo/main/cases/cases.json", page_url="https://lovstudio.ai/skills/demo",
                                  case_page_url="https://lovstudio.ai/skills/demo/cases/accepted-result", case_id=case["id"],
                                  fingerprint=public_verifier.canonical_fingerprint(case), marker=case["title"], timeout=15)
        image = "https://raw.githubusercontent.com/lovstudio/demo/main/" + case["cover"]
        detail = f'<h1>{case["title"]}</h1><article data-testid="skill-case-details"><img src="{image}"><h2>Input</h2><h2>Prompt</h2><h2>Output</h2></article>'
        with patch.object(public_verifier, "fetch", side_effect=[(200, json.dumps([case]).encode(), "utf-8"), (200, case["title"].encode(), "utf-8"), (200, detail.encode(), "utf-8")]), patch.object(public_verifier, "fetch_public_image", return_value={}) as fetch_image:
            public_verifier.run(args)
        fetch_image.assert_called_once_with(image, 15)

    def test_public_session_is_checked_and_is_not_reported_as_paid(self):
        case = base_case()
        case["session"] = {"access": "public", "url": f"https://lovstudio.ai/yoda/session/{SLUG}"}
        args = argparse.Namespace(cases_url="https://example.com/cases/cases.json", page_url="https://lovstudio.ai/skills/demo", case_page_url="https://lovstudio.ai/skills/demo/cases/accepted-result", case_id=case["id"],
                                  fingerprint=public_verifier.canonical_fingerprint(case), marker=case["title"], timeout=15)
        detail = f'<h1>{case["title"]}</h1><article data-testid="skill-case-details"><h2>Input</h2><h2>Prompt</h2><h2>Output</h2><a href="{case["session"]["url"]}">Session</a></article>'
        for body, expected in [('<section aria-label="会话记录">Public conversation</section>', "public-page-checked"), ("<main>PAID CASE SESSION</main>", None)]:
            with patch.object(public_verifier, "fetch", side_effect=[(200, json.dumps([case]).encode(), "utf-8"), (200, case["title"].encode(), "utf-8"), (200, detail.encode(), "utf-8"), (200, body.encode(), "utf-8")]):
                if expected:
                    self.assertEqual(public_verifier.run(args)["session_access"], expected)
                else:
                    with self.assertRaisesRegex(ValueError, "paywall"):
                        public_verifier.run(args)


if __name__ == "__main__":
    unittest.main()
