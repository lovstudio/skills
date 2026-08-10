#!/usr/bin/env python3
"""Build a semantic-analysis pack from an SRT or WebVTT subtitle file."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "0.2.0"
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


@dataclass
class Cue:
    index: int
    start: float
    end: float
    text: str


@dataclass
class TranscriptWindow:
    start: float
    end: float
    cue_count: int
    text: str


@dataclass
class SubtitleGap:
    start: float
    end: float
    duration: float
    before: str
    after: str


def parse_timecode(value: str) -> float:
    """Parse HH:MM:SS.mmm, HH:MM:SS, or MM:SS.mmm."""
    cleaned = value.strip().replace(",", ".")
    parts = cleaned.split(":")
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        if minutes >= 60:
            raise ValueError(f"invalid timecode: {value!r}")
    elif len(parts) == 2:
        hours = 0
        minutes = int(parts[0])
        seconds = float(parts[1])
    else:
        raise ValueError(f"unsupported timecode: {value!r}")
    if minutes < 0 or seconds < 0 or seconds >= 60:
        raise ValueError(f"invalid timecode: {value!r}")
    return hours * 3600 + minutes * 60 + seconds


def clean_text(lines: Iterable[str]) -> str:
    parts: List[str] = []
    for line in lines:
        stripped = TAG_RE.sub("", html.unescape(line)).strip()
        if stripped:
            parts.append(stripped)
    return SPACE_RE.sub(" ", " ".join(parts)).strip()


def parse_subtitles(path: Path) -> Tuple[List[Cue], List[str]]:
    raw = path.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\s*\r?\n", raw.strip())
    cues: List[Cue] = []
    warnings: List[str] = []

    for block in blocks:
        lines = [line.rstrip("\r") for line in block.splitlines()]
        timing_index: Optional[int] = None
        for i, line in enumerate(lines):
            if "-->" in line:
                timing_index = i
                break
        if timing_index is None:
            continue

        timing = lines[timing_index]
        start_raw, end_raw = timing.split("-->", 1)
        end_token = end_raw.strip().split()[0]
        try:
            start = parse_timecode(start_raw)
            end = parse_timecode(end_token)
        except (ValueError, IndexError) as exc:
            warnings.append(f"Skipped timing line {timing!r}: {exc}")
            continue

        if end <= start:
            warnings.append(f"Skipped non-positive cue at {timing!r}")
            continue

        text = clean_text(lines[timing_index + 1 :])
        if not text:
            continue
        cues.append(Cue(index=len(cues) + 1, start=start, end=end, text=text))

    if not cues:
        raise ValueError("no valid subtitle cues were found")

    for previous, current in zip(cues, cues[1:]):
        if current.start < previous.start:
            warnings.append(
                f"Non-monotonic cue order near {format_clock(current.start)}"
            )
        if current.start < previous.end:
            overlap = previous.end - current.start
            if overlap > 1.0:
                warnings.append(
                    f"Subtitle overlap of {overlap:.2f}s near "
                    f"{format_clock(current.start)}"
                )
    return cues, warnings


def build_windows(cues: Sequence[Cue], chunk_seconds: int) -> List[TranscriptWindow]:
    buckets: Dict[int, List[Cue]] = {}
    duration = max(cue.end for cue in cues)
    for cue in cues:
        bucket = int(cue.start // chunk_seconds)
        buckets.setdefault(bucket, []).append(cue)

    windows: List[TranscriptWindow] = []
    for bucket in sorted(buckets):
        group = buckets[bucket]
        text_parts: List[str] = []
        previous_text = ""
        for cue in group:
            if cue.text != previous_text:
                text_parts.append(cue.text)
            previous_text = cue.text
        windows.append(
            TranscriptWindow(
                start=bucket * chunk_seconds,
                end=min(
                    duration,
                    max(group[-1].end, (bucket + 1) * chunk_seconds),
                ),
                cue_count=len(group),
                text=" ".join(text_parts),
            )
        )
    return windows


def find_gaps(
    cues: Sequence[Cue], threshold: float, max_gaps: int
) -> List[SubtitleGap]:
    gaps: List[SubtitleGap] = []
    for previous, current in zip(cues, cues[1:]):
        duration = current.start - previous.end
        if duration >= threshold:
            gaps.append(
                SubtitleGap(
                    start=previous.end,
                    end=current.start,
                    duration=duration,
                    before=previous.text,
                    after=current.text,
                )
            )
    selected = sorted(gaps, key=lambda item: item.duration, reverse=True)[:max_gaps]
    return sorted(selected, key=lambda item: item.start)


def format_clock(seconds: float, include_hours: Optional[bool] = None) -> str:
    whole = max(0, int(seconds))
    hours, remainder = divmod(whole, 3600)
    minutes, secs = divmod(remainder, 60)
    if include_hours is None:
        include_hours = hours > 0
    if include_hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours * 60 + minutes:02d}:{secs:02d}"


def shorten(text: str, limit: int = 80) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def to_payload(
    path: Path,
    cues: Sequence[Cue],
    windows: Sequence[TranscriptWindow],
    gaps: Sequence[SubtitleGap],
    warnings: Sequence[str],
    segments: int,
) -> dict:
    duration = max(cue.end for cue in cues)
    return {
        "source": str(path),
        "format": path.suffix.lower().lstrip("."),
        "duration_seconds": round(duration, 3),
        "duration": format_clock(duration),
        "cue_count": len(cues),
        "requested_chapters": segments,
        "warnings": list(warnings),
        "transcript_windows": [asdict(window) for window in windows],
        "meaningful_gaps": [asdict(gap) for gap in gaps],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Video Chapter Analysis Pack",
        "",
        f"- Source: `{payload['source']}`",
        f"- Subtitle format: `{payload['format'].upper()}`",
        f"- Duration: `{payload['duration']}` "
        f"({payload['duration_seconds']:.3f}s)",
        f"- Cues: `{payload['cue_count']}`",
        f"- Requested chapters: `{payload['requested_chapters']}`",
        "",
        "> Transcript windows are reading aids, not proposed chapters. "
        "Choose boundaries by meaning first.",
    ]

    warnings = payload["warnings"]
    if warnings:
        lines.extend(["", "## Parser Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    lines.extend(["", "## Transcript Timeline", ""])
    for window in payload["transcript_windows"]:
        lines.extend(
            [
                f"### {format_clock(window['start'])}–"
                f"{format_clock(window['end'])} "
                f"({window['cue_count']} cues)",
                "",
                window["text"],
                "",
            ]
        )

    lines.extend(["## Meaningful Subtitle Gaps", ""])
    if not payload["meaningful_gaps"]:
        lines.append("- None above the configured threshold.")
    else:
        for gap in payload["meaningful_gaps"]:
            lines.append(
                f"- `{format_clock(gap['start'])}–{format_clock(gap['end'])}` "
                f"({gap['duration']:.2f}s): "
                f"“{shorten(gap['before'])}” → “{shorten(gap['after'])}”"
            )

    lines.extend(
        [
            "",
            "## Output Checklist",
            "",
            "- Use exactly the requested number of chapters.",
            "- Start at 00:00 and use strictly increasing cue-aligned timestamps.",
            "- Prefer semantic transitions over equal-length slices.",
            "- Return time range, concrete title, and one-sentence summary.",
            "- List dead air or troubleshooting separately as optional trims.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse SRT/VTT subtitles into a time-windowed semantic analysis pack."
        )
    )
    parser.add_argument("--input", required=True, help="Input .srt or .vtt file")
    parser.add_argument(
        "--segments",
        type=int,
        choices=(3, 4, 5),
        default=5,
        help="Requested chapter count (default: 5)",
    )
    parser.add_argument(
        "--chunk-seconds",
        type=int,
        default=60,
        help="Transcript window size in seconds (default: 60)",
    )
    parser.add_argument(
        "--gap-threshold",
        type=float,
        default=1.5,
        help="Minimum subtitle gap to report, in seconds (default: 1.5)",
    )
    parser.add_argument(
        "--max-gaps",
        type=int,
        default=20,
        help="Maximum meaningful gaps to include (default: 20)",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Output path, or - for stdout (default: -)",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args(argv)
    if args.chunk_seconds < 15:
        parser.error("--chunk-seconds must be at least 15")
    if args.gap_threshold < 0:
        parser.error("--gap-threshold cannot be negative")
    if args.max_gaps < 0:
        parser.error("--max-gaps cannot be negative")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input).expanduser()
    if not input_path.is_file():
        print(f"error: subtitle file not found: {input_path}", file=sys.stderr)
        return 2
    if input_path.suffix.lower() not in {".srt", ".vtt"}:
        print("error: input must be an .srt or .vtt file", file=sys.stderr)
        return 2

    try:
        cues, warnings = parse_subtitles(input_path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: could not parse {input_path}: {exc}", file=sys.stderr)
        return 2

    windows = build_windows(cues, args.chunk_seconds)
    gaps = find_gaps(cues, args.gap_threshold, args.max_gaps)
    payload = to_payload(
        input_path, cues, windows, gaps, warnings, args.segments
    )
    output = (
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.format == "json"
        else render_markdown(payload)
    )

    if args.output == "-":
        sys.stdout.write(output)
    else:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Wrote analysis pack: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
