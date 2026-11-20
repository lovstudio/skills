from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPTS = (
    ROOT / "scripts" / "init_bp.py",
    ROOT / "skills" / "bp-outline" / "scripts" / "init_bp.py",
)


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
