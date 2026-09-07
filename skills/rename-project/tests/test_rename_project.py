from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "rename_project.py"
SPEC = importlib.util.spec_from_file_location("rename_project", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
rename_project = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rename_project)


class RenameProjectScanTests(unittest.TestCase):
    def test_default_generated_directories_are_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("codex-diy\n", encoding="utf-8")
            for directory in (".runtime", ".codex-upstream"):
                generated = root / directory
                generated.mkdir()
                (generated / "metadata.json").write_text("codex-diy\n", encoding="utf-8")

            plan = rename_project.scan(root, "codex-diy", "codeex", False, [], False, [])

            self.assertEqual([item["path"] for item in plan["candidates"]], ["README.md"])
            self.assertIn(".runtime", plan["skip_dirs"])
            self.assertIn(".codex-upstream", plan["skip_dirs"])

    def test_custom_generated_directory_can_be_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            generated = root / "private-build-cache"
            generated.mkdir()
            (generated / "manifest.json").write_text("codex-diy\n", encoding="utf-8")

            plan = rename_project.scan(
                root,
                "codex-diy",
                "codeex",
                False,
                [],
                False,
                [],
                ["private-build-cache"],
            )

            self.assertEqual(plan["candidates"], [])
            self.assertIn("private-build-cache", plan["skip_dirs"])

    def test_invalid_pattern_still_writes_failure_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            report = root / "failure.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "codeex",
                    "--root",
                    str(root),
                    "--old-name",
                    "codex-diy",
                    "--preserve",
                    "[",
                    "--report",
                    str(report),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "error")
            self.assertIn("invalid --preserve regex", payload["error"])


if __name__ == "__main__":
    unittest.main()
