from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evidence_report.py"
SPEC = importlib.util.spec_from_file_location("evidence_report", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def measurement_provenance(source_ref: str) -> dict:
    return {
        "source_ref": source_ref,
        "build_ref": "release-build-1",
        "observed_at": "2026-08-10T10:00:00+08:00",
        "sample_window": "10 scripted runs",
        "sampler": "fixture sampler",
        "workload_id": "fixture-workload-v1",
    }


def evidence_document() -> dict:
    return {
        "schema": "app-runtime-evidence/v1",
        "title": "Fixture app runtime",
        "status": "verified",
        "scope": {
            "platform_family": "mobile",
            "runtime": "fixture",
            "workload": "ten scripted interactions",
        },
        "observations": [
            {
                "id": "slow-frame-rate",
                "stage": "before",
                "kind": "measurement",
                "value": 18,
                "unit": "percent",
                "source": "real-device trace",
                "note": "baseline",
                "provenance": measurement_provenance("trace-before"),
            },
            {
                "id": "slow-frame-rate",
                "stage": "after",
                "kind": "acceptance",
                "value": 4,
                "unit": "percent",
                "source": "real-device trace",
                "note": "same workload",
                "provenance": {
                    **measurement_provenance("trace-after"),
                    "acceptance": {
                        "threshold": "slow frames <= 5%",
                        "workload_contract": "fixture-workload-v1 on the same device",
                    },
                },
                "comparison": {"quality": "paired", "note": "contract matches"},
            },
        ],
        "resources": [
            {
                "id": "idle-session",
                "kind": "agent_session",
                "policy": "idle_resumable",
                "owner_state": "active",
                "activity_state": "idle",
                "resumable": True,
                "attachments": 0,
                "registration_active": False,
                "operation_active": False,
                "cwd_in_use": False,
                "dirty": None,
                "identity_state": "stable",
                "evidence_state": "complete",
                "retention_state": "eligible",
            },
            {
                "id": "unknown-directory",
                "kind": "directory",
                "policy": "inventory_only",
                "owner_state": "unknown",
                "activity_state": "unknown",
                "resumable": None,
                "attachments": 0,
                "registration_active": False,
                "operation_active": False,
                "cwd_in_use": False,
                "dirty": None,
                "identity_state": "unknown",
                "evidence_state": "missing",
                "retention_state": "unknown",
            },
        ],
        "hypotheses": [
            {
                "id": "render-fanout",
                "statement": "The interaction repeats render work per resident row.",
                "supports": ["slow-frame-rate"],
                "falsifier": "A trace has bounded render work independent of row count.",
                "priority": "P0",
            }
        ],
        "verification_gates": [
            {
                "name": "repository tests",
                "status": "passed",
                "source_ref": "ci-run-1",
                "note": "correctness only",
            }
        ],
        "evidence_gaps": ["No field distribution is available."],
    }


class EvidenceReportTests(unittest.TestCase):
    def test_computes_paired_delta_and_fail_closed_verdicts(self) -> None:
        report = MODULE.build_report(evidence_document())

        self.assertEqual(report["schema"], "app-runtime-report/v1")
        self.assertEqual(report["deltas"][0]["delta"], -14)
        self.assertAlmostEqual(report["deltas"][0]["percent_change"], -77.7777777778)
        self.assertEqual(report["deltas"][0]["comparison_quality"], "paired_observation")
        verdicts = {item["id"]: item for item in report["resources"]}
        self.assertEqual(verdicts["idle-session"]["verdict"], "candidate")
        self.assertEqual(verdicts["unknown-directory"]["verdict"], "protect")
        self.assertIn("inventory_only_policy", verdicts["unknown-directory"]["reasons"])
        self.assertIn("dirty_unknown", verdicts["unknown-directory"]["reasons"])

    def test_directional_comparison_suppresses_false_precision(self) -> None:
        document = evidence_document()
        document["observations"][1]["comparison"] = {
            "quality": "directional",
            "note": "different runtime boundary",
        }

        report = MODULE.build_report(document)

        self.assertIsNone(report["deltas"][0]["delta"])
        self.assertIsNone(report["deltas"][0]["percent_change"])
        self.assertEqual(report["deltas"][0]["comparison_quality"], "directional_evidence")

    def test_undeclared_current_comparison_suppresses_false_precision(self) -> None:
        document = evidence_document()
        del document["observations"][1]["comparison"]

        report = MODULE.build_report(document)

        self.assertIsNone(report["deltas"][0]["delta"])
        self.assertEqual(report["deltas"][0]["comparison_quality"], "undeclared_comparison")

    def test_current_measurement_requires_structured_provenance(self) -> None:
        document = evidence_document()
        del document["observations"][0]["provenance"]

        with self.assertRaisesRegex(MODULE.EvidenceError, "provenance"):
            MODULE.build_report(document)

    def test_current_schema_requires_platform_runtime_and_workload_scope(self) -> None:
        document = evidence_document()
        del document["scope"]["platform_family"]

        with self.assertRaisesRegex(MODULE.EvidenceError, "scope.platform_family"):
            MODULE.build_report(document)

    def test_inference_requires_formula_inputs_and_assumptions(self) -> None:
        document = evidence_document()
        document["observations"][0] = {
            "id": "estimated-work",
            "stage": "before",
            "kind": "inference",
            "value": 100,
            "unit": "calls",
            "source": "source path",
            "note": "derived",
            "provenance": {"source_ref": "source-path"},
        }

        with self.assertRaisesRegex(MODULE.EvidenceError, "derivation"):
            MODULE.build_report(document)

    def test_legacy_electron_schema_is_read_with_migration_warning(self) -> None:
        document = evidence_document()
        document["schema"] = "electron-runtime-evidence/v1"
        for observation in document["observations"]:
            observation.pop("provenance", None)

        report = MODULE.build_report(document)

        self.assertEqual(report["schema"], "app-runtime-report/v1")
        self.assertEqual(report["input_schema"], "electron-runtime-evidence/v1")
        self.assertIn("legacy input schema", report["warnings"][0])

    def test_active_non_resumable_session_is_protected(self) -> None:
        document = evidence_document()
        document["resources"][0]["resumable"] = False

        report = MODULE.build_report(document)

        self.assertEqual(report["resources"][0]["verdict"], "protect")
        self.assertIn("active_owner_not_resumable", report["resources"][0]["reasons"])

    def test_changed_identity_is_protected_against_aba(self) -> None:
        document = evidence_document()
        document["resources"][0]["identity_state"] = "changed"

        report = MODULE.build_report(document)

        self.assertEqual(report["resources"][0]["verdict"], "protect")
        self.assertIn("identity_changed", report["resources"][0]["reasons"])

    def test_unknown_hypothesis_reference_is_rejected(self) -> None:
        document = evidence_document()
        document["hypotheses"][0]["supports"] = ["missing-observation"]

        with self.assertRaisesRegex(MODULE.EvidenceError, "unknown observations"):
            MODULE.build_report(document)

    def test_cli_writes_json_markdown_gates_and_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            input_path = base / "evidence.json"
            json_path = base / "report.json"
            markdown_path = base / "report.md"
            input_path.write_text(json.dumps(evidence_document()), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--json-output",
                    str(json_path),
                    "--markdown-output",
                    str(markdown_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(json_path.read_text())
            markdown = markdown_path.read_text()
            self.assertEqual(report["summary"]["comparable_deltas"], 1)
            self.assertIn("Correctness and release gates", markdown)
            self.assertIn("No field distribution", markdown)
            self.assertIn("**protect**", markdown)


if __name__ == "__main__":
    unittest.main()
