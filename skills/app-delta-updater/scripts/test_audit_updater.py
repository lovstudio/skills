#!/usr/bin/env python3
"""Focused regression tests for the static updater audit."""

from __future__ import annotations

import argparse
import base64
import json
import tempfile
import unittest
from pathlib import Path

import audit_updater


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write(path, json.dumps(value))


def public_key() -> str:
    return base64.b64encode(b"untrusted comment: minisign public key\nfixture-public-key").decode("ascii")


def checks_by_id(checks: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {check["id"]: check for check in checks}


def create_tauri_fixture(root: Path, updater_key: str) -> None:
    write_json(
        root / "package.json",
        {
            "dependencies": {
                "@tauri-apps/plugin-process": "2",
                "@tauri-apps/plugin-updater": "2",
            }
        },
    )
    write(
        root / "src-tauri" / "Cargo.toml",
        "tauri-plugin-updater = \"2\"\ntauri-plugin-process = \"2\"\n",
    )
    write_json(
        root / "src-tauri" / "tauri.conf.json",
        {
            "bundle": {"createUpdaterArtifacts": True},
            "plugins": {
                "updater": {
                    "pubkey": updater_key,
                    "endpoints": ["https://updates.lovstudio.test/latest.json"],
                }
            },
        },
    )
    write_json(
        root / "src-tauri" / "capabilities" / "default.json",
        {"permissions": ["updater:default", "process:default"]},
    )
    write(
        root / "src-tauri" / "src" / "lib.rs",
        "tauri::Builder::default()\n"
        "  .plugin(tauri_plugin_updater::Builder::new().build())\n"
        "  .plugin(tauri_plugin_process::init());\n",
    )
    write(
        root / "src" / "updater.ts",
        'import { check } from "@tauri-apps/plugin-updater";\n'
        'import { relaunch } from "@tauri-apps/plugin-process";\n'
        "void check();\nvoid relaunch();\n",
    )
    write(
        root / ".github" / "workflows" / "release.yml",
        "env:\n  TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}\n"
        "steps:\n  - uses: tauri-apps/tauri-action@v1\n    with:\n      uploadUpdaterJson: true\n",
    )


class AuditUpdaterTests(unittest.TestCase):
    def test_tauri_complete_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_tauri_fixture(root, public_key())
            checks = checks_by_id(audit_updater.audit_tauri(root))

        self.assertTrue(all(check["status"] == "pass" for check in checks.values()))

    def test_tauri_placeholder_public_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            create_tauri_fixture(root, "REPLACE_WITH_YOUR_PUBLIC_KEY")
            checks = checks_by_id(audit_updater.audit_tauri(root))

        self.assertEqual(checks["public-key"]["status"], "fail")

    def test_electron_ignores_node_modules_and_does_not_require_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(
                root / "package.json",
                {
                    "dependencies": {"electron": "30", "electron-updater": "6"},
                    "build": {"publish": {"provider": "generic"}, "afterSign": "scripts/sign.js"},
                },
            )
            write(root / "src" / "main.ts", "export const applicationReady = true;\n")
            write(
                root / "node_modules" / "dependency" / "updater.ts",
                "import { autoUpdater } from 'electron'; autoUpdater.checkForUpdates();\n",
            )
            checks = checks_by_id(audit_updater.audit_electron(root))

        self.assertEqual(checks["runtime-check"]["status"], "fail")
        self.assertEqual(checks["delta-metadata"]["status"], "info")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    unittest.main()


if __name__ == "__main__":
    main()
