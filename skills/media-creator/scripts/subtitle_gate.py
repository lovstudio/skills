#!/usr/bin/env python3
"""Build and verify subtitle-review MKV files, then seal approved subtitles.

The review file deliberately keeps narration subtitles as a soft SubRip track.
Non-subtitle graphics may already be present in the supplied video master. The
approved command replaces the review subtitle track without re-encoding video
or audio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple


TIME_RE = re.compile(
    r"^(?P<sh>\d{1,3}):(?P<sm>\d{2}):(?P<ss>\d{2})[,.](?P<sms>\d{3})"
    r"\s*-->\s*"
    r"(?P<eh>\d{1,3}):(?P<em>\d{2}):(?P<es>\d{2})[,.](?P<ems>\d{3})"
    r"(?:\s+.*)?$"
)


class GateError(RuntimeError):
    """A user-actionable subtitle gate failure."""


def run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise GateError(
            "command failed ({code}): {cmd}\n{detail}".format(
                code=result.returncode,
                cmd=" ".join(command),
                detail=detail[-4000:],
            )
        )
    return result


def require_program(name: str) -> None:
    result = subprocess.run(
        [name, "-version"], capture_output=True, text=True
    )
    if result.returncode:
        raise GateError("required program is unavailable: {0}".format(name))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def milliseconds(match: re.Match[str], prefix: str) -> int:
    return (
        int(match.group(prefix + "h")) * 3_600_000
        + int(match.group(prefix + "m")) * 60_000
        + int(match.group(prefix + "s")) * 1000
        + int(match.group(prefix + "ms"))
    )


def parse_srt(path: Path, duration_ms: Optional[int] = None) -> List[Dict[str, Any]]:
    if not path.is_file():
        raise GateError("subtitle file not found: {0}".format(path))
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise GateError("subtitle must be UTF-8: {0}: {1}".format(path, exc))
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        raise GateError("subtitle file is empty: {0}".format(path))

    cues: List[Dict[str, Any]] = []
    previous_end = 0
    for block_index, block in enumerate(re.split(r"\n{2,}", raw), 1):
        lines = [line.rstrip() for line in block.split("\n")]
        timing_index = next(
            (index for index, line in enumerate(lines[:2]) if "-->" in line),
            None,
        )
        if timing_index is None:
            raise GateError(
                "cue {0} has no SRT timing line: {1}".format(block_index, lines[0])
            )
        match = TIME_RE.match(lines[timing_index].strip())
        if not match:
            raise GateError(
                "cue {0} has an invalid timing line: {1}".format(
                    block_index, lines[timing_index]
                )
            )
        start_ms = milliseconds(match, "s")
        end_ms = milliseconds(match, "e")
        text = "\n".join(lines[timing_index + 1 :]).strip()
        if not text:
            raise GateError("cue {0} has no subtitle text".format(block_index))
        if end_ms <= start_ms:
            raise GateError(
                "cue {0} has non-positive duration: {1}".format(
                    block_index, lines[timing_index]
                )
            )
        if cues and start_ms < previous_end:
            raise GateError(
                "cue {0} overlaps the preceding cue ({1}ms < {2}ms)".format(
                    block_index, start_ms, previous_end
                )
            )
        if duration_ms is not None and end_ms > duration_ms + 250:
            raise GateError(
                "cue {0} ends after the video ({1}ms > {2}ms)".format(
                    block_index, end_ms, duration_ms
                )
            )
        cues.append({"start_ms": start_ms, "end_ms": end_ms, "text": text})
        previous_end = end_ms
    return cues


def probe(path: Path, ffprobe: str) -> Dict[str, Any]:
    result = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GateError("ffprobe returned invalid JSON: {0}".format(exc))


def duration_ms(info: Dict[str, Any]) -> int:
    try:
        return round(float(info["format"]["duration"]) * 1000)
    except (KeyError, TypeError, ValueError) as exc:
        raise GateError("could not read media duration: {0}".format(exc))


def validate_streams(info: Dict[str, Any]) -> Dict[str, Any]:
    streams = info.get("streams", [])
    video = [item for item in streams if item.get("codec_type") == "video"]
    audio = [item for item in streams if item.get("codec_type") == "audio"]
    subtitle = [item for item in streams if item.get("codec_type") == "subtitle"]
    if len(video) != 1 or len(audio) != 1 or len(subtitle) != 1:
        raise GateError(
            "expected one video, one audio and one subtitle stream; got {0}/{1}/{2}".format(
                len(video), len(audio), len(subtitle)
            )
        )
    if subtitle[0].get("codec_name") not in {"subrip", "srt"}:
        raise GateError(
            "embedded subtitle is not SubRip: {0}".format(
                subtitle[0].get("codec_name")
            )
        )
    return {"video": video[0], "audio": audio[0], "subtitle": subtitle[0]}


def comparable(cues: Sequence[Dict[str, Any]]) -> List[Tuple[int, int, str]]:
    return [
        (int(item["start_ms"]), int(item["end_ms"]), str(item["text"]))
        for item in cues
    ]


def extract_embedded_srt(
    media: Path,
    ffmpeg: str,
) -> Tuple[List[Dict[str, Any]], str]:
    """Extract the author-review baseline for approval comparisons."""
    with tempfile.TemporaryDirectory(prefix="lov-subtitle-gate-") as tmpdir:
        extracted = Path(tmpdir) / "embedded.srt"
        run(
            [
                ffmpeg,
                "-y",
                "-v",
                "error",
                "-i",
                str(media),
                "-map",
                "0:s:0",
                "-c:s",
                "srt",
                str(extracted),
            ]
        )
        return parse_srt(extracted), sha256(extracted)


def verify_embedded_srt(
    media: Path,
    expected: Sequence[Dict[str, Any]],
    ffmpeg: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="lov-subtitle-gate-") as tmpdir:
        extracted = Path(tmpdir) / "embedded.srt"
        run(
            [
                ffmpeg,
                "-y",
                "-v",
                "error",
                "-i",
                str(media),
                "-map",
                "0:s:0",
                "-c:s",
                "srt",
                str(extracted),
            ]
        )
        actual = parse_srt(extracted)
    if comparable(actual) != comparable(expected):
        raise GateError("embedded subtitle does not round-trip to the supplied SRT")


def atomic_output_path(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    return output.with_name(".{0}.partial{1}".format(output.stem, output.suffix))


def write_report(path: Optional[Path], report: Dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".{0}.partial".format(path.name))
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(str(temporary), str(path))


def build_review(args: argparse.Namespace) -> Dict[str, Any]:
    video = Path(args.video).resolve()
    audio = Path(args.audio).resolve() if args.audio else None
    srt = Path(args.srt).resolve()
    output = Path(args.output).resolve()
    if output.suffix.lower() != ".mkv":
        raise GateError("review output must use the .mkv extension")
    if output.exists():
        raise GateError(
            "review output already exists and is author-owned: {0}; "
            "use a new review version instead of overwriting it".format(output)
        )
    if not video.is_file():
        raise GateError("video master not found: {0}".format(video))
    if audio is not None and not audio.is_file():
        raise GateError("audio master not found: {0}".format(audio))

    video_info = probe(video, args.ffprobe)
    cues = parse_srt(srt, duration_ms(video_info))
    temporary = atomic_output_path(output)
    temporary.unlink(missing_ok=True)
    command = [args.ffmpeg, "-y", "-hide_banner", "-v", "error", "-i", str(video)]
    if audio is not None:
        command.extend(["-i", str(audio), "-i", str(srt)])
        maps = ["-map", "0:v:0", "-map", "1:a:0", "-map", "2:0"]
        codecs = [
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            args.audio_bitrate,
            "-ar",
            "48000",
            "-ac",
            "2",
        ]
    else:
        command.extend(["-i", str(srt)])
        maps = ["-map", "0:v:0", "-map", "0:a:0", "-map", "1:0"]
        codecs = ["-c:v", "copy", "-c:a", "copy"]
    command.extend(
        maps
        + codecs
        + [
            "-c:s",
            "srt",
            "-metadata:s:s:0",
            "language={0}".format(args.language),
            "-metadata:s:s:0",
            "title={0}".format(args.subtitle_title),
            "-disposition:s:0",
            "default",
            str(temporary),
        ]
    )
    try:
        run(command)
        info = probe(temporary, args.ffprobe)
        selected = validate_streams(info)
        verify_embedded_srt(temporary, cues, args.ffmpeg)
        os.replace(str(temporary), str(output))
    finally:
        temporary.unlink(missing_ok=True)

    report = {
        "schema": "lovstudio/subtitle-gate/v1",
        "mode": "review",
        "render_status": "review-ready",
        "subtitle_status": "awaiting-review",
        "review_mkv": str(output),
        "external_srt": str(srt),
        "cue_count": len(cues),
        "duration_seconds": round(duration_ms(info) / 1000.0, 3),
        "streams": selected,
        "sha256": {"review_mkv": sha256(output), "external_srt": sha256(srt)},
    }
    write_report(Path(args.report).resolve() if args.report else None, report)
    return report


def approve(args: argparse.Namespace) -> Dict[str, Any]:
    review = Path(args.review).resolve()
    srt = Path(args.srt).resolve()
    output = Path(args.output).resolve()
    if output.suffix.lower() != ".mkv":
        raise GateError("approved master output must use the .mkv extension")
    if not review.is_file():
        raise GateError("review MKV not found: {0}".format(review))
    review_info = probe(review, args.ffprobe)
    review_streams = validate_streams(review_info)
    review_cues, review_subtitle_sha256 = extract_embedded_srt(review, args.ffmpeg)
    cues = parse_srt(srt, duration_ms(review_info))
    changed_from_review = comparable(review_cues) != comparable(cues)
    if args.expect_edits and not changed_from_review:
        raise GateError(
            "approval was declared as author-edited, but the approved SRT is "
            "identical to the subtitle embedded in the review MKV; stop and "
            "recover the author's actual Subtitle Edit file before rendering"
        )
    temporary = atomic_output_path(output)
    temporary.unlink(missing_ok=True)
    command = [
        args.ffmpeg,
        "-y",
        "-hide_banner",
        "-v",
        "error",
        "-i",
        str(review),
        "-i",
        str(srt),
        "-map",
        "0:v:0",
        "-map",
        "0:a:0",
        "-map",
        "1:0",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-c:s",
        "srt",
        "-metadata:s:s:0",
        "language={0}".format(args.language),
        "-metadata:s:s:0",
        "title={0}".format(args.subtitle_title),
        "-disposition:s:0",
        "default",
        str(temporary),
    ]
    try:
        run(command)
        info = probe(temporary, args.ffprobe)
        selected = validate_streams(info)
        verify_embedded_srt(temporary, cues, args.ffmpeg)
        os.replace(str(temporary), str(output))
    finally:
        temporary.unlink(missing_ok=True)

    report = {
        "schema": "lovstudio/subtitle-gate/v1",
        "mode": "approved-master",
        "render_status": "passed",
        "subtitle_status": "approved",
        "source_review_mkv": str(review),
        "approved_srt": str(srt),
        "approved_master_mkv": str(output),
        "source_review_mkv_mtime_ns": review.stat().st_mtime_ns,
        "approved_srt_mtime_ns": srt.stat().st_mtime_ns,
        "cue_count": len(cues),
        "review_cue_count": len(review_cues),
        "changed_from_review": changed_from_review,
        "expect_edits": bool(args.expect_edits),
        "duration_seconds": round(duration_ms(info) / 1000.0, 3),
        "streams": selected,
        "source_streams": review_streams,
        "sha256": {
            "approved_master_mkv": sha256(output),
            "approved_srt": sha256(srt),
            "review_embedded_srt": review_subtitle_sha256,
        },
    }
    write_report(Path(args.report).resolve() if args.report else None, report)
    return report


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--srt", required=True, help="UTF-8 SubRip subtitle file")
    parser.add_argument("--output", required=True, help="output MKV path")
    parser.add_argument("--report", help="optional JSON gate report")
    parser.add_argument("--language", default="zho", help="Matroska language tag")
    parser.add_argument(
        "--subtitle-title", default="Chinese", help="embedded subtitle track title"
    )
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a soft-subtitle review MKV and seal an approved SRT"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser(
        "review", help="package a subtitle-free video master and editable SRT"
    )
    review.add_argument("--video", required=True, help="subtitle-free video master")
    review.add_argument("--audio", help="separate audio master; encoded to AAC when set")
    review.add_argument("--audio-bitrate", default="192k")
    add_common(review)
    review.set_defaults(handler=build_review)

    approved = subparsers.add_parser(
        "approve", help="replace the review track with the user-approved SRT"
    )
    approved.add_argument("--review", required=True, help="review MKV with video/audio")
    approved.add_argument(
        "--expect-edits",
        action="store_true",
        help=(
            "fail if the approved SRT is identical to the review subtitle; "
            "required when the author says they edited subtitles"
        ),
    )
    add_common(approved)
    approved.set_defaults(handler=approve)

    args = parser.parse_args()
    require_program(args.ffmpeg)
    require_program(args.ffprobe)
    report = args.handler(args)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GateError, OSError) as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        raise SystemExit(2)
