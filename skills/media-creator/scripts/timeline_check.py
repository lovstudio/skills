#!/usr/bin/env python3
"""Validate a media edit manifest for ordering, duration, and protected segments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EPSILON = 0.001


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest root must be an object")
    return value


def as_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number") from exc
    if result < 0:
        raise ValueError(f"{label} must be non-negative")
    return result


def validate(manifest: dict[str, Any], duration: float | None, contiguous: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    segments = manifest.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty list")
        segments = []

    seen: set[str] = set()
    previous_end: float | None = None
    protected_count = 0
    normalized: list[dict[str, Any]] = []

    for index, segment in enumerate(segments):
        label = f"segments[{index}]"
        if not isinstance(segment, dict):
            errors.append(f"{label} must be an object")
            continue
        segment_id = str(segment.get("id", "")).strip()
        if not segment_id:
            errors.append(f"{label}.id is required")
        elif segment_id in seen:
            errors.append(f"{label}.id is duplicated: {segment_id}")
        seen.add(segment_id)
        try:
            start = as_number(segment.get("source_start"), f"{label}.source_start")
            end = as_number(segment.get("source_end"), f"{label}.source_end")
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if end <= start:
            errors.append(f"{label} must have source_end greater than source_start")
        if previous_end is not None:
            if start < previous_end - EPSILON:
                errors.append(f"{label} overlaps the previous segment")
            elif start > previous_end + EPSILON:
                message = f"gap between {previous_end:.3f}s and {start:.3f}s"
                if contiguous:
                    errors.append(message)
                else:
                    warnings.append(message)
        previous_end = end if previous_end is None else max(previous_end, end)
        if segment.get("protected_audio") is True:
            protected_count += 1
        normalized.append(
            {
                "id": segment_id,
                "source_start": start,
                "source_end": end,
                "duration_seconds": max(0.0, end - start),
                "protected_audio": segment.get("protected_audio") is True,
                "role": segment.get("role"),
            }
        )

    if duration is not None and previous_end is not None:
        if previous_end > duration + EPSILON:
            errors.append(
                f"last segment ends at {previous_end:.3f}s beyond declared duration {duration:.3f}s"
            )
        elif previous_end < duration - EPSILON:
            warnings.append(
                f"timeline ends at {previous_end:.3f}s before declared duration {duration:.3f}s"
            )

    return {
        "schema": "lovstudio/media-timeline-check/v1",
        "ok": not errors,
        "segment_count": len(normalized),
        "protected_audio_count": protected_count,
        "duration_seconds": duration,
        "timeline_end_seconds": previous_end,
        "segments": normalized,
        "warnings": warnings,
        "errors": errors,
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
    parser.add_argument("--input", required=True, help="Edit manifest JSON")
    parser.add_argument("--duration", type=float, help="Optional source duration in seconds")
    parser.add_argument("--contiguous", action="store_true", help="Treat gaps as errors")
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args()

    try:
        report = validate(read_json(Path(args.input).expanduser()), args.duration, args.contiguous)
    except (OSError, ValueError) as exc:
        print(f"ERROR [timeline-check] {exc}", file=sys.stderr)
        return 1
    write_json(report, args.output, args.pretty)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
