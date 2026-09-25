#!/usr/bin/env python3
"""Regression tests for scripts/ncm2mp3.py.

Run: uv run --with pycryptodome --with mutagen python3 tests/test_ncm2mp3.py
Requires ffmpeg to synthesize payloads and to exercise transcoding.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from mutagen import flac, id3, mp3

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ncm2mp3.py"
spec = importlib.util.spec_from_file_location("ncm2mp3", SCRIPT)
ncm2mp3 = importlib.util.module_from_spec(spec)
sys.modules["ncm2mp3"] = ncm2mp3
spec.loader.exec_module(ncm2mp3)

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)
RC4_KEY = b"1234567890123456789012345678901234567890"


def make_payload(path: Path, codec: str, seconds: int = 5) -> bytes:
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
         "-c:a", codec, str(path)],
        check=True,
    )
    return path.read_bytes()


def make_ncm(path: Path, audio: bytes, meta: dict | None, kind: bytes = b"music",
             cover: bytes = b"", padding: int = 0, frame_len: int | None = None) -> None:
    key_blob = bytes(b ^ 0x64 for b in AES.new(ncm2mp3.CORE_KEY, AES.MODE_ECB).encrypt(pad(ncm2mp3.KEY_PREFIX + RC4_KEY, 16)))
    meta_blob = b""
    if meta is not None:
        encrypted = AES.new(ncm2mp3.META_KEY, AES.MODE_ECB).encrypt(pad(kind + b":" + json.dumps(meta).encode(), 16))
        meta_blob = bytes(b ^ 0x63 for b in ncm2mp3.META_PLAIN_PREFIX + base64.b64encode(encrypted))
    frame = len(cover) + padding if frame_len is None else frame_len
    header = (
        ncm2mp3.MAGIC + b"\x01\x6d"
        + struct.pack("<I", len(key_blob)) + key_blob
        + struct.pack("<I", len(meta_blob)) + meta_blob
        + b"\x00\x00\x00\x00\x01"
        + struct.pack("<II", frame, len(cover)) + cover + bytes(range(256)) * (padding // 256) + b"\x7f" * (padding % 256)
    )
    stream = (ncm2mp3.keystream_block(RC4_KEY) * (len(audio) // 256 + 1))[: len(audio)]
    path.write_bytes(header + bytes(a ^ b for a, b in zip(audio, stream)))


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def meta_for(title: str, seconds: int = 5, album_pic: str = "") -> dict:
    return {"musicName": title, "artist": [["歌手A", 1], ["Singer B", 2]], "album": "专辑", "format": "mp3",
            "duration": seconds * 1000, "albumPic": album_pic}


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is required")
class Ncm2Mp3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name).resolve()
        cls.mp3 = make_payload(cls.root / "payload.mp3", "libmp3lame")
        cls.flac = make_payload(cls.root / "payload.flac", "flac")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def workdir(self, name: str) -> Path:
        path = self.root / name
        path.mkdir()
        return path

    def test_padded_cover_frame_decodes_payload_exactly(self) -> None:
        work = self.workdir("padded")
        make_ncm(work / "新.ncm", self.mp3, meta_for("新版布局"), padding=7570)
        result = run(str(work / "新.ncm"), "--no-cover-download")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = work / "新.mp3"
        tags = mp3.MP3(out).tags
        self.assertEqual(str(tags["TIT2"]), "新版布局")
        self.assertEqual(str(tags["TPE1"]), "歌手A/Singer B")
        self.assertEqual(tags.getall("APIC"), [])
        payload_start = self.mp3.index(b"\xff", 10)
        self.assertTrue(out.read_bytes().endswith(self.mp3[payload_start:]))

    def test_legacy_layout_with_embedded_png_cover(self) -> None:
        work = self.workdir("legacy")
        make_ncm(work / "old.ncm", self.mp3, meta_for("旧版布局"), cover=PNG)
        self.assertEqual(run(str(work / "old.ncm")).returncode, 0)
        apic = mp3.MP3(work / "old.mp3").tags.getall("APIC")
        self.assertEqual([(p.mime, p.type, p.data) for p in apic], [("image/png", id3.PictureType.COVER_FRONT, PNG)])

    def test_misaligned_audio_is_rejected_without_output(self) -> None:
        work = self.workdir("misaligned")
        make_ncm(work / "bad.ncm", self.mp3, meta_for("错位"), padding=7570, frame_len=0)
        result = run(str(work / "bad.ncm"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown header", result.stderr)
        self.assertEqual(sorted(p.name for p in work.iterdir()), ["bad.ncm"])

    def test_truncated_file_fails_cleanly(self) -> None:
        work = self.workdir("truncated")
        make_ncm(work / "full.ncm", self.mp3, meta_for("截断"), padding=7570)
        (work / "cut.ncm").write_bytes((work / "full.ncm").read_bytes()[:2000])
        result = run(str(work / "cut.ncm"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("unexpected EOF", result.stderr)
        self.assertFalse((work / "cut.mp3").exists())

    def test_flac_payload_transcodes_or_stays_lossless(self) -> None:
        work = self.workdir("flac")
        make_ncm(work / "hq.ncm", self.flac, meta_for("无损"), cover=PNG)
        self.assertEqual(run(str(work / "hq.ncm")).returncode, 0)
        self.assertAlmostEqual(mp3.MP3(work / "hq.mp3").info.length, 5, delta=0.2)

        self.assertEqual(run(str(work / "hq.ncm"), "--format", "original").returncode, 0)
        audio = flac.FLAC(work / "hq.flac")
        self.assertEqual(audio["title"], ["无损"])
        self.assertEqual([p.data for p in audio.pictures], [PNG])

    def test_dj_metadata_uses_main_music(self) -> None:
        work = self.workdir("dj")
        make_ncm(work / "dj.ncm", self.mp3, {"programName": "节目", "mainMusic": meta_for("电台单曲")}, kind=b"dj")
        self.assertEqual(run(str(work / "dj.ncm")).returncode, 0)
        self.assertEqual(str(mp3.MP3(work / "dj.mp3").tags["TIT2"]), "电台单曲")

    def test_existing_outputs_skip_valid_replace_unplayable_and_force(self) -> None:
        work = self.workdir("existing")
        make_ncm(work / "a.ncm", self.mp3, meta_for("已有"), padding=100)
        self.assertEqual(run(str(work / "a.ncm")).returncode, 0)
        before = (work / "a.mp3").stat().st_mtime_ns

        skipped = json.loads(run(str(work / "a.ncm"), "--json").stdout)
        self.assertEqual(skipped["summary"]["skipped"], 1)
        self.assertEqual((work / "a.mp3").stat().st_mtime_ns, before)

        (work / "a.mp3").write_bytes(bytes(range(256)) * 800)
        replaced = json.loads(run(str(work / "a.ncm"), "--json").stdout)["results"][0]
        self.assertEqual((replaced["status"], replaced["detail"]["replaces"]), ("converted", "unplayable existing output"))

        forced = json.loads(run(str(work / "a.ncm"), "--json", "--force").stdout)
        self.assertEqual(forced["summary"]["converted"], 1)

    def test_playable_or_truncated_same_name_file_is_a_conflict(self) -> None:
        work = self.workdir("conflict")
        make_ncm(work / "song.ncm", self.mp3, meta_for("冲突"))
        other = make_payload(work / "song.mp3", "libmp3lame", seconds=12)
        result = run(str(work / "song.ncm"), "--json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["results"][0]["status"], "conflict")
        self.assertEqual((work / "song.mp3").read_bytes(), other)

        self.assertEqual(run(str(work / "song.ncm"), "--force").returncode, 0)
        full = (work / "song.mp3").read_bytes()
        (work / "song.mp3").write_bytes(full[: len(full) // 3])
        again = json.loads(run(str(work / "song.ncm"), "--json").stdout)["results"][0]
        self.assertEqual(again["status"], "conflict")

    def test_truncated_audio_payload_fails_instead_of_reporting_full_length(self) -> None:
        work = self.workdir("cut-audio")
        make_ncm(work / "full.ncm", self.mp3, meta_for("半截"), padding=7570)
        data = (work / "full.ncm").read_bytes()
        (work / "cut.ncm").write_bytes(data[: len(data) - len(self.mp3) // 2])
        result = run(str(work / "cut.ncm"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("may be incomplete", result.stderr)
        self.assertFalse((work / "cut.mp3").exists())

        make_ncm(work / "hq.ncm", self.flac, meta_for("半截无损"))
        data = (work / "hq.ncm").read_bytes()
        (work / "hqcut.ncm").write_bytes(data[: len(data) - len(self.flac) // 2])
        result = run(str(work / "hqcut.ncm"), "--format", "original")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((work / "hqcut.flac").exists())

    def test_two_inputs_mapping_to_one_output_do_not_clobber(self) -> None:
        work = self.workdir("clash")
        for folder, title in (("A", "甲"), ("B", "乙")):
            (work / folder).mkdir()
            make_ncm(work / folder / "same.ncm", self.mp3, meta_for(title))
        result = json.loads(run(str(work / "A"), str(work / "B"), "-o", str(work / "out"), "--json").stdout)
        self.assertEqual([r["status"] for r in result["results"]], ["converted", "conflict"])
        self.assertEqual(str(mp3.MP3(work / "out" / "same.mp3").tags["TIT2"]), "甲")

    def test_bad_inputs_are_reported_not_ignored(self) -> None:
        work = self.workdir("inputs")
        make_ncm(work / "ok.ncm", self.mp3, meta_for("正常"))
        (work / "._ok.ncm").write_bytes(b"\x00\x05\x16\x07" + bytes(60))
        result = json.loads(run(str(work), str(work / "missing-folder"), "--dry-run", "--json").stdout)
        statuses = [(Path(r["source"]).name, r["status"]) for r in result["results"]]
        self.assertEqual(statuses, [("ok.ncm", "planned"), ("missing-folder", "failed")])

        (work / "logdir").mkdir()
        refused = run(str(work / "ok.ncm"), "--log", str(work / "logdir"))
        self.assertEqual(refused.returncode, 2)
        self.assertFalse((work / "ok.mp3").exists())

    def test_dry_run_writes_nothing_and_reports_missing_ffmpeg(self) -> None:
        work = self.workdir("dry")
        make_ncm(work / "d.ncm", self.flac, meta_for("预演"))
        plan = json.loads(run(str(work / "d.ncm"), "--dry-run", "--json").stdout)["results"][0]
        self.assertEqual((plan["status"], plan["detail"]["transcode"]), ("planned", "libmp3lame -q:a 2"))

        missing = run(str(work / "d.ncm"), "--dry-run", "--json", "--ffmpeg", str(work / "no-ffmpeg"), "-o", str(work / "out"))
        self.assertEqual(json.loads(missing.stdout)["results"][0]["status"], "failed")
        self.assertEqual(sorted(p.name for p in work.iterdir()), ["d.ncm"])

    def test_recursive_folder_mirrors_into_output_dir(self) -> None:
        work = self.workdir("tree")
        (work / "in" / "专辑").mkdir(parents=True)
        make_ncm(work / "in" / "top.ncm", self.mp3, meta_for("顶层"))
        make_ncm(work / "in" / "专辑" / "deep.ncm", self.mp3, meta_for("子目录"))
        (work / "in" / "note.txt").write_text("not audio")
        result = run(str(work / "in"), "-r", "-o", str(work / "out"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((work / "out" / "top.mp3").is_file())
        self.assertTrue((work / "out" / "专辑" / "deep.mp3").is_file())
        self.assertFalse(any(p.name.startswith(".ncm2mp3-") for p in (work / "out").rglob("*")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
