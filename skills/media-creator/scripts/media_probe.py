#!/usr/bin/env python3
"""Inspect a local media file with ffprobe and emit stable JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_ffprobe(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or "ffprobe returned a non-zero status"
        raise RuntimeError(message)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid JSON: {exc}") from exc


def number(value: Any) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_stream(stream: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "index",
        "codec_type",
        "codec_name",
        "codec_long_name",
        "width",
        "height",
        "pix_fmt",
        "r_frame_rate",
        "avg_frame_rate",
        "sample_rate",
        "channels",
        "channel_layout",
        "duration",
        "bit_rate",
        "disposition",
        "tags",
    )
    normalized: dict[str, Any] = {}
    for field in fields:
        if field in stream:
            normalized[field] = stream[field]
    for field in ("duration", "bit_rate", "sample_rate"):
        if field in normalized:
            parsed = number(normalized[field])
            if parsed is not None:
                normalized[field] = parsed
    return normalized


def build_report(path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    format_data = raw.get("format") or {}
    streams = [normalize_stream(item) for item in raw.get("streams", [])]
    video_streams = [item for item in streams if item.get("codec_type") == "video"]
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    subtitle_streams = [item for item in streams if item.get("codec_type") == "subtitle"]
    duration = number(format_data.get("duration"))
    return {
        "schema": "lovstudio/media-probe/v1",
        "input": {
            "name": path.name,
            "path": str(path),
            "size_bytes": path.stat().st_size,
        },
        "format": {
            "name": format_data.get("format_name"),
            "long_name": format_data.get("format_long_name"),
            "duration_seconds": duration,
            "bit_rate": number(format_data.get("bit_rate")),
            "tags": format_data.get("tags", {}),
        },
        "duration_seconds": duration,
        "streams": streams,
        "stream_counts": {
            "video": len(video_streams),
            "audio": len(audio_streams),
            "subtitle": len(subtitle_streams),
        },
        "video": video_streams,
        "audio": audio_streams,
        "subtitles": subtitle_streams,
    }


def write_json(data: dict[str, Any], output: str | None, pretty: bool) -> None:
    rendered = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)
    if output:
        target = Path(output).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input media file")
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()

    path = Path(args.input).expanduser()
    if not path.is_file():
        print(f"ERROR [media-probe] input file does not exist: {path}", file=sys.stderr)
        return 1
    try:
        report = build_report(path, run_ffprobe(path))
        write_json(report, args.output, args.pretty)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR [media-probe] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
