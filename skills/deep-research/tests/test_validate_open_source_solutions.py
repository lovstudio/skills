#!/usr/bin/env python3
"""Smoke tests for validate_open_source_solutions.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_open_source_solutions.py"


class ValidateOpenSourceSolutionsTest(unittest.TestCase):
    def test_valid_solution_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            artifact = directory / "open_source_solutions.jsonl"
            report = directory / "report.md"
            url = "https://github.com/example/project"
            artifact.write_text(
                json.dumps(
                    {
                        "name": "project",
                        "canonical_url": url,
                        "forge": "github",
                        "description": "verified test project",
                        "license": "MIT",
                        "last_activity_at": "2026-08-30",
                        "retrieved_at": "2026-08-30",
                        "implementation_mechanism": "browser automation",
                        "evidence_url": f"{url}/blob/abc/publish.py",
                        "verification_status": "code_verified",
                        "fit": "reference",
                        "risks": ["test risk"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            report.write_text(
                f"## Open-Source Solutions Landscape\n\n[{url}]({url})\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(SCRIPT), "--artifact", str(artifact), "--report", str(report), "--strict"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "open_source_solutions.jsonl"
            artifact.write_text('{"name":"incomplete"}\n', encoding="utf-8")
            result = subprocess.run(
                ["python3", str(SCRIPT), "--artifact", str(artifact), "--strict"],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
