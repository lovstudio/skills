from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evidence_report.py"
SPEC = importlib.util.spec_from_file_location("evidence_report_for_kit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class KitEvaluationTests(unittest.TestCase):
    def test_controller_identity_and_adapter_matrix_are_cross_platform(self) -> None:
        manifest = yaml.safe_load((ROOT / "skill.yaml").read_text(encoding="utf-8"))
        kit = yaml.safe_load((ROOT / "kit.yaml").read_text(encoding="utf-8"))
        controller = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        adapters = (ROOT / "references" / "platform-adapters.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(manifest["id"], "lov-app-optimizer")
        self.assertEqual(manifest["version"], "0.2.0")
        self.assertEqual(kit["entrypoint"], "lov-app-optimizer")
        for runtime in (
            "Electron",
            "Tauri",
            "iOS",
            "Android",
            "React Native",
            "Flutter",
            "Web/PWA",
        ):
            self.assertIn(runtime, controller)
            self.assertIn(runtime, adapters)

    def test_trigger_fixture_covers_multiple_platforms_non_triggers_and_pipelines(self) -> None:
        fixture = json.loads((ROOT / "tests" / "trigger-evals.json").read_text(encoding="utf-8"))
        kit = yaml.safe_load((ROOT / "kit.yaml").read_text(encoding="utf-8"))
        cases = fixture["cases"]
        active = [case for case in cases if case["expected"]["activate"]]
        inactive = [case for case in cases if not case["expected"]["activate"]]

        self.assertGreaterEqual(len(active), 6)
        self.assertGreaterEqual(len(inactive), 4)
        self.assertGreaterEqual(
            len({case["expected"]["platform_family"] for case in active}), 4
        )
        self.assertTrue(any("Electron" in case["input"] for case in active))
        self.assertTrue(any("iPhone" in case["input"] for case in active))
        self.assertTrue(any("PWA" in case["input"] for case in active))
        for case in active:
            self.assertIn(case["expected"]["pipeline"], kit["pipelines"])
        for case in inactive:
            self.assertTrue(case["expected"]["reason"])

    def test_yoda_remains_electron_case_one_without_claiming_cross_platform_proof(self) -> None:
        cases = json.loads((ROOT / "cases" / "cases.json").read_text(encoding="utf-8"))
        case = cases[0]

        self.assertEqual(case["ordinal"], 1)
        self.assertEqual(case["platform"]["runtime"], "Electron")
        self.assertEqual(case["platform"]["legacy_source"], "lov-electron-runtime-optimizer@0.1.0")
        self.assertEqual(case["output"]["status"], "partially_verified")
        self.assertIn(
            "其他平台目前是 adapter 设计与触发覆盖",
            case["output"]["boundaries"][-1],
        )
        hydration = next(
            item
            for item in case["output"]["runtime_evidence"]
            if item["metric"] == "初始任务 hydration 上限"
        )
        self.assertIn("upper_bound", hydration["status"])
        self.assertNotIn("reduction", hydration)

    def test_yoda_evidence_exercises_all_modules_without_fake_acceptance(self) -> None:
        document = json.loads(
            (ROOT / "cases" / "evidence" / "yoda-runtime-evidence.json").read_text(
                encoding="utf-8"
            )
        )

        report = MODULE.build_report(document)

        self.assertEqual(report["schema"], "app-runtime-report/v1")
        self.assertEqual(report["status"], "partially_verified")
        self.assertGreater(report["summary"]["observations"], 0)
        self.assertGreater(report["summary"]["hypotheses"], 0)
        self.assertGreater(report["summary"]["resources"], 0)
        self.assertIn("protect", report["summary"]["resource_verdicts"])
        self.assertIn("candidate", report["summary"]["resource_verdicts"])
        self.assertTrue(report["verification_gates"])
        self.assertTrue(report["evidence_gaps"])
        self.assertFalse(any(item["kind"] == "acceptance" for item in report["observations"]))
        git_comparison = next(
            item for item in report["deltas"] if item["id"] == "git-subprocesses-per-sync"
        )
        self.assertIsNone(git_comparison["percent_change"])


if __name__ == "__main__":
    unittest.main()
