import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

SKILL_MD = """---
name: lov-demo
description: >
  Demo skill used by portability tests. Use when the user mentions "demo skill".
license: MIT
compatibility: Python 3.8+
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: demo
---

# Demo

Write drafts into ~/lovstudio/coding/demo before review.
"""


class PortabilityTests(unittest.TestCase):
    def test_lint_flags_the_private_lovstudio_workspace_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "demo-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
            (skill / "README.md").write_text(
                "# Demo\n\nProfile: ~/.lovstudio/skills/profile.json\n", encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "lint_skill.py"), "--path", str(skill), "--json"],
                capture_output=True,
                text=True,
            )
            findings = json.loads(result.stdout)["findings"]
            hits = [f for f in findings if f["code"] == "LOCAL_LOVSTUDIO_PATH"]
            self.assertEqual([f["file"] for f in hits], ["SKILL.md"], findings)
            self.assertEqual(hits[0]["severity"], "warn")
            self.assertIn("~/lovstudio", hits[0]["message"])


if __name__ == "__main__":
    unittest.main()
