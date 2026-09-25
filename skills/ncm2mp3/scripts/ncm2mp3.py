#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pycryptodome>=3.15", "mutagen>=1.45"]
# ///
"""Decrypt NetEase Cloud Music .ncm files into playable, tagged audio.

Segment layout, offset-addressed stream cipher and magic-byte sniffing follow
Johnserf-Seed/ncm2mp3. The cover frame follows taurusxin/ncmdump: newer files
reserve padding after the cover image, and parsers that read a bare image
length (ncmdump-py 1.1.6, ncm2mp3 0.3.1) misalign the audio and emit noise.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import traceback
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

try:
    import mutagen
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    from mutagen import flac, id3, mp3
except ImportError as missing:
    sys.exit(
        f"missing dependency: {missing.name}. Run with `uv run {Path(__file__).name}` "
        "or install them: python3 -m pip install pycryptodome mutagen"
    )


MAGIC = b"CTENFDAM"
CORE_KEY = b"hzHRAmso5kInbaxW"
META_KEY = b"#14ljk_!\\]&0U<'("
KEY_PREFIX = b"neteasecloudmusic"
META_PLAIN_PREFIX = b"163 key(Don't modify):"
MAX_SEGMENT_LEN = 64 * 1024 * 1024
# A multiple of 256 keeps every chunk aligned with the 256-byte keystream.
CHUNK_SIZE = 4 * 1024 * 1024
COVER_TIMEOUT_SECONDS = 8


class NcmError(Exception):
    pass


@dataclass
class NcmFile:
    path: Path
    meta: dict
    cover: bytes
    keystream: bytes
    audio_offset: int
    audio_format: str

    @property
    def duration(self) -> float:
        return (self.meta.get("duration") or 0) / 1000

    def write_audio(self, dest: Path) -> None:
        stream = self.keystream * (CHUNK_SIZE // 256)
        with self.path.open("rb") as source, dest.open("wb") as out:
            source.seek(self.audio_offset)
            while chunk := source.read(CHUNK_SIZE):
                out.write(xor(chunk, stream))


@dataclass
class Result:
    source: str
    status: str
    target: str = ""
    detail: dict = field(default_factory=dict)


def read_exact(handle, size: int, name: str) -> bytes:
    if size > MAX_SEGMENT_LEN:
        raise NcmError(f"{name} length {size} exceeds {MAX_SEGMENT_LEN}")
    data = handle.read(size)
    if len(data) != size:
        raise NcmError(f"unexpected EOF in {name}")
    return data


def read_u32(handle, name: str) -> int:
    return struct.unpack("<I", read_exact(handle, 4, name))[0]


def keystream_block(key: bytes) -> bytes:
    box = bytearray(range(256))
    j = 0
    for i in range(256):
        j = (j + box[i] + key[i % len(key)]) & 0xFF
        box[i], box[j] = box[j], box[i]

    block = bytearray(256)
    for offset in range(256):
        j = (offset + 1) & 0xFF
        a = box[j]
        block[offset] = box[(a + box[(a + j) & 0xFF]) & 0xFF]
    return bytes(block)


def xor(data: bytes, stream: bytes) -> bytes:
    size = len(data)
    # Whole-buffer big-int XOR is ~100x faster than a per-byte Python loop.
    return (int.from_bytes(data, "big") ^ int.from_bytes(stream[:size], "big")).to_bytes(size, "big")


def sniff_format(head: bytes) -> str | None:
    if head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
        return "mp3"
    if head[:4] == b"fLaC":
        return "flac"
    if head[4:8] == b"ftyp":
        return "m4a"
    if head[:4] == b"OggS":
        return "ogg"
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    return None


def parse_ncm(source: Path) -> NcmFile:
    with source.open("rb") as handle:
        if handle.read(len(MAGIC)) != MAGIC:
            raise NcmError("not an NCM file")
        read_exact(handle, 2, "post-magic gap")

        key_blob = bytes(b ^ 0x64 for b in read_exact(handle, read_u32(handle, "key length"), "key"))
        key = unpad(AES.new(CORE_KEY, AES.MODE_ECB).decrypt(key_blob), 16)
        if not key.startswith(KEY_PREFIX):
            raise NcmError("invalid RC4 key prefix")
        keystream = keystream_block(key[len(KEY_PREFIX):])

        meta: dict = {}
        meta_len = read_u32(handle, "metadata length")
        if meta_len:
            blob = bytes(b ^ 0x63 for b in read_exact(handle, meta_len, "metadata"))
            if not blob.startswith(META_PLAIN_PREFIX):
                raise NcmError("invalid metadata header")
            payload = base64.b64decode(blob[len(META_PLAIN_PREFIX):])
            plain = unpad(AES.new(META_KEY, AES.MODE_ECB).decrypt(payload), 16)
            kind, _, body = plain.partition(b":")
            meta = json.loads(body)
            if kind == b"dj":
                meta = meta.get("mainMusic") or {}

        read_exact(handle, 5, "crc32 and cover version")
        # The cover frame may reserve more space than the image it carries
        # (newer clients write image_len=0 inside a ~7.5 KB frame); audio
        # starts only after the whole frame.
        frame_len = read_u32(handle, "cover frame length")
        image_len = read_u32(handle, "cover length")
        if image_len > frame_len:
            raise NcmError(f"cover length {image_len} exceeds frame length {frame_len}")
        cover = read_exact(handle, image_len, "cover")
        read_exact(handle, frame_len - image_len, "cover frame padding")

        audio_offset = handle.tell()
        head = xor(handle.read(16), keystream)

    audio_format = sniff_format(head)
    if audio_format is None:
        raise NcmError(f"decrypted audio has unknown header {head.hex()}")
    return NcmFile(source, meta, cover, keystream, audio_offset, audio_format)


def image_mime(data: bytes) -> str | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return None


def fetch_cover(url: str) -> tuple[bytes, str]:
    try:
        with urllib.request.urlopen(url, timeout=COVER_TIMEOUT_SECONDS) as response:
            return response.read(), "downloaded"
    except Exception as error:
        return b"", f"download failed: {error}"


def resolve_cover(ncm: NcmFile, download: bool) -> tuple[bytes, str]:
    if ncm.cover:
        cover, source = ncm.cover, "embedded"
    elif download and ncm.meta.get("albumPic"):
        cover, source = fetch_cover(ncm.meta["albumPic"])
    else:
        return b"", "none"
    if cover and not image_mime(cover):
        return b"", f"ignored {source} data that is not JPEG or PNG"
    return cover, source


def artist_names(meta: dict) -> str:
    return "/".join(str(artist[0]) for artist in meta.get("artist") or [] if artist)


def tag_mp3(path: Path, ncm: NcmFile, download_cover: bool) -> str:
    audio = mp3.MP3(path)
    if audio.tags is None:
        audio.add_tags()
    tags = audio.tags

    artists = artist_names(ncm.meta)
    for frame, value in (
        (id3.TIT2, ncm.meta.get("musicName")),
        (id3.TPE1, artists),
        (id3.TPE2, artists),
        (id3.TALB, ncm.meta.get("album")),
    ):
        if value:
            tags.setall(frame.__name__, [frame(encoding=id3.Encoding.UTF16, text=value)])

    cover_source = "existing"
    if not tags.getall("APIC"):
        cover, cover_source = resolve_cover(ncm, download_cover)
        if cover:
            tags.add(id3.APIC(encoding=id3.Encoding.UTF16, mime=image_mime(cover), type=id3.PictureType.COVER_FRONT, desc="", data=cover))

    audio.save(v2_version=3)
    return cover_source


def tag_flac(path: Path, ncm: NcmFile, download_cover: bool) -> str:
    audio = flac.FLAC(path)
    artists = artist_names(ncm.meta)
    for key, value in (
        ("title", ncm.meta.get("musicName")),
        ("artist", artists),
        ("albumartist", artists),
        ("album", ncm.meta.get("album")),
    ):
        if value:
            audio[key] = value

    cover_source = "existing"
    if not audio.pictures:
        cover, cover_source = resolve_cover(ncm, download_cover)
        if cover:
            picture = flac.Picture()
            picture.type = id3.PictureType.COVER_FRONT
            picture.mime = image_mime(cover)
            picture.data = cover
            audio.add_picture(picture)

    audio.save()
    return cover_source


def demuxed_seconds(path: Path, ffmpeg: str) -> float:
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-nostats", "-i", str(path), "-map", "0:a:0", "-c", "copy", "-f", "null", "-", "-progress", "pipe:1"],
        capture_output=True,
        text=True,
    )
    times = [line.split("=", 1)[1] for line in result.stdout.splitlines() if line.startswith("out_time_us=")]
    return int(times[-1]) / 1_000_000 if times and times[-1].isdigit() else 0.0


def playable_seconds(path: Path, ffmpeg: str | None) -> tuple[float, bool]:
    """Duration backed by the audio actually on disk; 0 when unreadable.

    Containers state the full length up front (MP3 Xing/Info frame, FLAC
    STREAMINFO), so a truncated file still claims it. The bool says whether
    the length was bounded by what is really present.
    """
    try:
        with path.open("rb") as handle:
            if sniff_format(handle.read(16)) is None:
                return 0.0, True
        audio = mutagen.File(path)
    except Exception:
        return 0.0, True
    info = getattr(audio, "info", None)
    length = float(getattr(info, "length", 0) or 0)
    if length <= 0:
        return 0.0, True

    if isinstance(audio, mp3.MP3):
        size = path.stat().st_size
        audio_bytes = size - (audio.tags.size if audio.tags else 0)
        with path.open("rb") as handle:
            handle.seek(max(size - 128, 0))
            if handle.read(3) == b"TAG":
                audio_bytes -= 128
        if info.bitrate:
            length = min(length, audio_bytes * 8 / info.bitrate)
        return length, True
    if ffmpeg:
        return min(length, demuxed_seconds(path, ffmpeg)), True
    return length, False


def plausible(length: float, expected: float) -> bool:
    # A misaligned keystream can fake an MPEG sync word, so a positive length
    # is not enough; it must also match what NetEase recorded.
    tolerance = max(0.5, min(3.0, expected * 0.02))
    return length > 0 and (not expected or abs(length - expected) <= tolerance)


def transcode(ncm: NcmFile, ffmpeg: str, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="ncm2mp3-") as temp_dir:
        raw = Path(temp_dir) / f"audio.{ncm.audio_format}"
        ncm.write_audio(raw)
        result = subprocess.run(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(raw),
                "-map", "0:a", "-map_metadata", "0", "-id3v2_version", "3",
                "-codec:a", "libmp3lame", "-q:a", "2",
                str(output),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise NcmError(f"ffmpeg exited {result.returncode}: {result.stderr.strip()}")


def convert(source: Path, target_dir: Path, args: argparse.Namespace, claimed: set[str]) -> Result:
    ncm = parse_ncm(source)
    extension = "mp3" if args.format == "mp3" else ncm.audio_format
    target = target_dir / f"{source.stem}.{extension}"
    detail: dict = {"payload": ncm.audio_format, "output": extension}

    key = str(target.absolute()).casefold()
    if key in claimed:
        return Result(str(source), "conflict", str(target), {**detail, "reason": "another input in this run writes the same output"})
    claimed.add(key)

    if target.is_dir():
        raise NcmError(f"output path {target} is a folder")
    if target.exists() and not args.force:
        existing, _ = playable_seconds(target, args.ffmpeg)
        if plausible(existing, ncm.duration):
            return Result(str(source), "skipped", str(target), {**detail, "duration": round(existing, 1), "reason": "valid output already exists"})
        if existing > 0:
            return Result(str(source), "conflict", str(target), {
                **detail,
                "reason": f"a different or incomplete audio file ({existing:.1f}s, expected {ncm.duration:.1f}s) already uses this name; rerun with --force to replace it",
            })
        detail["replaces"] = "unplayable existing output"

    needs_transcode = extension != ncm.audio_format
    if needs_transcode and not args.ffmpeg:
        raise NcmError(f"{ncm.audio_format} payload needs ffmpeg to become mp3; install ffmpeg, pass --ffmpeg, or use --format original")

    if args.dry_run:
        detail["cover"] = "embedded" if ncm.cover else ("will download" if args.download_cover and ncm.meta.get("albumPic") else "none")
        if needs_transcode:
            detail["transcode"] = "libmp3lame -q:a 2"
        return Result(str(source), "planned", str(target), detail)

    created_dir = not target_dir.exists()
    target_dir.mkdir(parents=True, exist_ok=True)
    # Hidden sibling on the same volume so os.replace is atomic and a failed
    # run never publishes a half-written file; the short per-process name keeps
    # concurrent runs and near-limit filenames from colliding.
    partial = target_dir / f".ncm2mp3-{os.getpid()}.{extension}"
    published = False
    try:
        if needs_transcode:
            transcode(ncm, args.ffmpeg, partial)
        else:
            ncm.write_audio(partial)

        if extension == "mp3":
            detail["cover"] = tag_mp3(partial, ncm, args.download_cover)
        elif extension == "flac":
            detail["cover"] = tag_flac(partial, ncm, args.download_cover)
        else:
            detail["tags"] = "not written for this container"

        length, bounded = playable_seconds(partial, args.ffmpeg)
        if not plausible(length, ncm.duration):
            raise NcmError(f"output lasts {length:.1f}s, metadata says {ncm.duration:.1f}s; the file may be incomplete")
        detail["duration"] = round(length, 1)
        if not bounded:
            detail["completeness"] = "unchecked without ffmpeg"
        os.replace(partial, target)
        published = True
    finally:
        partial.unlink(missing_ok=True)
        if created_dir and not published:
            try:
                target_dir.rmdir()
            except OSError:
                pass

    return Result(str(source), "converted", str(target), detail)


def collect(inputs: list[str], recursive: bool, output_dir: Path | None) -> list:
    """Return, in input order, (source, target_dir) jobs and Results for inputs that cannot be read."""
    entries: list = []
    for raw in inputs:
        path = Path(raw).expanduser()
        if not path.exists():
            entries.append(Result(str(path), "failed", detail={"reason": "no such file or folder"}))
        elif not path.is_dir():
            entries.append((path, output_dir or path.parent))
        else:
            def unreadable(error: OSError) -> None:
                entries.append(Result(str(error.filename), "failed", detail={"reason": f"cannot read folder: {error.strerror}"}))

            for folder, subdirs, files in os.walk(path, onerror=unreadable):
                subdirs.sort()
                if not recursive:
                    subdirs.clear()
                for name in sorted(files):
                    # "._x.ncm" are AppleDouble sidecars macOS writes on exFAT/SMB.
                    if name.lower().endswith(".ncm") and not name.startswith("._"):
                        source = Path(folder) / name
                        relative = source.parent.relative_to(path)
                        entries.append((source, output_dir / relative if output_dir else source.parent))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description="Decrypt NetEase Cloud Music .ncm files into playable, tagged audio.")
    parser.add_argument("inputs", nargs="+", help=".ncm files or folders")
    parser.add_argument("-r", "--recursive", action="store_true", help="search folders recursively")
    parser.add_argument("-o", "--output-dir", help="write outputs here instead of next to each source")
    parser.add_argument("--format", choices=["mp3", "original"], default="mp3",
                        help="mp3 (default) transcodes non-mp3 payloads; original keeps FLAC and other payloads as-is")
    parser.add_argument("--force", action="store_true", help="overwrite any existing output with the same name")
    parser.add_argument("--no-cover-download", dest="download_cover", action="store_false",
                        help="never fetch the album cover URL from the NCM metadata")
    parser.add_argument("--ffmpeg", default=os.environ.get("FFMPEG") or "ffmpeg",
                        help="ffmpeg binary; needed to transcode non-mp3 payloads and to check non-mp3 outputs are complete")
    parser.add_argument("--dry-run", action="store_true", help="parse and report the plan without writing anything")
    parser.add_argument("--json", action="store_true", help="print one JSON document instead of text lines")
    parser.add_argument("--log", help="append per-file results (with tracebacks for failures) to this file")
    args = parser.parse_args()
    args.ffmpeg = shutil.which(args.ffmpeg) if args.ffmpeg else None
    # Stopping a Finder Quick Action sends SIGTERM; exit via SystemExit so
    # finally blocks remove temp files and subprocess.run kills ffmpeg.
    signal.signal(signal.SIGTERM, lambda signum, _frame: sys.exit(128 + signum))

    log = None
    if args.log and not args.dry_run:
        try:
            log_path = Path(args.log).expanduser()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log = log_path.open("a", encoding="utf-8")
        except OSError as error:
            parser.error(f"cannot open log file: {error}")

    output_dir = Path(args.output_dir).expanduser() if args.output_dir else None
    claimed: set[str] = set()
    results: list[Result] = []

    for entry in collect(args.inputs, args.recursive, output_dir):
        failure_trace = ""
        if isinstance(entry, Result):
            result = entry
        elif entry[0].suffix.lower() != ".ncm":
            result = Result(str(entry[0]), "ignored", detail={"reason": "not an .ncm file"})
        else:
            try:
                result = convert(entry[0], entry[1], args, claimed)
            except Exception as error:
                result = Result(str(entry[0]), "failed", detail={"reason": str(error)})
                failure_trace = traceback.format_exc().rstrip()
        results.append(result)

        line = f"{result.status}: {Path(result.source).name} -> {result.target or '-'} {json.dumps(result.detail, ensure_ascii=False)}"
        if log:
            log.write(f"{result.status.upper()}: {result.source} -> {result.target or '-'} {json.dumps(result.detail, ensure_ascii=False)}\n")
            if failure_trace:
                log.write(failure_trace + "\n")
            log.flush()
        if not args.json:
            print(line, file=sys.stderr if result.status in ("failed", "conflict") else sys.stdout, flush=True)

    statuses = ("converted", "planned", "skipped", "conflict", "ignored", "failed")
    counts = {status: sum(r.status == status for r in results) for status in statuses}
    if args.json:
        print(json.dumps({"summary": counts, "results": [r.__dict__ for r in results]}, ensure_ascii=False, indent=2))
    else:
        print(", ".join(f"{counts[s]} {s}" for s in statuses if counts[s] or s in ("converted", "failed")), flush=True)
    return 1 if counts["failed"] or counts["conflict"] else 0


if __name__ == "__main__":
    sys.exit(main())
