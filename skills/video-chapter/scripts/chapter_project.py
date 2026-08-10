#!/usr/bin/env python3
"""Create and validate the canonical Video Chapter project file."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

VERSION = "0.2.0"
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?$")


def parse_timecode(value: str) -> float:
    cleaned = value.strip().replace(",", ".")
    parts = cleaned.split(":")
    if len(parts) == 3:
        hours, minutes = int(parts[0]), int(parts[1])
        seconds = float(parts[2])
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = int(parts[0]), float(parts[1])
    else:
        raise ValueError(f"unsupported timecode: {value!r}")
    if hours < 0 or minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
        raise ValueError(f"invalid timecode: {value!r}")
    return hours * 3600 + minutes * 60 + seconds


def format_clock(seconds: float) -> str:
    whole = max(0, int(seconds))
    hours, remainder = divmod(whole, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse_rate(value: str) -> float:
    numerator, separator, denominator = value.partition("/")
    if separator:
        divisor = float(denominator)
        if divisor == 0:
            return 0
        return float(numerator) / divisor
    return float(value)


def probe_video(path: Path) -> Dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height,avg_frame_rate,r_frame_rate",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise ValueError("ffprobe is required to inspect a source video") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or "ffprobe failed"
        raise ValueError(f"could not inspect video: {detail}") from exc

    payload = json.loads(result.stdout)
    video_stream = next(
        (
            stream
            for stream in payload.get("streams", [])
            if stream.get("codec_type") == "video"
            or ("width" in stream and "height" in stream)
        ),
        None,
    )
    if video_stream is None:
        raise ValueError("source has no video stream")

    rate = parse_rate(
        video_stream.get("avg_frame_rate")
        or video_stream.get("r_frame_rate")
        or "0"
    )
    duration = float(payload.get("format", {}).get("duration") or 0)
    if duration <= 0 or rate <= 0:
        raise ValueError("source duration or frame rate is invalid")
    return {
        "src": str(path.resolve()),
        "duration": round(duration, 3),
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "fps": round(rate, 6),
    }


def parse_chapter_lines(path: Path) -> List[Dict[str, Any]]:
    chapters: List[Dict[str, Any]] = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            timestamp, content = line.split(maxsplit=1)
        except ValueError as exc:
            raise ValueError(
                f"line {line_number}: expected 'MM:SS title'"
            ) from exc
        title, separator, summary = content.partition("|")
        title = title.strip()
        summary = summary.strip() if separator else ""
        if not title:
            raise ValueError(f"line {line_number}: chapter title is empty")
        chapters.append(
            {
                "id": f"chapter-{len(chapters) + 1}",
                "start": round(parse_timecode(timestamp), 3),
                "end": 0,
                "title": title,
                "summary": summary,
            }
        )
    if not chapters:
        raise ValueError("chapter list is empty")
    return chapters


def default_style(width: int, height: int) -> Dict[str, Any]:
    scale = min(width / 1920, height / 1080)
    return {
        "position": "bottom",
        "marginX": round(96 * scale),
        "marginBottom": round(72 * scale),
        "barHeight": max(4, round(12 * scale)),
        "gap": max(2, round(8 * scale)),
        "labelGap": max(6, round(18 * scale)),
        "fontFamily": "PingFang SC",
        "fontFile": None,
        "fontSize": max(18, round(34 * scale)),
        "textColor": "#F5F1E8",
        "activeColor": "#EB6637",
        "inactiveColor": "#FFFFFF38",
        "panelColor": "#101419CC",
        "cornerRadius": max(2, round(6 * scale)),
        "showTitle": True,
        "showIndex": True,
    }


def build_project(
    *,
    name: str,
    chapters: List[Dict[str, Any]],
    video: Dict[str, Any],
) -> Dict[str, Any]:
    duration = float(video["duration"])
    for index, chapter in enumerate(chapters):
        chapter["end"] = round(
            chapters[index + 1]["start"] if index + 1 < len(chapters) else duration,
            3,
        )
    return {
        "schemaVersion": "1.0",
        "name": name,
        "video": video,
        "chapters": chapters,
        "style": default_style(int(video["width"]), int(video["height"])),
        "export": {
            "codec": "h264",
            "crf": 18,
            "preset": "medium",
            "alphaCodec": "prores_4444",
        },
    }


def _require_number(
    errors: List[str],
    owner: Dict[str, Any],
    key: str,
    *,
    minimum: Optional[float] = None,
) -> None:
    value = owner.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{key} must be a number")
        return
    if minimum is not None and value < minimum:
        errors.append(f"{key} must be at least {minimum}")


def validate_project(project: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if project.get("schemaVersion") != "1.0":
        errors.append("schemaVersion must be '1.0'")
    if not isinstance(project.get("name"), str) or not project.get("name", "").strip():
        errors.append("name must be a non-empty string")

    video = project.get("video")
    if not isinstance(video, dict):
        errors.append("video must be an object")
        video = {}
    for key in ("duration", "width", "height", "fps"):
        _require_number(errors, video, key, minimum=0.001)
    if not isinstance(video.get("src"), str):
        errors.append("video.src must be a string")
    elif video["src"] and not Path(video["src"]).expanduser().is_file():
        warnings.append(f"source video is not present at {video['src']}")

    chapters = project.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        errors.append("chapters must be a non-empty array")
        chapters = []
    duration = float(video.get("duration") or 0)
    seen_ids = set()
    previous_end = 0.0
    for index, chapter in enumerate(chapters):
        label = f"chapters[{index}]"
        if not isinstance(chapter, dict):
            errors.append(f"{label} must be an object")
            continue
        chapter_id = chapter.get("id")
        if not isinstance(chapter_id, str) or not chapter_id:
            errors.append(f"{label}.id must be a non-empty string")
        elif chapter_id in seen_ids:
            errors.append(f"{label}.id is duplicated")
        seen_ids.add(chapter_id)
        for key in ("start", "end"):
            value = chapter.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{label}.{key} must be a number")
        if not isinstance(chapter.get("title"), str) or not chapter.get("title", "").strip():
            errors.append(f"{label}.title must be a non-empty string")
        if not isinstance(chapter.get("summary"), str):
            errors.append(f"{label}.summary must be a string")
        start = float(chapter.get("start") or 0)
        end = float(chapter.get("end") or 0)
        if end <= start:
            errors.append(f"{label}.end must be greater than start")
        if index == 0 and abs(start) > 0.01:
            errors.append("the first chapter must start at 0")
        if index > 0 and abs(start - previous_end) > 0.02:
            errors.append(f"{label}.start must equal the previous chapter end")
        previous_end = end
    if chapters and duration > 0 and abs(previous_end - duration) > 0.05:
        errors.append("the final chapter end must equal video.duration")

    style = project.get("style")
    if not isinstance(style, dict):
        errors.append("style must be an object")
        style = {}
    if style.get("position") not in {"top", "bottom"}:
        errors.append("style.position must be 'top' or 'bottom'")
    for key in (
        "marginX",
        "marginBottom",
        "barHeight",
        "gap",
        "labelGap",
        "fontSize",
        "cornerRadius",
    ):
        _require_number(errors, style, key, minimum=0)
    for key in ("textColor", "activeColor", "inactiveColor", "panelColor"):
        value = style.get(key)
        if not isinstance(value, str) or not COLOR_RE.fullmatch(value):
            errors.append(f"style.{key} must be #RRGGBB or #RRGGBBAA")
    if not isinstance(style.get("fontFamily"), str) or not style.get("fontFamily"):
        errors.append("style.fontFamily must be a non-empty string")
    if style.get("fontFile") is not None and not isinstance(style.get("fontFile"), str):
        errors.append("style.fontFile must be a string or null")
    for key in ("showTitle", "showIndex"):
        if not isinstance(style.get(key), bool):
            errors.append(f"style.{key} must be a boolean")

    export = project.get("export")
    if not isinstance(export, dict):
        errors.append("export must be an object")
    return errors, warnings


def load_project(path: Path) -> Dict[str, Any]:
    try:
        project = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read project: {exc}") from exc
    if not isinstance(project, dict):
        raise ValueError("project root must be a JSON object")
    return project


def load_valid_project(path: Path) -> Tuple[Dict[str, Any], List[str]]:
    project = load_project(path)
    errors, warnings = validate_project(project)
    if errors:
        raise ValueError("; ".join(errors))
    return project, warnings


def command_create(args: argparse.Namespace) -> int:
    chapters_path = Path(args.chapters).expanduser()
    if not chapters_path.is_file():
        print(f"error: chapter list not found: {chapters_path}", file=sys.stderr)
        return 2
    try:
        chapters = parse_chapter_lines(chapters_path)
        if args.video:
            video_path = Path(args.video).expanduser()
            if not video_path.is_file():
                raise ValueError(f"video not found: {video_path}")
            video = probe_video(video_path)
        else:
            if not args.duration:
                raise ValueError("--duration is required when --video is omitted")
            video = {
                "src": "",
                "duration": round(parse_timecode(args.duration), 3),
                "width": args.width,
                "height": args.height,
                "fps": args.fps,
            }
        project = build_project(name=args.name, chapters=chapters, video=video)
        errors, warnings = validate_project(project)
        if errors:
            raise ValueError("; ".join(errors))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote project: {output_path}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.project).expanduser()
    try:
        project = load_project(path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors, warnings = validate_project(project)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        f"Valid project: {len(project['chapters'])} chapters, "
        f"{format_clock(float(project['video']['duration']))}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a chapter project")
    create.add_argument("--chapters", required=True, help="Timestamp/title text file")
    create.add_argument("--video", help="Source video to inspect with ffprobe")
    create.add_argument("--duration", help="MM:SS or HH:MM:SS without --video")
    create.add_argument("--width", type=int, default=1920)
    create.add_argument("--height", type=int, default=1080)
    create.add_argument("--fps", type=float, default=30)
    create.add_argument("--name", default="Video chapter project")
    create.add_argument("--output", required=True, help="Output JSON path")
    create.set_defaults(func=command_create)

    validate = subparsers.add_parser("validate", help="Validate project invariants")
    validate.add_argument("--project", required=True, help="Project JSON path")
    validate.set_defaults(func=command_validate)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

