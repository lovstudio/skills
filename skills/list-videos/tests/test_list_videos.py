#!/usr/bin/env python3
"""Regression tests for scripts/list_videos.py (no ffmpeg required)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "list_videos.py"


def touch(path: Path, size: int = 8) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


class ListVideosTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve() / "fixture"
        self.cache = Path(self.tmp.name).resolve() / "cache.json"
        touch(self.root / "a" / "clip1.mp4", 100)
        touch(self.root / "a" / "b" / "clip2.MOV", 50)
        touch(self.root / "a" / "b" / "._clip2.MOV", 4)
        touch(self.root / "a" / "notes.txt")
        touch(self.root / "node_modules" / "x" / "ignored.mp4")
        touch(self.root / ".hidden" / "hidden.mp4")
        touch(self.root / "Some.app" / "Contents" / "bundled.mp4")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> dict:
        env = {**os.environ, "LOV_LIST_VIDEOS_CACHE": str(self.cache)}
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root), "--format", "json", "-q", *args],
            capture_output=True, text=True, env=env, check=True,
        )
        return json.loads(proc.stdout)

    def paths(self, payload: dict) -> set[str]:
        return {os.path.relpath(v["path"], self.root) for v in payload["videos"]}

    def test_first_scan_applies_default_excludes(self) -> None:
        result = self.run_cli()
        self.assertEqual(self.paths(result), {"a/clip1.mp4", "a/b/clip2.MOV"})
        self.assertEqual(result["scan"]["dirs_scanned"], 3)
        self.assertEqual(result["matched"], 2)
        self.assertEqual(result["total_bytes"], 150)

    def test_second_scan_reuses_every_directory(self) -> None:
        self.run_cli()
        result = self.run_cli()
        self.assertEqual(result["scan"]["dirs_scanned"], 0)
        self.assertEqual(result["scan"]["dirs_reused"], 3)
        self.assertEqual(self.paths(result), {"a/clip1.mp4", "a/b/clip2.MOV"})

    def test_added_and_removed_directories_are_tracked(self) -> None:
        self.run_cli()
        touch(self.root / "gone" / "deep" / "tmp.mp4")
        self.assertIn("gone/deep/tmp.mp4", self.paths(self.run_cli()))
        import shutil
        shutil.rmtree(self.root / "gone")
        result = self.run_cli()
        self.assertNotIn("gone/deep/tmp.mp4", self.paths(result))
        self.assertEqual(result["scan"]["pruned"], 2)
        cache = json.loads(self.cache.read_text())
        self.assertFalse(any(k.endswith("/gone") or "/gone/" in k for k in cache["dirs"]))

    def test_in_place_growth_is_refreshed_without_dir_mtime_change(self) -> None:
        self.run_cli()
        target = self.root / "a" / "clip1.mp4"
        dir_mtime = os.stat(target.parent).st_mtime_ns
        time.sleep(0.01)
        with target.open("ab") as handle:
            handle.write(b"y" * 400)
        # Appending must not have touched the parent directory.
        self.assertEqual(os.stat(target.parent).st_mtime_ns, dir_mtime)
        result = self.run_cli()
        sizes = {os.path.relpath(v["path"], self.root): v["size"] for v in result["videos"]}
        self.assertEqual(sizes["a/clip1.mp4"], 500)
        self.assertEqual(result["scan"]["dirs_reused"], 3)

    def test_filters_and_limit_report_matched_versus_shown(self) -> None:
        result = self.run_cli("--min-size", "60", "--limit", "1")
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["shown"], 1)
        result = self.run_cli("--ext", "mov")
        self.assertEqual(self.paths(result), {"a/b/clip2.MOV"})
        result = self.run_cli("--limit", "1")
        self.assertEqual((result["matched"], result["shown"]), (2, 1))

    def test_hidden_and_no_default_excludes(self) -> None:
        self.assertIn(".hidden/hidden.mp4", self.paths(self.run_cli("--hidden")))
        result = self.run_cli("--no-default-excludes")
        self.assertIn("node_modules/x/ignored.mp4", self.paths(result))
        self.assertIn("Some.app/Contents/bundled.mp4", self.paths(result))
        self.assertNotIn("a/b/._clip2.MOV", self.paths(result))

    def test_no_cache_leaves_no_file(self) -> None:
        self.run_cli("--no-cache")
        self.assertFalse(self.cache.exists())


if __name__ == "__main__":
    unittest.main()
