from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
ENV_KEYS = (
    "SKILL_PROFILE_PATH",
    "AGENT_SKILL_PROFILE",
    "SKILL_SKILL_PROFILE",
    "SKILL_MAINTAIN_PARTNERS_SITE_ROOT",
    "SKILL_WEB_ROOT",
    "PARTNERS_SITE_ROOT",
    "SKILL_MAINTAIN_PARTNERS_FILE",
    "SKILL_PARTNERS_FILE",
    "PARTNERS_FILE",
)


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPTS = [load_script("add_partner"), load_script("audit_partners")]


class DefaultProfileResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.site = Path(self.tmp.name) / "site"
        (self.site / "app" / "(main)" / "(home)").mkdir(parents=True)
        (self.site / "public").mkdir()
        env = {key: value for key, value in os.environ.items() if key not in ENV_KEYS}
        env["HOME"] = str(self.home)
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def write_profile(self, data: dict) -> None:
        profile = self.home / ".lovstudio" / "skills" / "profile.json"
        profile.parent.mkdir(parents=True)
        profile.write_text(json.dumps(data), encoding="utf-8")

    def test_reads_sites_lovstudio_web_from_default_profile(self) -> None:
        self.write_profile({"sites": {"lovstudio_web": str(self.site)}})
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                self.assertEqual(script.resolve_repo(None), self.site)

    def test_reads_lovstudio_web_root_from_default_profile(self) -> None:
        self.write_profile({"lovstudio": {"web_root": str(self.site)}})
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                self.assertEqual(script.resolve_repo(None), self.site)

    def test_lovstudio_partners_file_takes_precedence_over_default_grid(self) -> None:
        home_dir = self.site / "app" / "(main)" / "(home)"
        (home_dir / "PartnersGrid.tsx").write_text("const PARTNERS = []\n", encoding="utf-8")
        custom = self.site / "components" / "Partners.tsx"
        custom.parent.mkdir()
        custom.write_text("export const PARTNERS = []\n", encoding="utf-8")
        self.write_profile({"lovstudio": {"partners_file": "components/Partners.tsx"}})
        for script in SCRIPTS:
            with self.subTest(script=script.__name__):
                self.assertEqual(script.resolve_partners_file(self.site, None), custom)


if __name__ == "__main__":
    unittest.main()
