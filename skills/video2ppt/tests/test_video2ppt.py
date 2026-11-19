#!/usr/bin/env python3
"""End-to-end check on a synthetic three-slide video (needs ffmpeg, Pillow, python-pptx)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "video2ppt.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def make_video(path: Path) -> None:
    # red 3s -> blue 3s -> white 3s; a black band flashes in the bottom 20px during 7-8s,
    # like a subtitle line, to prove the crop keeps it out of the comparison.
    inputs = []
    for colour in ("red", "blue", "white"):
        inputs += ["-f", "lavfi", "-i", f"color=c={colour}:s=320x180:d=3:r=10"]
    graph = ("[0][1][2]concat=n=3:v=1:a=0,"
             "drawbox=x=0:y=160:w=320:h=20:c=black:t=fill:enable='between(t,7,7.9)'[v]")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
                    "-filter_complex", graph, "-map", "[v]", "-pix_fmt", "yuv420p", str(path)],
                   check=True)


class Video2PptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.video = cls.root / "in.mp4"
        make_video(cls.video)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def extract(self, out, *extra):
        result = run("extract", str(self.video), str(out), "--name", "deck", "--json", *extra)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_hist_default_finds_three_slides(self):
        report = self.extract(self.root / "hist")
        self.assertEqual(report["frames_kept"], 3)
        from pptx import Presentation
        self.assertEqual(len(Presentation(report["outputs"]["pptx"]).slides), 3)

    def test_pixel_crop_ignores_noise_outside_region(self):
        noisy = self.extract(self.root / "noisy", "--method", "pixel", "--similarity", "0.995")
        clean = self.extract(self.root / "crop", "--method", "pixel", "--similarity", "0.995",
                             "--crop", "320:160:0:0")
        self.assertGreater(noisy["frames_kept"], 3)
        self.assertEqual(clean["frames_kept"], 3)

    def test_refuses_overwrite_and_pack_drop_add(self):
        out = self.root / "pack"
        self.extract(out)
        again = run("extract", str(self.video), str(out), "--name", "deck")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("--overwrite", again.stderr)

        result = run("pack", str(out), "--drop", "2", "--add", "00:00:04", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["frames_kept"], 3)
        self.assertTrue((out / "dropped").is_dir())
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([f["index"] for f in manifest["frames"]], [1, 2, 3])
        self.assertEqual(sorted(f["timestamp_sec"] for f in manifest["frames"]),
                         [f["timestamp_sec"] for f in manifest["frames"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
