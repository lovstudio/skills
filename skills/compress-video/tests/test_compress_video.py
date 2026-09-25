#!/usr/bin/env python3
"""Regression tests for scripts/compress_video.py. Requires ffmpeg and ffprobe."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compress_video.py"


def make_clip(path: Path, seconds: float = 3, size: str = "1280x720", crf: int = 10) -> None:
    """A noisy, high-bitrate H.264 clip so that compression has something to remove."""
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
        "-t", str(seconds), "-c:v", "libx264", "-crf", str(crf), "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(path),
    ], check=True)


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg is required")
class CompressVideoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name).resolve()
        cls.src = cls.dir / "clip.mov"
        make_clip(cls.src)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def run_cli(self, *args: str, expect: int = 0) -> tuple[dict, str]:
        env = {**os.environ, "SKILL_PROFILE_PATH": str(self.dir / "no-profile.json")}
        proc = subprocess.run([sys.executable, str(SCRIPT), *args, "--json", "-q"],
                              capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, expect, proc.stderr)
        return json.loads(proc.stdout), proc.stderr

    def test_default_compresses_to_hevc_and_keeps_source(self) -> None:
        payload, _ = self.run_cli(str(self.src), "--preset", "ultrafast")
        result = payload["results"][0]
        self.assertEqual(result["status"], "compressed")
        out = Path(result["output"])
        self.assertEqual(out.name, "clip-compressed.mp4")
        self.assertTrue(self.src.exists())
        self.assertLess(result["output_size"], result["input_size"] * 0.5)
        self.assertTrue(result["duration_ok"])
        info = probe(out)
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        self.assertEqual(video["codec_name"], "hevc")
        self.assertEqual((video["width"], video["height"]), (1280, 720))
        self.assertEqual(result["crf"], 28)
        self.assertFalse(result["replaced"])
        # Refuses to overwrite silently.
        self.run_cli(str(self.src), "--preset", "ultrafast", expect=1)
        out.unlink()

    def test_dry_run_prints_command_without_output(self) -> None:
        payload, _ = self.run_cli(str(self.src), "--dry-run", "--quality", "smallest")
        result = payload["results"][0]
        self.assertEqual(result["status"], "dry-run")
        self.assertIn("libx265", result["command"])
        self.assertIn("slow", result["command"])
        self.assertFalse((self.dir / "clip-compressed.mp4").exists())

    def test_max_edge_scales_and_h264_codec(self) -> None:
        out = self.dir / "scaled.mp4"
        payload, _ = self.run_cli(str(self.src), "--output", str(out), "--max-edge", "640",
                                  "--codec", "h264", "--preset", "ultrafast")
        result = payload["results"][0]
        self.assertEqual(result["status"], "compressed")
        video = next(s for s in probe(out)["streams"] if s["codec_type"] == "video")
        self.assertEqual((video["codec_name"], video["width"], video["height"]), ("h264", 640, 360))
        self.assertEqual(result["crf"], 25)

    def test_target_size_two_pass_fits_budget(self) -> None:
        out = self.dir / "budget.mp4"
        payload, _ = self.run_cli(str(self.src), "--output", str(out), "--target-size", "300k",
                                  "--preset", "ultrafast")
        result = payload["results"][0]
        self.assertEqual(result["status"], "compressed")
        self.assertLessEqual(out.stat().st_size, 300 * 1024 * 1.10)

    def test_vmaf_is_measured_when_requested(self) -> None:
        out = self.dir / "vmaf.mp4"
        payload, _ = self.run_cli(str(self.src), "--output", str(out), "--vmaf", "--preset", "ultrafast")
        result = payload["results"][0]
        self.assertIsNotNone(result["vmaf"])
        self.assertGreater(result["vmaf"], 70)

    def test_replace_mode_swaps_source_for_mp4(self) -> None:
        victim = self.dir / "replace-me.mov"
        shutil.copy(self.src, victim)
        payload, _ = self.run_cli(str(victim), "--replace", "--permanent", "--preset", "ultrafast")
        result = payload["results"][0]
        self.assertEqual(result["status"], "compressed")
        self.assertTrue(result["replaced"])
        self.assertFalse(victim.exists())
        self.assertTrue((self.dir / "replace-me.mp4").exists())
        self.assertFalse((self.dir / "replace-me.part.mp4").exists())

    def test_already_compact_source_is_left_alone(self) -> None:
        tiny = self.dir / "tiny.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:size=320x240:rate=10",
                        "-t", "2", "-c:v", "libx265", "-crf", "45", "-preset", "ultrafast", "-tag:v", "hvc1",
                        "-x265-params", "log-level=error", str(tiny)], check=True)
        payload, _ = self.run_cli(str(tiny), "--preset", "ultrafast", "--replace", "--permanent")
        result = payload["results"][0]
        self.assertEqual(result["status"], "skipped-larger")
        self.assertTrue(tiny.exists())
        self.assertIsNone(result["output"])
        self.assertFalse((self.dir / "tiny.part.mp4").exists())


if __name__ == "__main__":
    unittest.main()
