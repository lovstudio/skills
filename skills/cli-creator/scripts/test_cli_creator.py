#!/usr/bin/env python3
"""Smoke and contract tests for lov-cli-creator helper scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional


SKILL_ROOT = Path(__file__).resolve().parents[1]
INSPECTOR = SKILL_ROOT / "scripts" / "inspect_project.py"
SCAFFOLDER = SKILL_ROOT / "scripts" / "scaffold_cli.py"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_cli.py"


def run(*argv: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *argv],
        cwd=str(cwd or SKILL_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def sample_plan() -> dict:
    return {
        "schema": "lov-cli-plan/v1",
        "name": "Real Probe",
        "command": "lov-cli-real-probe",
        "description": "Inspect the sample project's real probe script through a typed CLI.",
        "backend": {
            "kind": "subprocess",
            "name": "Python",
            "executable": "python3",
            "install": "Install Python 3.9 or newer.",
            "timeout_seconds": 30,
        },
        "commands": [
            {
                "name": "probe",
                "description": "Read project state through the real project script.",
                "mutates": False,
                "argv": ["$PYTHON", "probe.py"],
                "parameters": [],
                "postconditions": ["Probe exits zero and returns project state"],
            }
        ],
    }


class CliCreatorTests(unittest.TestCase):
    def make_project(self, parent: Path) -> Path:
        project = parent / "real-probe"
        project.mkdir()
        (project / "README.md").write_text("# Real Probe\n", encoding="utf-8")
        (project / "package.json").write_text(
            json.dumps({"name": "real-probe", "bin": {"real-probe": "bin.js"}}),
            encoding="utf-8",
        )
        (project / "probe.py").write_text(
            "import json\nprint(json.dumps({'status': 'real-project'}))\n",
            encoding="utf-8",
        )
        (project / "cli.py").write_text(
            "import argparse\nargparse.ArgumentParser().parse_args()\n",
            encoding="utf-8",
        )
        return project

    def write_plan(self, parent: Path, value: Optional[Dict] = None) -> Path:
        plan = parent / "plan.json"
        plan.write_text(json.dumps(value or sample_plan(), indent=2), encoding="utf-8")
        return plan

    def test_inspector_detects_manifests_and_cli(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lov-cli-inspect-") as name:
            project = self.make_project(Path(name))
            result = run(str(INSPECTOR), "--format", "json", cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema"], "lov-cli-project-analysis/v1")
            self.assertIn("real-probe", payload["callable_surfaces"]["package_bins"])
            paths = {item["path"] for item in payload["callable_surfaces"]["cli_candidates"]}
            self.assertIn("cli.py", paths)

    def test_scaffold_runs_source_cli(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lov-cli-scaffold-") as name:
            parent = Path(name)
            project = self.make_project(parent)
            plan = self.write_plan(parent)
            result = run(str(SCAFFOLDER), "--plan", str(plan), "--json", cwd=project)
            self.assertEqual(result.returncode, 0, result.stderr)
            harness = project / "agent-harness"
            spec = json.loads((harness / "lov-cli.json").read_text(encoding="utf-8"))
            self.assertEqual(spec["status"], "scaffold")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(harness / "src")
            command = subprocess.run(
                [sys.executable, "-m", spec["package"], "--json", "probe"],
                cwd=str(parent),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(command.returncode, 0, command.stdout + command.stderr)
            payload = json.loads(command.stdout)
            self.assertTrue(payload["ok"])
            self.assertIn("real-project", payload["data"]["stdout"])

    def test_scaffold_rejects_occupied_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lov-cli-occupied-") as name:
            parent = Path(name)
            project = self.make_project(parent)
            plan = self.write_plan(parent)
            (project / "agent-harness").mkdir()
            result = run(str(SCAFFOLDER), str(project), "--plan", str(plan))
            self.assertEqual(result.returncode, 5)
            self.assertIn("already exists", result.stderr)

    def test_scaffold_rejects_shell_string_argv(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lov-cli-invalid-") as name:
            parent = Path(name)
            project = self.make_project(parent)
            invalid = sample_plan()
            invalid["commands"][0]["argv"] = "python3 probe.py"
            plan = self.write_plan(parent, invalid)
            result = run(str(SCAFFOLDER), str(project), "--plan", str(plan))
            self.assertEqual(result.returncode, 2)
            self.assertIn("argv", result.stderr)
            self.assertFalse((project / "agent-harness").exists())

    def test_validator_accepts_ready_source_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="lov-cli-validate-") as name:
            parent = Path(name)
            project = self.make_project(parent)
            plan = self.write_plan(parent)
            scaffold = run(str(SCAFFOLDER), str(project), "--plan", str(plan))
            self.assertEqual(scaffold.returncode, 0, scaffold.stderr)
            harness = project / "agent-harness"
            spec_path = harness / "lov-cli.json"
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["status"] = "ready"
            serialized = json.dumps(spec, indent=2) + "\n"
            spec_path.write_text(serialized, encoding="utf-8")
            package_spec = harness / "src" / spec["package"] / "cli_spec.json"
            package_spec.write_text(serialized, encoding="utf-8")
            test_doc = harness / "TEST.md"
            test_doc.write_text(
                test_doc.read_text(encoding="utf-8").replace(
                    "Status: scaffold. Replace this line with the exact test command, named results,\npass count, duration, artifact paths, and known gaps after execution.",
                    "Status: passed. Five named source-contract checks passed in the local smoke run.",
                ),
                encoding="utf-8",
            )
            result = run(str(VALIDATOR), str(harness))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("source-doctor-json", result.stdout)


if __name__ == "__main__":
    unittest.main()
