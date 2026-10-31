from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hanzi_lens.py"
ENV_KEYS = (
    "SKILL_PROFILE_PATH",
    "SKILL_HANZI_LENS_OUTPUT_DIR",
    "SKILL_OUTPUT_DIR",
    "SKILL_HANZI_LENS_INFOGRAPHIC_SKILL_DIR",
    "LOVSTUDIO_SKILLS_INSTALL_DIR",
)


def load_hanzi_lens():
    spec = importlib.util.spec_from_file_location("hanzi_lens", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


HANZI_LENS = load_hanzi_lens()


class ConfigResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        env = {key: value for key, value in os.environ.items() if key not in ENV_KEYS}
        env["HOME"] = str(self.home)
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_default_profile_is_the_lovstudio_shared_profile(self) -> None:
        profile = self.home / ".lovstudio" / "skills" / "profile.json"
        profile.parent.mkdir(parents=True)
        profile.write_text(
            json.dumps({"workspace": {"output_dir": str(self.home / "out")}}),
            encoding="utf-8",
        )
        self.assertEqual(HANZI_LENS.shared_profile_path(), profile)
        self.assertEqual(HANZI_LENS.configured_output_root(), self.home / "out" / "hanzi-lens")

    def test_shared_install_dir_locates_the_infographic_dependency(self) -> None:
        cli = self.home / "skills" / "lov-professional-infographic" / "scripts" / "infographic_cli.py"
        cli.parent.mkdir(parents=True)
        cli.write_text("", encoding="utf-8")
        os.environ["LOVSTUDIO_SKILLS_INSTALL_DIR"] = str(self.home / "skills")
        self.assertEqual(HANZI_LENS.resolve_infographic_cli(None), cli)


if __name__ == "__main__":
    unittest.main()
