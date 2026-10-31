from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_workbuddy_connector.py"
INIT_SCRIPTS = (
    ROOT / "scripts" / "init_bp.py",
    ROOT / "skills" / "bp-outline" / "scripts" / "init_bp.py",
)
GIT_URL = "https://github.com/lovstudio/bp-skill"


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_workbuddy_connector", BUILD)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


class WorkBuddyPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.package = Path(cls.tmp.name) / "package"
        subprocess.run(
            [sys.executable, str(BUILD), "--output-dir", str(cls.package)],
            check=True,
            capture_output=True,
            text=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_generated_skills_carry_the_brand_author_and_github_source(self) -> None:
        skills = sorted((self.package / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 4)
        for skill in skills:
            with self.subTest(skill=skill.parent.name):
                frontmatter = skill.read_text(encoding="utf-8").split("---\n")[1]
                self.assertIn("\nauthor: Lovstudio.AI\n", frontmatter)
                self.assertIn(f"\ngit_url: {GIT_URL}\n", frontmatter)
        meta = json.loads((self.package / "connector-meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["git_url"], GIT_URL)

    def test_validation_rejects_a_private_home_path(self) -> None:
        module = load_build_module()
        leaked = self.package / "leak.md"
        leaked.write_text("See /Users/mark/lovstudio/output\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(ValueError, "private absolute path"):
                module.validate_package(self.package)
        finally:
            leaked.unlink()


class DefaultProfileTests(unittest.TestCase):
    def test_init_reads_the_lovstudio_shared_profile(self) -> None:
        for script in INIT_SCRIPTS:
            with self.subTest(script=str(script.relative_to(ROOT))):
                with tempfile.TemporaryDirectory() as tmp:
                    home = Path(tmp)
                    profile = home / ".lovstudio" / "skills" / "profile.json"
                    profile.parent.mkdir(parents=True)
                    profile.write_text(
                        json.dumps({"workspace": {"output_dir": str(home / "out")}}),
                        encoding="utf-8",
                    )
                    env = {
                        key: value
                        for key, value in os.environ.items()
                        if key not in {"SKILL_PROFILE_PATH", "SKILL_BP_OUTPUT_DIR", "SKILL_OUTPUT_DIR"}
                    }
                    env["HOME"] = str(home)
                    result = subprocess.run(
                        [sys.executable, str(script), "--name", "Acme", "--json"],
                        cwd=tmp,
                        env=env,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    workspace = Path(json.loads(result.stdout)["workspace"])
                    self.assertEqual(workspace, (home / "out" / "acme-business-plan").resolve())


if __name__ == "__main__":
    unittest.main()
