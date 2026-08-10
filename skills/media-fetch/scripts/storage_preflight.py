#!/usr/bin/env python3
"""Check destination capacity before Media Fetch starts payload transfer."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


GIB = 1024**3
MIB = 1024**2


def read_decision(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: cannot read decision JSON {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("ranked"), list):
        raise SystemExit("ERROR: decision document must contain a ranked array")
    return data


def candidate_for(decision: dict[str, Any], selected_id: str | None) -> dict[str, Any]:
    target = selected_id or decision.get("selected_id")
    for row in decision["ranked"]:
        if not isinstance(row, dict) or not isinstance(row.get("candidate"), dict):
            continue
        candidate = row["candidate"]
        if candidate.get("id") == target:
            return candidate
    raise SystemExit(f"ERROR: selected candidate not found: {target}")


def existing_parent(path: Path) -> Path:
    current = path.expanduser().resolve(strict=False)
    while not current.exists() and current != current.parent:
        current = current.parent
    if not current.exists():
        raise SystemExit(f"ERROR: no existing parent for destination: {path}")
    return current


def human(value: int) -> str:
    return f"{value / GIB:.2f} GiB"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--selected-id")
    parser.add_argument("--output-dir", type=Path, default=Path.home() / "Downloads/Media")
    parser.add_argument("--reserve-free-gib", type=float, default=15.0)
    parser.add_argument("--probe-count", type=int, default=3)
    parser.add_argument("--probe-budget-mib", type=int, default=512)
    parser.add_argument("--overhead-ratio", type=float, default=0.10)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    decision = read_decision(args.decision)
    candidate = candidate_for(decision, args.selected_id)
    payload_bytes = int(candidate.get("size_bytes") or 0)
    destination = args.output_dir.expanduser().resolve(strict=False)
    filesystem_path = existing_parent(destination)
    usage = shutil.disk_usage(filesystem_path)

    if payload_bytes <= 0:
        result = {
            "ok": False,
            "status": "size_unknown",
            "candidate_id": candidate.get("id"),
            "destination": str(destination),
            "filesystem_path": str(filesystem_path),
            "available_bytes": usage.free,
            "message": "candidate size is required before payload transfer",
        }
        exit_code = 2
    else:
        overhead = int(payload_bytes * max(0.0, args.overhead_ratio))
        probe = max(0, args.probe_count) * max(0, args.probe_budget_mib) * MIB
        reserve = int(max(0.0, args.reserve_free_gib) * GIB)
        required = payload_bytes + overhead + probe + reserve
        shortfall = max(0, required - usage.free)
        result = {
            "ok": shortfall == 0,
            "status": "ready" if shortfall == 0 else "capacity_shortfall",
            "candidate_id": candidate.get("id"),
            "destination": str(destination),
            "filesystem_path": str(filesystem_path),
            "payload_bytes": payload_bytes,
            "overhead_bytes": overhead,
            "probe_bytes": probe,
            "reserve_bytes": reserve,
            "required_bytes": required,
            "available_bytes": usage.free,
            "shortfall_bytes": shortfall,
            "required_human": human(required),
            "available_human": human(usage.free),
            "shortfall_human": human(shortfall),
        }
        exit_code = 0 if shortfall == 0 else 3

    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(text + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
