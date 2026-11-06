import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parent / "validate_runs_on.py"
SPEC = importlib.util.spec_from_file_location("validate_runs_on", SCRIPT)
validate_runs_on = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_runs_on)

PASSED = {
    "id": "run",
    "date": "2026-11-06",
    "env": "macOS 26 arm64, WorkBuddy CLI 2.115, kimi-k2.7",
    "result": "passed",
    "scope_zh": "合成素材跑完，独立校验通过",
    "scope_en": "Ran the sample through; independent checks passed",
}
GOOD = {
    "checked_at": "2026-11-06",
    "skill_version": "1.0.0",
    "verdict_zh": "Mac 能跑。",
    "verdict_en": "Runs on a Mac.",
    "systems": [
        {"id": "macos-arm64", "status": "verified", "evidence": ["run"]},
        {"id": "macos-intel", "status": "unverified"},
        {"id": "windows", "status": "unverified"},
        {"id": "linux", "status": "unverified"},
    ],
    "agents": [{"label": "WorkBuddy", "model": "kimi-k2.7", "domestic": True, "status": "verified", "evidence": ["run"]}],
    "requires": [],
    "alternatives": [],
    "evidence": [PASSED],
}


def errors_for(**changes):
    record = copy.deepcopy(GOOD)
    record.update(changes)
    return validate_runs_on.validate_record("x", record)


def agent(**changes):
    return [{"label": "WorkBuddy", "model": "kimi-k2.7", "domestic": True, "status": "verified", "evidence": ["run"], **changes}]


class ClaimsNeedRuns(unittest.TestCase):
    def assert_rejected(self, pattern, **changes):
        errors = errors_for(**changes)
        self.assertTrue(errors, "expected the record to be rejected")
        self.assertRegex("\n".join(errors), pattern)

    def test_good_record_passes(self):
        self.assertEqual(errors_for(), [])

    def test_verified_without_evidence_is_rejected(self):
        self.assert_rejected("verified needs a cited run", agents=agent(evidence=[]))

    def test_verified_citing_a_missing_record_is_rejected(self):
        self.assert_rejected("unknown evidence", agents=agent(evidence=["gone"]))

    def test_verified_on_a_failed_run_is_rejected(self):
        self.assert_rejected("verified needs a cited run", evidence=[{**PASSED, "result": "failed"}])

    def test_verified_on_a_partial_run_is_rejected(self):
        self.assert_rejected("verified needs a cited run", evidence=[{**PASSED, "result": "partial"}])

    def test_a_source_declaration_cannot_prove_it_works(self):
        self.assert_rejected("source declaration can only record", evidence=[{**PASSED, "kind": "source"}])

    def test_partial_must_say_what_is_missing(self):
        self.assert_rejected(
            "partial must say what is missing",
            agents=agent(status="partial"),
            evidence=[{**PASSED, "result": "partial"}],
        )

    def test_blocked_needs_a_failure_and_a_reason(self):
        self.assert_rejected("blocked needs cited evidence", agents=agent(status="blocked", gap_zh="x", gap_en="y"))
        self.assert_rejected(
            "blocked must say what is missing",
            agents=agent(status="blocked"),
            evidence=[{**PASSED, "result": "failed"}],
        )

    def test_blocked_may_rest_on_the_source(self):
        record = copy.deepcopy(GOOD)
        record["systems"][2] = {"id": "windows", "status": "blocked", "evidence": ["src"], "note_zh": "只支持 macOS", "note_en": "macOS only"}
        record["evidence"].append({**PASSED, "id": "src", "kind": "source", "result": "failed"})
        self.assertEqual(validate_runs_on.validate_record("x", record), [])

    def test_unverified_must_not_cite_evidence(self):
        self.assert_rejected("unverified must not cite", agents=agent(status="unverified"))

    def test_unknown_status_is_rejected(self):
        self.assert_rejected("status must be one of", agents=agent(status="works-great"))

    def test_tested_agent_must_name_its_model(self):
        record = copy.deepcopy(GOOD)
        del record["agents"][0]["model"]
        self.assertRegex("\n".join(validate_runs_on.validate_record("x", record)), "must name the model")


class RecordShape(unittest.TestCase):
    def test_every_system_must_be_answered(self):
        record = copy.deepcopy(GOOD)
        record["systems"] = record["systems"][:3]
        self.assertRegex("\n".join(validate_runs_on.validate_record("x", record)), "must list linux")

    def test_unknown_field_is_rejected(self):
        self.assertRegex("\n".join(errors_for(extra=1)), "unknown field 'extra'")

    def test_evidence_needs_where_and_what(self):
        self.assertRegex("\n".join(errors_for(evidence=[{**PASSED, "env": ""}])), "env is required")
        self.assertRegex("\n".join(errors_for(evidence=[{**PASSED, "scope_en": ""}])), "scope_en is required")

    def test_future_evidence_is_rejected(self):
        self.assertRegex("\n".join(errors_for(evidence=[{**PASSED, "date": "2027-01-01"}])), "dated after checked_at")

    def test_uncited_evidence_is_rejected(self):
        self.assertRegex("\n".join(errors_for(evidence=[PASSED, {**PASSED, "id": "spare"}])), "not cited")

    def test_public_text_cannot_carry_a_local_path(self):
        self.assertRegex("\n".join(errors_for(evidence=[{**PASSED, "scope_en": "ran /Users/someone/x"}])), "private path")

    def test_requires_must_be_explicit(self):
        record = copy.deepcopy(GOOD)
        del record["requires"]
        self.assertRegex("\n".join(validate_runs_on.validate_record("x", record)), "use \\[\\] when no account")

    def test_evidence_link_must_exist_in_the_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            url = f"{validate_runs_on.EVIDENCE_URL_PREFIX}evidence/x/run.md"
            record = copy.deepcopy(GOOD)
            record["evidence"][0]["url"] = url
            self.assertRegex("\n".join(validate_runs_on.validate_record("x", record, root)), "file not in this repo")
            (root / "evidence/x").mkdir(parents=True)
            (root / "evidence/x/run.md").write_text("ok", encoding="utf-8")
            self.assertEqual(validate_runs_on.validate_record("x", record, root), [])


class RealCatalog(unittest.TestCase):
    def test_skills_yaml_records_are_valid(self):
        data = yaml.safe_load((validate_runs_on.ROOT / "skills.yaml").read_text(encoding="utf-8"))
        self.assertEqual(validate_runs_on.validate_catalog(data), [])


if __name__ == "__main__":
    unittest.main()
