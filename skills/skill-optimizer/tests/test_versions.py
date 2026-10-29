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
  Demo skill used by version tests. Use when the user mentions "demo skill".
license: MIT
metadata:
  author: lovstudio
  version: "0.1.1"
  tags: demo
---

# Demo
"""

PRICING_CARD = """schema: lovstudio/pricing-card/v1
version: "0.1.0"
model: one_time
list_price_cny: 19.9
credits: 280
distribution:
  version: "keep-nested"
"""


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
    )


class VersionSetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.skill = Path(self.tmp.name) / "demo-skill"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
        (self.skill / "README.md").write_text(
            "# Demo\n\n![Version](https://img.shields.io/badge/version-0.1.1-CC785C)\n",
            encoding="utf-8",
        )
        (self.skill / "skill.yaml").write_text('id: lov-demo\nversion: "0.1.1"\n', encoding="utf-8")
        (self.skill / "skill-card.yaml").write_text(
            'schema: lovstudio/skill-card/v1\nversion: "0.1.1"\n', encoding="utf-8"
        )
        (self.skill / "pricing-card.yaml").write_text(PRICING_CARD, encoding="utf-8")

    def version_of(self, name):
        for line in (self.skill / name).read_text(encoding="utf-8").splitlines():
            if line.startswith("version:"):
                return line.split(":", 1)[1].strip().strip('"')
        return None

    def test_bump_moves_both_cards_with_the_version_set(self):
        result = run(
            "bump_version.py", "--path", str(self.skill), "--type", "patch", "-m", "fix", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertIn("skill-card.yaml", report["changed"])
        self.assertIn("pricing-card.yaml", report["changed"])
        self.assertEqual(report["versions_before"]["pricing-card.yaml"], "0.1.0")
        for name in ("skill.yaml", "skill-card.yaml", "pricing-card.yaml"):
            self.assertEqual(self.version_of(name), "0.1.2", name)
        pricing = (self.skill / "pricing-card.yaml").read_text(encoding="utf-8")
        self.assertIn("list_price_cny: 19.9", pricing)
        self.assertIn("credits: 280", pricing)
        self.assertIn('  version: "keep-nested"', pricing)

    def test_card_without_version_stays_without_one(self):
        (self.skill / "pricing-card.yaml").write_text(
            "schema: lovstudio/pricing-card/v1\nmodel: free\n", encoding="utf-8"
        )
        result = run("bump_version.py", "--path", str(self.skill), "--type", "patch", "-m", "fix")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(self.version_of("pricing-card.yaml"))

    def test_lint_reports_a_stale_pricing_card(self):
        result = run("lint_skill.py", "--path", str(self.skill), "--json")
        report = json.loads(result.stdout)
        drift = [f for f in report["findings"] if f["code"] == "VERSION_DRIFT"]
        self.assertEqual(len(drift), 1, report["findings"])
        self.assertIn("pricing-card.yaml=0.1.0", drift[0]["message"])

    def test_lint_accepts_an_aligned_version_set(self):
        (self.skill / "pricing-card.yaml").write_text(
            PRICING_CARD.replace('version: "0.1.0"', 'version: "0.1.1"'), encoding="utf-8"
        )
        result = run("lint_skill.py", "--path", str(self.skill), "--json")
        codes = [f["code"] for f in json.loads(result.stdout)["findings"]]
        self.assertNotIn("VERSION_DRIFT", codes)


if __name__ == "__main__":
    unittest.main()
