#!/usr/bin/env python3
"""Exercise the bundled production validator; no test framework required."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    case_dir = Path(__file__).resolve().parent
    root = case_dir.parent.parent
    original = json.loads((case_dir / "production.json").read_text(encoding="utf-8"))
    records = []
    failed = False
    with tempfile.TemporaryDirectory(prefix=".validation-run-", dir=str(case_dir)) as directory:
        directory = Path(directory)
        cases = [("draft-positive", original, 0)]
        gap = copy.deepcopy(original)
        gap["timeline"][1]["start_seconds"] = 7
        gap["timeline"][1]["start_frame"] = 210
        gap["timeline"][1]["duration_seconds"] = 8
        cases.append(("negative-gap", gap, 1))
        ready = copy.deepcopy(original)
        ready["status"] = "ready"
        ready["execution_status"] = "rendered-reviewed"
        ready["rights_review_status"] = "approved"
        for asset in ready["assets"]:
            asset["availability"] = "available"
            asset["locator"] = "media/" + asset["id"] + {"audio": ".wav", "video": ".mp4", "image": ".png", "graphic": ".png"}[asset["kind"]]
        for right in ready["rights_ledger"]:
            if right["id"] != "rights-music":
                right["status"] = "cleared"
                right["evidence_status"] = "verified"
                right["evidence"] = "Synthetic test declaration; not a real clearance."
        for check in ready["qc"]:
            check["status"] = "pass"
            check["evidence"] = "Synthetic validator test; not a production claim."
        cases.append(("negative-unknown-ready", ready, 1))
        ready_positive = copy.deepcopy(ready)
        for right in ready_positive["rights_ledger"]:
            right["status"] = "cleared"
            right["evidence_status"] = "verified"
            right["evidence"] = "Synthetic validator-only clearance declaration, not real evidence."
        cases.append(("synthetic-ready-positive", ready_positive, 0))
        no_logo = copy.deepcopy(ready_positive)
        no_logo["assets"] = [item for item in no_logo["assets"] if item["id"] != "brand-logo"]
        for shot in no_logo["timeline"]:
            shot["asset_ids"] = [asset_id for asset_id in shot["asset_ids"] if asset_id != "brand-logo"]
        cases.append(("negative-ready-no-logo", no_logo, 1))
        unused_logo = copy.deepcopy(ready_positive)
        for shot in unused_logo["timeline"]:
            shot["asset_ids"] = [asset_id for asset_id in shot["asset_ids"] if asset_id != "brand-logo"]
        cases.append(("negative-ready-unused-logo", unused_logo, 1))
        fake_logo = copy.deepcopy(ready_positive)
        for asset in fake_logo["assets"]:
            if asset["id"] == "brand-logo":
                asset["origin"] = "generated"
        cases.append(("negative-ready-generated-logo", fake_logo, 1))
        internal_draft = copy.deepcopy(no_logo)
        internal_draft["status"] = "draft"
        internal_draft["execution_status"] = "planned-not-rendered"
        cases.append(("internal-draft-no-logo-positive", internal_draft, 0))
        missing = copy.deepcopy(original)
        missing["timeline"][0]["asset_ids"].append("missing-asset")
        cases.append(("negative-missing-asset", missing, 1))
        no_cjk = copy.deepcopy(original)
        no_cjk["narration"][1]["text"] = "Make one small runnable version."
        no_cjk["narration_full_text"] = "\n".join(item["text"] for item in no_cjk["narration"])
        cases.append(("negative-no-cjk", no_cjk, 1))
        for name, data, expected in cases:
            fixture = directory / (name + ".json")
            fixture.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            command = [sys.executable, "scripts/validate_production.py", str(fixture.relative_to(root))]
            result = subprocess.run(command, cwd=str(root), text=True, encoding="utf-8", capture_output=True)
            records += ["CASE: " + name, "EXPECTED_EXIT: " + str(expected), "COMMAND: python3 " + " ".join(command[1:]), "STDOUT:", result.stdout.rstrip(), "STDERR:", result.stderr.rstrip(), "EXIT_STATUS: " + str(result.returncode), ""]
            try:
                response = json.loads(result.stdout)
                matched = response["valid"] == (expected == 0)
            except (ValueError, KeyError):
                matched = False
            failed = failed or result.returncode != expected or not matched
        command = [sys.executable, "scripts/validate_production.py", "--help"]
        result = subprocess.run(command, cwd=str(root), text=True, encoding="utf-8", capture_output=True)
        records += ["CASE: help", "COMMAND: python3 scripts/validate_production.py --help", "STDOUT:", result.stdout.rstrip(), "STDERR:", result.stderr.rstrip(), "EXIT_STATUS: " + str(result.returncode), ""]
        failed = failed or result.returncode != 0
    records += ["OVERALL: " + ("FAIL" if failed else "PASS"), "Note: all ready cases use synthetic declarations to check the contract; no clearance or render was actually performed."]
    report = "\n".join(records) + "\n"
    (case_dir / "validation-results.txt").write_text(report, encoding="utf-8")
    print(report)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
