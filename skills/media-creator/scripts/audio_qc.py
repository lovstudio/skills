#!/usr/bin/env python3
"""Inspect audio streams and measure integrated loudness with FFmpeg loudnorm."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def parse_number(value: Any) -> float | None:
    if value in (None, "", "N/A", "-inf", "-Infinity"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def probe_audio(path: Path) -> list[dict[str, Any]]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe audio inspection failed")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid JSON: {exc}") from exc
    streams = []
    for stream in data.get("streams", []):
        streams.append(
            {
                "index": stream.get("index"),
                "codec_name": stream.get("codec_name"),
                "sample_rate": parse_number(stream.get("sample_rate")),
                "channels": stream.get("channels"),
                "channel_layout": stream.get("channel_layout"),
                "bit_rate": parse_number(stream.get("bit_rate")),
                "duration_seconds": parse_number(stream.get("duration")),
                "tags": stream.get("tags", {}),
            }
        )
    return streams


def measure_loudness(path: Path, target_i: float, target_tp: float) -> dict[str, Any]:
    filter_spec = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA=11:print_format=json"
    )
    result = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "info",
            "-nostats",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-af",
            filter_spec,
            "-f",
            "null",
            "-",
        ]
    )
    combined = f"{result.stdout}\n{result.stderr}"
    matches = re.findall(r"\{\s*\"input_i\"[\s\S]*?\}", combined)
    if not matches:
        return {
            "command_ok": result.returncode == 0,
            "error": result.stderr.strip() or "loudnorm did not emit JSON metrics",
        }
    try:
        raw = json.loads(matches[-1])
    except json.JSONDecodeError as exc:
        return {
            "command_ok": result.returncode == 0,
            "error": f"loudnorm JSON parse failed: {exc}",
        }
    integrated = parse_number(raw.get("input_i", raw.get("measured_I")))
    true_peak = parse_number(raw.get("input_tp", raw.get("measured_TP")))
    return {
        "command_ok": result.returncode == 0,
        "integrated_lufs_i": integrated,
        "true_peak_dbfs": true_peak,
        "loudnorm": raw,
    }


def build_report(path: Path, target_i: float, target_tp: float, peak_ceiling: float) -> dict[str, Any]:
    streams = probe_audio(path)
    if not streams:
        return {
            "schema": "lovstudio/audio-qc/v1",
            "input": {"name": path.name, "path": str(path)},
            "status": "fail",
            "audio_streams": [],
            "error": "no audio stream found",
        }
    loudness = measure_loudness(path, target_i, target_tp)
    integrated = loudness.get("integrated_lufs_i")
    true_peak = loudness.get("true_peak_dbfs")
    warnings: list[str] = []
    if integrated is None:
        warnings.append("integrated loudness was not measured")
    elif abs(integrated - target_i) > 1.5:
        warnings.append(f"integrated loudness is outside target tolerance: {integrated:.2f} LUFS-I")
    if true_peak is None:
        warnings.append("true peak was not measured")
    elif true_peak > peak_ceiling:
        warnings.append(f"true peak exceeds ceiling: {true_peak:.2f} dBFS")
    status = "pass" if not warnings and loudness.get("command_ok") else "warn"
    if not loudness.get("command_ok"):
        status = "fail"
    return {
        "schema": "lovstudio/audio-qc/v1",
        "input": {
            "name": path.name,
            "path": str(path),
            "size_bytes": path.stat().st_size,
        },
        "status": status,
        "targets": {
            "integrated_lufs_i": target_i,
            "true_peak_dbfs": target_tp,
            "true_peak_ceiling_dbfs": peak_ceiling,
            "lufs_tolerance": 1.5,
        },
        "audio_streams": streams,
        "measurements": {
            "integrated_lufs_i": integrated,
            "true_peak_dbfs": true_peak,
        },
        "warnings": warnings,
        "loudnorm": loudness.get("loudnorm"),
        "error": loudness.get("error"),
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
    parser.add_argument("--input", required=True, help="Input video or audio file")
    parser.add_argument("--target-i", type=float, default=-16.0, help="Target integrated loudness")
    parser.add_argument("--target-tp", type=float, default=-1.5, help="Loudnorm target true peak")
    parser.add_argument("--peak-ceiling", type=float, default=-1.0, help="Maximum accepted measured true peak")
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    parser.add_argument("--strict", action="store_true", help="Return non-zero for warnings")
    args = parser.parse_args()

    path = Path(args.input).expanduser()
    if not path.is_file():
        print(f"ERROR [audio-qc] input file does not exist: {path}", file=sys.stderr)
        return 1
    try:
        report = build_report(path, args.target_i, args.target_tp, args.peak_ceiling)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR [audio-qc] {exc}", file=sys.stderr)
        return 1
    write_json(report, args.output, args.pretty)
    if report["status"] == "fail":
        return 1
    if args.strict and report["status"] == "warn":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
