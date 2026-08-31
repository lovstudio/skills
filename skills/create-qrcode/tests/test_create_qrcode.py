from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "create_qrcode.py"


class CreateQrCodeTests(unittest.TestCase):
    def run_cli(self, *arguments: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_creates_private_receipt_without_payload(self) -> None:
        payload = "WIFI:T:WPA;S:测试网络;P:not-a-real-secret;;"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "qr.png"
            result = self.run_cli(
                "--stdin",
                "--no-profile",
                "--output",
                str(output),
                "--verify",
                "structure",
                "--json",
                input_text=payload,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertTrue(output.is_file())
            self.assertNotIn(payload, result.stdout)
            self.assertEqual(receipt["payload_bytes"], len(payload.encode("utf-8")))
            self.assertEqual(receipt["verification"], "structure")
            self.assertFalse(receipt["poster"])
            self.assertFalse(receipt["payload_disclosed"])
            self.assertEqual(receipt["width"], receipt["size"])
            self.assertEqual(receipt["height"], receipt["size"])
            with Image.open(output) as image:
                self.assertEqual(image.format, "PNG")

    def test_profile_preferences_are_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "skills": {
                            "lov-create-qrcode": {
                                "records": {
                                    "default_palette": "clay",
                                    "default_shape": "square",
                                    "default_size": 384,
                                    "default_error_correction": "Q",
                                    "default_border": 5,
                                    "default_poster": False,
                                    "default_show_data": False,
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            output = root / "profile-qr.png"
            result = self.run_cli(
                "https://example.com/profile",
                "--profile",
                str(profile),
                "--output",
                str(output),
                "--verify",
                "structure",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["palette"], "clay")
            self.assertEqual(receipt["shape"], "square")
            self.assertEqual(receipt["size"], 384)
            self.assertEqual(receipt["error_correction"], "Q")
            self.assertEqual(receipt["border_modules"], 5)
            self.assertEqual(receipt["sources"]["palette"], "skill-record")

    def test_rejects_low_contrast_without_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "unsafe.png"
            result = self.run_cli(
                "https://example.com",
                "--no-profile",
                "--foreground",
                "#BBBBBB",
                "--background",
                "#FFFFFF",
                "--output",
                str(output),
                "--json",
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())
            self.assertIn("contrast", result.stderr)


if __name__ == "__main__":
    unittest.main()
