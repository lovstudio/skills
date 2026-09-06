"""Reference values and real FFmpeg color-range regressions; no private media."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from photographic_color import camera_color, decode_video, grade, resolve_mode, slog3_to_linear
from video_moments import source_info


class PhotographicColorTests(unittest.TestCase):
    def test_sony_published_gray_and_black_anchors(self):
        values = slog3_to_linear(np.array([95, 420, 598], dtype=float) / 1023)
        np.testing.assert_allclose(values[:2], [0, .18], atol=1e-12)
        self.assertAlmostEqual(values[2], .9, delta=.005)

    def test_log_gray_stays_neutral_in_srgb(self):
        params = dict(exposure=0, red=1, green=1, blue=1, saturation=1, contrast=1, brightness=0, gamma=1)
        im = grade(np.full((2, 2, 3), 420 / 1023), "slog3-sgamut3cine", params)
        np.testing.assert_allclose(np.array(im), 118, atol=1)

    def test_mode_requires_evidence_and_rejects_false_sdr_override(self):
        log = {"camera_color": {"CaptureGammaEquation": "s-log3-cine", "CaptureColorPrimaries": "s-gamut3-cine"}}
        self.assertEqual(resolve_mode(log, "auto"), "slog3-sgamut3cine")
        with self.assertRaisesRegex(ValueError, "conflicts"):
            resolve_mode(log, "srgb")
        with self.assertRaisesRegex(ValueError, "Unknown"):
            resolve_mode({}, "auto")
        with self.assertRaisesRegex(ValueError, "HDR"):
            resolve_mode({"color_transfer": "smpte2084"}, "srgb")
        log["camera_color"]["CaptureColorPrimaries"] = "s-gamut3"
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            resolve_mode(log, "auto")

    def test_sidecar_namespace_allowlist_and_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "clip.mp4"
            sidecar = Path(tmp) / "clipM01.XML"
            sidecar.write_text('<Meta xmlns="urn:sony"><Device serialNo="private"/><Item name="CaptureGammaEquation" value="s-log3-cine"/><Item name="CaptureColorPrimaries" value="s-gamut3-cine"/><Item name="CodingEquations" value="rec709"/></Meta>')
            (Path(tmp) / "._clipM01.XML").write_text("not XML")
            result = camera_color(video)
            self.assertEqual(result["CodingEquations"], "rec709")
            self.assertNotIn("private", json.dumps(result))
            self.assertEqual(result["sha256"], hashlib.sha256(sidecar.read_bytes()).hexdigest())
            (Path(tmp) / "clip.XML").write_text("<Meta/>")
            self.assertIn("Ambiguous", camera_color(video)["error"])

    def test_ffmpeg_full_and_video_range_are_not_interchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            for color_range, expected in [("pc", 940 / 1023), ("tv", 1.0)]:
                video = Path(tmp) / (color_range + ".mkv")
                subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                                "nullsrc=s=32x32:r=25,format=yuv444p10le,geq=lum=940:cb=512:cr=512",
                                "-vf", f"setparams=range={color_range}:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                                "-frames:v", "1", "-c:v", "ffv1", "-color_range", color_range,
                                "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709",
                                str(video)], check=True)
                source = source_info(video)
                rgb, record = decode_video(source, 0)
                self.assertAlmostEqual(float(rgb.mean()), expected, delta=.005)
                self.assertEqual(record["range"], color_range)
                with self.assertRaisesRegex(ValueError, "conflicts"):
                    decode_video(source, 0, "tv" if color_range == "pc" else "pc")

    def test_photographic_source_binding_and_export(self):
        cli = Path(__file__).resolve().parents[1] / "scripts/video_moments.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);video = root / "source.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=1",
                            "-vf", "setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                            "-c:v", "libx264", "-color_range", "tv", "-colorspace", "bt709", "-color_trc", "bt709",
                            "-color_primaries", "bt709", str(video)], check=True)
            def call(*args):
                return subprocess.run([sys.executable, str(cli), *map(str, args)], capture_output=True, text=True)
            self.assertEqual(call("extract", video, "--at", ".4", "--output", root / "raw").returncode, 0)
            manifest = root / "raw/frames.json"
            result = call("photographic", manifest, "--output", root / "graded")
            self.assertEqual(result.returncode, 0, result.stderr)
            edits = json.loads((root / "graded/edits.json").read_text())
            self.assertEqual(edits["color_mode"], "bt709")
            self.assertEqual(edits["status"], "needs-visual-review")
            row = edits["images"][0]
            with Image.open(root / "graded" / row["file"]) as im:
                self.assertEqual(im.size, (320, 180));self.assertEqual(im.mode, "RGB")
                self.assertTrue(im.info.get("icc_profile"));self.assertFalse(im.getexif())
                self.assertEqual(hashlib.sha256(im.tobytes()).hexdigest(), row["pixel_sha256"])
            moved = root / "moved.mp4";video.rename(moved)
            result = call("photographic", manifest, "--source-video", moved, "--output", root / "relocated")
            self.assertEqual(result.returncode, 0, result.stderr)
            with moved.open("ab") as stream:stream.write(b"changed")
            result = call("photographic", manifest, "--source-video", moved, "--output", root / "wrong")
            self.assertNotEqual(result.returncode, 0);self.assertIn("differs", result.stderr)


if __name__ == "__main__":
    unittest.main()
