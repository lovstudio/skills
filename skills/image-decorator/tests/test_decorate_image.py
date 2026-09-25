from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "decorate_image.py"


class DecorateImageTest(unittest.TestCase):
    def test_default_caption_and_logo(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = work / "source.png"
            output = work / "decorated.png"
            profile = work / "profile.json"
            profile.write_text("{}\n", encoding="utf-8")
            Image.new("RGB", (800, 450), "#8094A3").save(source)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                    "--profile",
                    str(profile),
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["caption"], "Powered by lovstudio.ai/skill/image-decorator")
            self.assertEqual(result["caption_source"], "fallback")
            self.assertEqual(result["logo_source"], "bundled")
            self.assertEqual(result["width"], 836)
            self.assertGreater(result["height"], 540)
            self.assertEqual(len(result["sha256"]), 64)
            with Image.open(output) as image:
                self.assertEqual(image.size, (result["width"], result["height"]))
                padding = result["decoration"]["outer_padding"]
                preserved = image.convert("RGBA").crop((padding, padding, padding + 800, padding + 450))
                with Image.open(source) as original:
                    self.assertIsNone(ImageChops.difference(preserved, original.convert("RGBA")).getbbox())

    def test_explicit_caption_and_jpeg(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = work / "source.jpg"
            output = work / "decorated.jpg"
            profile = work / "profile.json"
            profile.write_text("{}\n", encoding="utf-8")
            Image.new("RGB", (640, 480), "#CC785C").save(source)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                    "--caption",
                    "本期封面：测试图片",
                    "--profile",
                    str(profile),
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["caption_source"], "explicit")
            self.assertEqual(result["format"], "jpg")
            with Image.open(output) as image:
                self.assertEqual(image.mode, "RGB")

    def test_screenshot_caption_is_flush_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = work / "screenshot.png"
            output = work / "decorated.png"
            profile = work / "profile.json"
            profile.write_text("{}\n", encoding="utf-8")
            Image.new("RGB", (800, 450), "#E2E5EE").save(source)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                    "--caption",
                    "插件市场搜索结果",
                    "--style",
                    "screenshot-caption",
                    "--profile",
                    str(profile),
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["style"], "screenshot-caption")
            self.assertEqual(result["width"], 800)
            self.assertEqual(result["decoration"]["frame"], "none")
            self.assertEqual(result["decoration"]["outer_padding"], 0)
            self.assertEqual(result["decoration"]["corner_radius"], 0)
            with Image.open(output) as image, Image.open(source) as original:
                preserved = image.convert("RGBA").crop((0, 0, 800, 450))
                self.assertIsNone(
                    ImageChops.difference(preserved, original.convert("RGBA")).getbbox()
                )

    def test_screenshot_caption_removes_transparent_shadow_canvas(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = work / "screenshot.png"
            output = work / "decorated.png"
            profile = work / "profile.json"
            profile.write_text("{}\n", encoding="utf-8")
            image = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
            image.paste((255, 255, 255, 255), (40, 40, 760, 560))
            image.save(source)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(source),
                    "--output",
                    str(output),
                    "--caption",
                    "无外框截图",
                    "--style",
                    "screenshot-caption",
                    "--profile",
                    str(profile),
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["input_width"], 800)
            self.assertEqual(result["content_width"], 720)
            self.assertEqual(result["content_height"], 520)
            self.assertEqual(result["decoration"]["source_crop"], [40, 40, 760, 560])
            self.assertEqual(
                result["decoration"]["alpha_treatment"],
                "opaque-bounds-flatten",
            )
            with Image.open(output) as decorated:
                self.assertEqual(decorated.getpixel((0, 0))[3], 255)


if __name__ == "__main__":
    unittest.main()
