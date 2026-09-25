#!/usr/bin/env python3
"""Rebuild transcript artifacts from saved DashScope SSE raw responses."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from voice2srt import (
    Chunk,
    Voice2SrtError,
    canonicalize_text,
    dashscope_events_to_cues,
    load_vocabulary,
    media_duration_seconds,
    normalize_cues,
    reported_processed_seconds,
    validate_cues,
    write_json,
    write_srt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--chunk-seconds", type=float, default=240.0)
    args = parser.parse_args()

    output_dir = args.output_dir.expanduser().resolve()
    report_path = output_dir / "report.json"
    if not report_path.is_file():
        raise Voice2SrtError(f"report not found: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("provider") != "dashscope":
        raise Voice2SrtError("rebuild_dashscope only accepts DashScope reports")
    source = Path(str(report.get("input", "")))
    duration_seconds = media_duration_seconds(source)
    duration_ms = round(duration_seconds * 1000)

    cues = []
    raw_files = sorted((output_dir / "raw").glob("chunk-*.json"))
    if not raw_files:
        raise Voice2SrtError("no raw/chunk-*.json responses found")
    for index, raw_path in enumerate(raw_files):
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        events = raw.get("events") if isinstance(raw, dict) else None
        if not isinstance(events, list):
            raise Voice2SrtError(f"raw response has no events array: {raw_path}")
        start_ms = round(index * args.chunk_seconds * 1000)
        chunk = Chunk(
            index=index,
            start_ms=start_ms,
            duration_ms=min(round(args.chunk_seconds * 1000), duration_ms - start_ms),
            path=Path(f"chunk-{index:03d}.mp3"),
        )
        cues.extend(dashscope_events_to_cues(events, chunk))

    vocabulary_source = report.get("vocabulary_source")
    vocabulary = load_vocabulary(Path(vocabulary_source)) if vocabulary_source else []
    for cue in cues:
        cue.text = canonicalize_text(cue.text, vocabulary)
    cues = normalize_cues(cues, duration_ms)
    validation = validate_cues(cues, duration_ms)
    if not validation["ok"]:
        raise Voice2SrtError(f"rebuilt subtitle validation failed: {validation}")
    write_srt(output_dir / "transcript.srt", cues)
    (output_dir / "transcript.txt").write_text(
        "\n".join(cue.text for cue in cues) + "\n", encoding="utf-8"
    )
    write_json(
        output_dir / "transcript.json",
        {
            "schema": "lov-voice2srt/transcript/v1",
            "source": str(source),
            "provider": report.get("provider"),
            "model": report.get("model"),
            "duration_ms": duration_ms,
            "cues": [asdict(cue) for cue in cues],
        },
    )
    report["status"] = "complete-rebuilt-from-raw"
    report["validation"] = validation
    report.pop("actual_billed_seconds_reported", None)
    report["provider_processed_seconds_reported"] = reported_processed_seconds(raw_files)
    report["raw_interpretation"] = "cumulative SSE sentences differenced by text/word prefix"
    write_json(report_path, report)
    print(json.dumps({"status": "complete", "validation": validation}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Voice2SrtError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
