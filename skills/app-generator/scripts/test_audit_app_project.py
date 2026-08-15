#!/usr/bin/env python3
"""Regression tests for the app-generator project audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_app_project import audit


class LovinspAuditTests(unittest.TestCase):
    def create_project(self, vite_config: str, dependencies: dict[str, str]) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        package = {
            "dependencies": {"react": "latest", **dependencies},
            "devDependencies": {"vite": "latest"},
        }
        (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
        (root / "vite.config.ts").write_text(vite_config, encoding="utf-8")
        return root

    @staticmethod
    def lovinsp_check(root: Path) -> dict:
        report = audit(root, "web")
        return next(check for check in report["checks"] if check["id"] == "lovinsp")

    def test_accepts_lovinsp_before_framework_plugin(self) -> None:
        root = self.create_project(
            """
            import { lovinspPlugin } from 'lovinsp';
            import react from '@vitejs/plugin-react';
            export default { plugins: [lovinspPlugin({ bundler: 'vite' }), react()] };
            """,
            {"lovinsp": "latest"},
        )
        self.assertEqual(self.lovinsp_check(root)["status"], "ok")

    def test_rejects_lovinsp_after_framework_plugin(self) -> None:
        root = self.create_project(
            """
            import { lovinspPlugin } from 'lovinsp';
            import react from '@vitejs/plugin-react';
            export default { plugins: [react(), lovinspPlugin({ bundler: 'vite' })] };
            """,
            {"lovinsp": "latest"},
        )
        check = self.lovinsp_check(root)
        self.assertEqual(check["status"], "missing")
        self.assertIn("order_ok=False", check["detail"])

    def test_rejects_legacy_code_inspector_residue(self) -> None:
        root = self.create_project(
            """
            import { lovinspPlugin } from 'lovinsp';
            import react from '@vitejs/plugin-react';
            export default { plugins: [lovinspPlugin({ bundler: 'vite' }), react()] };
            """,
            {"lovinsp": "latest", "code-inspector-plugin": "latest"},
        )
        check = self.lovinsp_check(root)
        self.assertEqual(check["status"], "missing")
        self.assertIn("legacy_remains=True", check["detail"])


if __name__ == "__main__":
    unittest.main()
