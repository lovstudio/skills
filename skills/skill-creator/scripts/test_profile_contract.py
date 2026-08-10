#!/usr/bin/env python3
"""Regression tests for the always-on Skill Creator Profile contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_skill.py"


class ProfileContractTests(unittest.TestCase):
    def run_command(self, command: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_creator_always_generates_profile_contract_and_store(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source_parent = workspace / "sources"
            install_dir = workspace / "installed"
            profile = workspace / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "user": {"language": "zh-CN"},
                        "brand": {"name": "Example Brand"},
                        "skills": {"lov-demo": {"profile": {"watermark": True}}},
                    }
                ),
                encoding="utf-8",
            )
            environment = dict(os.environ)
            environment["SKILL_PROFILE_PATH"] = str(profile)
            result = self.run_command(
                [
                    sys.executable,
                    str(INIT),
                    "demo",
                    "--path",
                    str(source_parent),
                    "--install-dir",
                    str(install_dir),
                ],
                environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            skill = source_parent / "demo-skill"
            manifest = yaml.safe_load((skill / "skill.yaml").read_text(encoding="utf-8"))
            self.assertEqual(manifest["context"]["profile"]["schema"], "user-profile/v1")
            self.assertEqual(
                manifest["context"]["profile"]["persist"]["records_path"],
                "skills.lov-demo.records",
            )
            self.assertTrue((skill / "references" / "user-profile.md").is_file())
            self.assertTrue((skill / "scripts" / "profile_store.py").is_file())

            missing_confirmation = self.run_command(
                [
                    sys.executable,
                    str(skill / "scripts" / "profile_store.py"),
                    "record",
                    "--skill-id",
                    "lov-demo",
                    "--path",
                    "records.subtitle_level",
                    "--value",
                    json.dumps("cet4"),
                ],
                environment,
            )
            self.assertEqual(missing_confirmation.returncode, 2)

            saved = self.run_command(
                [
                    sys.executable,
                    str(skill / "scripts" / "profile_store.py"),
                    "record",
                    "--skill-id",
                    "lov-demo",
                    "--path",
                    "records.subtitle_level",
                    "--value",
                    json.dumps("cet4"),
                    "--confirm",
                ],
                environment,
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)
            persisted = json.loads(profile.read_text(encoding="utf-8"))
            self.assertEqual(persisted["brand"]["name"], "Example Brand")
            self.assertEqual(persisted["skills"]["lov-demo"]["profile"]["watermark"], True)
            self.assertEqual(persisted["skills"]["lov-demo"]["records"]["subtitle_level"], "cet4")

            read_back = self.run_command(
                [
                    sys.executable,
                    str(skill / "scripts" / "profile_store.py"),
                    "read",
                    "--skill-id",
                    "lov-demo",
                ],
                environment,
            )
            self.assertEqual(read_back.returncode, 0, read_back.stderr)
            context = json.loads(read_back.stdout)
            self.assertEqual(context["brand"]["name"], "Example Brand")
            self.assertEqual(context["records"]["subtitle_level"], "cet4")


if __name__ == "__main__":
    unittest.main()
