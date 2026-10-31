#!/usr/bin/env python3
"""Regression tests for the shared profile location used by media_config."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import media_config


class SharedProfileLocationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        env = {key: value for key, value in os.environ.items() if key != "SKILL_PROFILE_PATH"}
        env["HOME"] = str(self.home)
        patcher = patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_default_profile_is_lovstudio_shared_profile(self) -> None:
        self.assertEqual(
            media_config.profile_path(),
            self.home / ".lovstudio" / "skills" / "profile.json",
        )

    def test_init_write_updates_lovstudio_profile_and_keeps_other_keys(self) -> None:
        profile = self.home / ".lovstudio" / "skills" / "profile.json"
        profile.parent.mkdir(parents=True)
        profile.write_text(json.dumps({"sites": {"lovstudio_web": "$HOME/web"}}), encoding="utf-8")

        with patch("sys.argv", ["media_config.py", "init", "--write", "--json"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(media_config.main(), 0)

        saved = json.loads(profile.read_text(encoding="utf-8"))
        self.assertEqual(saved["sites"], {"lovstudio_web": "$HOME/web"})
        self.assertEqual(saved["media_fetch"]["config_version"], 2)
        self.assertFalse((self.home / ".skill-publisher").exists())
