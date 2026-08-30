import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_decision_guide.py"


class DecisionGuideValidatorTests(unittest.TestCase):
    def run_validator(self, markdown: str):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            report.write_text(markdown, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--report", str(report), "--strict"],
                capture_output=True,
                text=True,
            )
            return result.returncode, json.loads(result.stdout)

    def test_accepts_svg_and_textual_outcomes(self):
        code, payload = self.run_validator("""## Decision Guide

<svg data-decision-guide role="img"><title>Flow</title></svg>

### Outcome Map

- 推荐 A
- 停止 B
- 前置条件 C

## Finding 1
""")
        self.assertEqual(0, code)
        self.assertEqual("pass", payload["status"])

    def test_rejects_table_only_selection(self):
        code, payload = self.run_validator("""## Decision Guide

| Option | Score |
|---|---|
| A | 5 |
""")
        self.assertNotEqual(0, code)
        self.assertIn("Decision Guide missing a branching visual", payload["errors"])


if __name__ == "__main__":
    unittest.main()
