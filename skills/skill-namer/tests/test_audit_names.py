"""Exercise observable CLI failures without changing the source fixtures."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AuditCLI(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / "cases/evidence/self-naming-review.json").read_text())

    def run_plan(self, plan=None, raw=None):
        data = raw if raw is not None else json.dumps(plan, ensure_ascii=False).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.json"
            path.write_bytes(data)
            proc = subprocess.run([sys.executable, str(ROOT / "scripts/audit_names.py"), str(path)],
                                  capture_output=True, text=True)
            self.assertEqual(path.read_bytes(), data, "audit modified its input")
            self.assertEqual(proc.stderr, "", "unexpected traceback or stderr")
            return proc.returncode, json.loads(proc.stdout)

    def assert_error(self, code):
        status, report = self.run_plan(self.plan)
        self.assertEqual(status, 1)
        self.assertIn(code, [error["code"] for error in report["errors"]])

    def test_real_cases_pass(self):
        for name in ("self-naming-review.json", "catalog-review.json"):
            plan = json.loads((ROOT / "cases/evidence" / name).read_text())
            status, report = self.run_plan(plan)
            self.assertEqual(status, 0)
            self.assertTrue(report["ok"])
            self.assertEqual(report["counts"]["scope"], len(plan["rows"]))

    def test_approved_spelling_is_exact(self):
        self.plan["rows"][0]["after"]["name_zh"] = "Skill命名大师"
        self.assert_error("approved_name_changed")

    def test_unicode_case_and_spacing_duplicates(self):
        other = copy.deepcopy(self.plan["rows"][0])
        other.update(id="second-skill", approved={}, approval={"name_zh":"editorial", "display_name":"editorial"})
        other["after"] = {"name_zh":"另一个名字", "display_name":"ＳＫＩＬＬ NamingMaster"}
        self.plan["scope_ids"].append("second-skill")
        self.plan["rows"].append(other)
        self.assert_error("duplicate_name")

    def test_missing_scope_member(self):
        self.plan["scope_ids"].append("missing-skill")
        self.assert_error("missing_rows")

    def test_duplicate_identity(self):
        self.plan["rows"].append(copy.deepcopy(self.plan["rows"][0]))
        self.assert_error("duplicate_id")

    def test_decision_must_match_changes(self):
        self.plan["rows"][0]["decision"] = "retain"
        self.assert_error("decision_mismatch")

    def test_pending_review_is_not_completion(self):
        self.plan["rows"][0]["decision"] = "review"
        self.assert_error("pending_review")

    def test_unbacked_approval(self):
        self.plan["rows"][0]["approved"] = {}
        self.assert_error("missing_approval_evidence")

    def test_compatibility_mutation_is_not_a_display_field(self):
        self.plan["rows"][0]["after"]["runtime_name"] = "changed-id"
        status, report = self.run_plan(self.plan)
        self.assertEqual(status, 2)
        self.assertIn("invalid after", report["error"])

    def test_duplicate_json_keys_rejected(self):
        status, report = self.run_plan(raw=b'{"schema":"a","schema":"b"}')
        self.assertEqual(status, 2)
        self.assertIn("duplicate JSON key", report["error"])

    def test_malformed_input_is_diagnostic(self):
        for raw in (b'[]', b'{', b'\xff', b'{"schema":NaN}'):
            status, report = self.run_plan(raw=raw)
            self.assertEqual(status, 2)
            self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
