#!/usr/bin/env python3
"""Inspect completed media with ffprobe and emit a structured verification report."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VIDEO_SUFFIXES = {".mkv", ".mp4", ".m4v", ".mov", ".ts", ".m2ts", ".webm", ".avi"}
PARTIAL_SUFFIXES = {".part", ".partial", ".crdownload", ".tmp", ".!qB".lower()}


def media_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in VIDEO_SUFFIXES else []
    return sorted(
        (item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in VIDEO_SUFFIXES),
        key=lambda item: item.stat().st_size,
        reverse=True,
    )


def partial_files(path: Path) -> list[str]:
    root = path if path.is_dir() else path.parent
    return [
        str(item)
        for item in root.rglob("*")
        if item.is_file() and item.suffix.lower() in PARTIAL_SUFFIXES
    ]


def ffprobe(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {completed.stderr.strip()[:500]}")
    return json.loads(completed.stdout)


def language(stream: dict[str, Any]) -> str:
    tags = stream.get("tags") if isinstance(stream.get("tags"), dict) else {}
    return str(tags.get("language") or "und")


def inspect(path: Path) -> dict[str, Any]:
    probe = ffprobe(path)
    streams = probe.get("streams") if isinstance(probe.get("streams"), list) else []
    videos = [item for item in streams if item.get("codec_type") == "video"]
    audios = [item for item in streams if item.get("codec_type") == "audio"]
    subtitles = [item for item in streams if item.get("codec_type") == "subtitle"]
    format_data = probe.get("format") if isinstance(probe.get("format"), dict) else {}
    duration = float(format_data.get("duration") or 0)
    primary = videos[0] if videos else {}
    tags = primary.get("tags") if isinstance(primary.get("tags"), dict) else {}
    transfer = str(primary.get("color_transfer") or "").lower()
    hdr = "hdr10" if transfer in {"smpte2084", "pq"} else "hlg" if transfer == "arib-std-b67" else None
    return {
        "path": str(path.resolve()),
        "size_bytes": path.stat().st_size,
        "container": str(format_data.get("format_name") or "unknown"),
        "duration_seconds": round(duration, 3),
        "duration_minutes": round(duration / 60, 3),
        "video": {
            "streams": len(videos),
            "width": int(primary.get("width") or 0),
            "height": int(primary.get("height") or 0),
            "codec": str(primary.get("codec_name") or "unknown"),
            "pixel_format": str(primary.get("pix_fmt") or "unknown"),
            "hdr": hdr,
            "title": tags.get("title"),
        },
        "audio": [
            {
                "codec": str(item.get("codec_name") or "unknown"),
                "language": language(item),
                "channels": int(item.get("channels") or 0),
            }
            for item in audios
        ],
        "subtitles": [
            {"codec": str(item.get("codec_name") or "unknown"), "language": language(item)}
            for item in subtitles
        ],
    }


def episode_key(name: str) -> str | None:
    match = re.search(r"(?i)S(\d{1,2})E(\d{1,3})", name)
    return f"S{int(match.group(1)):02d}E{int(match.group(2)):02d}" if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-duration-minutes", type=float)
    parser.add_argument("--duration-tolerance-minutes", type=float, default=2.0)
    parser.add_argument("--expected-resolution")
    parser.add_argument("--preferred-subtitle", action="append", default=["zh-Hans", "en"])
    parser.add_argument("--expected-episode", action="append", default=[])
    args = parser.parse_args()

    if shutil.which("ffprobe") is None:
        raise SystemExit("ERROR: ffprobe is required")
    target = args.path.expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"ERROR: media path does not exist: {target}")
    files = media_files(target)
    if not files:
        raise SystemExit(f"ERROR: no supported media files under {target}")

    inspected: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in files:
        try:
            inspected.append(inspect(path))
        except (RuntimeError, json.JSONDecodeError, OSError) as exc:
            errors.append(str(exc))
    primary = inspected[0] if inspected else {}
    warnings: list[str] = []
    if not primary or primary.get("video", {}).get("streams", 0) < 1:
        errors.append("no readable video stream")
    if float(primary.get("duration_seconds") or 0) <= 0:
        errors.append("media duration is zero or unavailable")
    if args.expected_duration_minutes and primary:
        delta = abs(float(primary.get("duration_minutes") or 0) - args.expected_duration_minutes)
        if delta > args.duration_tolerance_minutes:
            errors.append(
                f"duration differs from expected edition by {delta:.2f} minutes"
            )
    if args.expected_resolution and primary:
        height = int(primary.get("video", {}).get("height") or 0)
        expected = int(re.sub(r"\D", "", args.expected_resolution) or 0)
        if expected and abs(height - expected) > max(16, expected * 0.08):
            warnings.append(f"observed height {height} differs from {args.expected_resolution}")

    subtitle_languages = {
        str(item.get("language") or "und").lower()
        for media in inspected
        for item in media.get("subtitles") or []
    }
    aliases = {
        "zh-hans": {"zh-hans", "zho", "chi", "chs", "zh", "zh-cn"},
        "en": {"en", "eng"},
    }
    missing: list[str] = []
    for preferred in dict.fromkeys(args.preferred_subtitle):
        accepted = aliases.get(preferred.lower(), {preferred.lower()})
        if not subtitle_languages & accepted:
            missing.append(preferred)
    if missing:
        warnings.append("missing preferred subtitle streams: " + ", ".join(missing))

    observed_episodes = {key for path in files if (key := episode_key(path.name))}
    missing_episodes = sorted(set(args.expected_episode) - observed_episodes)
    if missing_episodes:
        errors.append("missing requested episodes: " + ", ".join(missing_episodes))
    partials = partial_files(target)
    if partials:
        warnings.append(f"partial-suffix files remain: {len(partials)}")

    status = "failed" if errors else "passed_with_warnings" if warnings else "passed"
    report = {
        "schema_version": "1.0",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "target": str(target),
        "files": inspected,
        "preferred_subtitles_missing": missing,
        "observed_episodes": sorted(observed_episodes),
        "partial_files": partials,
        "warnings": warnings,
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "files": len(inspected), "warnings": len(warnings), "errors": len(errors), "output": str(args.output)}, ensure_ascii=False, indent=2))
    return 0 if status != "failed" else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
