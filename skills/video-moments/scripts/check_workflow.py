#!/usr/bin/env python3
"""Focused integration checks with synthetic video, never a real-user case."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


CLI = Path(__file__).with_name("video_moments.py")


def call(*args, success=True):
    p = subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)
    if (p.returncode == 0) != success:
        raise AssertionError(p.stdout + p.stderr)
    return p


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    with tempfile.TemporaryDirectory(prefix="moments-check-") as tmp:
        root = Path(tmp)
        video = root / "课程 测试.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc2=size=320x180:rate=25:duration=3", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", str(video)], check=True)
        call("index", video, "--every", "1", "--output", root / "index")
        original_stats = {p.name: p.stat().st_mtime_ns for p in (root / "index/frames").iterdir()}
        call("index", video, "--every", "1", "--output", root / "index", "--resume")
        assert original_stats == {p.name: p.stat().st_mtime_ns for p in (root / "index/frames").iterdir()}
        call("index", video, "--every", "0.5", "--output", root / "index", "--resume", success=False)
        call("index", video, "--every", "nan", "--output", root / "bad", success=False)
        call("extract", video, "--at", "3", "--output", root / "outside", success=False)
        call("extract", video, "--at", "1", "2", "--output", root / "originals")
        frames = json.loads((root / "originals/frames.json").read_text())
        call("photographic", root / "originals/frames.json", "--output", root / "unknown-color", success=False)
        call("photographic", root / "originals/frames.json", "--long-edge", "320",
             "--color-mode", "srgb", "--gamma", "1.15", "--output", root / "edits")
        edits = json.loads((root / "edits/edits.json").read_text())
        assert all(row["size"] == [320, 180] for row in edits["images"])
        call("photographic", root / "originals/frames.json", "--color-mode", "srgb", "--gamma", "nan",
             "--output", root / "invalid-edits", success=False)
        selection = {"schema": "video-moments-selection/v1", "frames_manifest": "originals/frames.json",
                     "source": frames["source"], "selection_basis": "visual", "moments": []}
        for frame in frames["frames"]:
            selection["moments"].append({"id": frame["id"], "time": frame["time"],
                "category": "synthetic-check", "reason": "工程测试 <script>alert(1)</script>",
                "evidence": "Synthetic fixture, no claim of semantic review", "edit_method": "original",
                "original": "originals/" + frame["file"], "final": "originals/" + frame["file"],
                "original_sha256": frame["sha256"], "final_sha256": frame["sha256"],
                "review": dict.fromkeys(["source_match", "identity", "screen_text", "composition", "privacy"], True)})
        selection_path = root / "selection.json"
        def save(value):
            selection_path.write_text(json.dumps(value), encoding="utf-8")
        save(selection)
        call("package", selection_path, "--output", root / "package")
        call("verify", root / "package")
        assert "<script>alert" not in (root / "package/gallery.html").read_text()
        call("package", selection_path, "--output", root / "package", success=False)
        for field, value in [("time", 0.5), ("final_sha256", "wrong"), ("quote", "unverified quote")]:
            bad = copy.deepcopy(selection)
            bad["moments"][0][field] = value
            save(bad)
            call("package", selection_path, "--output", root / "rejected", success=False)
        bad = copy.deepcopy(selection)
        bad["moments"][0]["review"]["identity"] = False
        save(bad)
        call("package", selection_path, "--output", root / "rejected", success=False)
        bad = copy.deepcopy(selection)
        bad["moments"][1]["id"] = bad["moments"][0]["id"]
        save(bad)
        call("package", selection_path, "--output", root / "rejected", success=False)
        first = next((root / "package/images").iterdir())
        first.write_bytes(b"corrupt")
        call("verify", root / "package", success=False)
    print("PASSED: synthetic CLI integration, resume, Chinese paths, source binding, visual gate, quote gate, escaping, overwrite refusal and corruption detection")


if __name__ == "__main__":
    main()
