from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "find_logo.py"


def load_find_logo():
    spec = importlib.util.spec_from_file_location("find_logo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve string annotations through sys.modules.
    sys.modules["find_logo"] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop("find_logo", None)
    return module


class DefaultOutputTests(unittest.TestCase):
    def test_default_archive_root_is_lovstudio_logo_collection(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            env = {key: value for key, value in os.environ.items() if key != "SKILL_FIND_LOGO_OUTPUT_DIR"}
            env["HOME"] = home
            with mock.patch.dict(os.environ, env, clear=True):
                module = load_find_logo()
            self.assertEqual(module.DEFAULT_OUT, Path(home) / ".lovstudio" / "logo-collection")

    def test_environment_override_still_wins(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            with mock.patch.dict(os.environ, {"SKILL_FIND_LOGO_OUTPUT_DIR": root}):
                module = load_find_logo()
            self.assertEqual(module.DEFAULT_OUT, Path(root))


if __name__ == "__main__":
    unittest.main()
