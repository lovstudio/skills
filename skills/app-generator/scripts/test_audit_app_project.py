#!/usr/bin/env python3
"""Regression tests for the app-generator project audit."""

from __future__ import annotations

import argparse
import json
import sys
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


class FinderQuickActionAuditTests(unittest.TestCase):
    def create_native_project(self, *, quick_action: bool) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        project_dir = root / "Sample.xcodeproj"
        extension_dir = root / "FinderQuickAction"
        host_dir = root / "Host"
        app_icon_dir = host_dir / "Assets.xcassets" / "AppIcon.appiconset"
        project_dir.mkdir()
        extension_dir.mkdir()
        host_dir.mkdir()
        app_icon_dir.mkdir(parents=True)
        (app_icon_dir / "Contents.json").write_text("{}", encoding="utf-8")

        if quick_action:
            project_text = """
            productType = "com.apple.product-type.app-extension";
            path = FinderQuickAction.appex;
            name = "Embed Foundation Extensions";
            dstSubfolderSpec = 13;
            """
            extension_plist = """
            <plist><dict><key>NSExtension</key><dict>
              <key>NSExtensionAttributes</key><dict>
                <key>NSExtensionActivationRule</key><dict>
                  <key>NSExtensionActivationSupportsImageWithMaxCount</key><integer>20</integer>
                </dict>
                <key>NSExtensionServiceAllowsFinderPreviewItem</key><true/>
                <key>NSExtensionServiceFinderPreviewLabel</key><string>Compress</string>
                <key>NSExtensionServiceFinderPreviewIconName</key><string>ActionIcon</string>
              </dict>
              <key>NSExtensionPointIdentifier</key><string>com.apple.services</string>
            </dict></dict></plist>
            """
            (extension_dir / "Info.plist").write_text(extension_plist, encoding="utf-8")
        else:
            project_text = 'productType = "com.apple.product-type.application";'
            service_plist = """
            <plist><dict><key>NSServices</key><array><dict></dict></array></dict></plist>
            """
            (host_dir / "Info.plist").write_text(service_plist, encoding="utf-8")

        (project_dir / "project.pbxproj").write_text(project_text, encoding="utf-8")
        return root

    @staticmethod
    def check(report: dict, check_id: str) -> dict:
        return next(check for check in report["checks"] if check["id"] == check_id)

    def test_accepts_headless_quick_action_using_services_extension_point(self) -> None:
        root = self.create_native_project(quick_action=True)
        report = audit(root, "macos", "finder-quick-action")

        self.assertEqual(report["native_integration"], "finder-quick-action")
        for check_id in (
            "finder-action-extension-target",
            "finder-quick-action-surface",
            "finder-quick-action-presentation",
            "finder-quick-action-embedding",
            "finder-quick-action-not-service-only",
        ):
            self.assertEqual(self.check(report, check_id)["status"], "ok")

    def test_rejects_traditional_service_as_quick_action_substitute(self) -> None:
        root = self.create_native_project(quick_action=False)
        report = audit(root, "macos", "finder-quick-action")

        self.assertEqual(
            self.check(report, "finder-action-extension-target")["status"],
            "missing",
        )
        service_only = self.check(report, "finder-quick-action-not-service-only")
        self.assertEqual(service_only["status"], "missing")
        self.assertIn("nsservices=True", service_only["detail"])

    def test_rejects_unbounded_true_predicate_activation_rule(self) -> None:
        root = self.create_native_project(quick_action=True)
        plist = root / "FinderQuickAction" / "Info.plist"
        text = plist.read_text(encoding="utf-8")
        text = text.replace(
            "<dict>\n                  <key>NSExtensionActivationSupportsImageWithMaxCount</key><integer>20</integer>\n                </dict>",
            "<string>TRUEPREDICATE</string>",
        )
        plist.write_text(text, encoding="utf-8")

        report = audit(root, "macos", "finder-quick-action")
        surface = self.check(report, "finder-quick-action-surface")
        self.assertEqual(surface["status"], "missing")
        self.assertIn("activation_rule=False", surface["detail"])

    def test_auto_detects_native_macos_project(self) -> None:
        root = self.create_native_project(quick_action=True)
        report = audit(root)

        self.assertEqual(report["app_type"], "macos")
        self.assertEqual(report["native_integration"], "finder-quick-action")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run app-generator audit regression tests.")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=1 + args.verbose).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
