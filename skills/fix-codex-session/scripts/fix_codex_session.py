#!/usr/bin/env python3
"""Diagnose and safely repair a poisoned Codex thread rollout.

A Codex thread can become un-resumable when a ``function_call`` tool item is
recorded in a turn without a sibling ``function_call_output`` for the same
``call_id``. When the host rebuilds the conversation from the rollout JSONL for
the next request, the dangling item makes the API reject it with:

    No tool output found for tool call call_<....>.

This script is read-only by default. It inspects the rollout files that belong
to a thread id under a Codex home directory, reports the health of each turn,
and (only with ``--fix``) writes a repaired copy that truncates at the last
healthy milestone. It never overwrites the original unless ``--write`` is
given; otherwise it writes ``<rollout>.repaired.jsonl`` in the same directory.

Deterministic, no external package dependencies (stdlib only).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


ROUTINE_RE = re.compile(r"^rollout-.*\.jsonl$")


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                records.append(
                    {
                        "_unparsed": True,
                        "_line": line_no,
                        "_error": str(exc),
                    }
                )
    return records


def _as_records(path: Path) -> List[Dict[str, Any]]:
    return _load_jsonl(path)


def _collect_call_ids(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map every function_call / function_call_output call_id to its items."""
    calls: Dict[str, Dict[str, Any]] = {}
    outputs: Dict[str, Dict[str, Any]] = {}
    for idx, rec in enumerate(records):
        if rec.get("_unparsed"):
            continue
        if rec.get("type") != "response_item":
            continue
        payload = rec.get("payload", {})
        item_type = payload.get("type")
        call_id = payload.get("call_id")
        entry = {"index": idx, "line": idx + 1, "item": payload}
        if item_type in ("function_call", "custom_tool_call"):
            calls.setdefault(str(call_id), entry)
        elif item_type == "function_call_output":
            outputs.setdefault(str(call_id), entry)
    return {"calls": calls, "outputs": outputs}


def _extract_reported_call_id(error: Any) -> Optional[str]:
    """Pull the tool call id named in a 'No tool output found' error."""
    text = str(error)
    match = re.search(r"No tool output found for tool call ([A-Za-z0-9_\-]+)", text)
    return match.group(1) if match else None


def _export_globals(thread_id: str, codex_home: Path) -> List[Path]:
    """Return rollout files under codex_home whose name mentions the thread id."""
    found: List[Path] = []
    if not codex_home.is_dir():
        return found
    for dirpath, _dirnames, filenames in os.walk(codex_home):
        for filename in filenames:
            if thread_id in filename and ROUTINE_RE.match(filename):
                found.append(Path(dirpath) / filename)
    found.sort(key=lambda p: (p.stat().st_mtime, str(p)), reverse=True)
    return found


def analyze(thread_id: str, codex_home: Path) -> Dict[str, Any]:
    """Analyze the thread's rollout files for dangling tool-call pairing."""
    files = _export_globals(thread_id, codex_home)
    result: Dict[str, Any] = {
        "thread_id": thread_id,
        "codex_home": str(codex_home),
        "files_found": len(files),
        "files": [],
        "summary": {"healthy": 0, "poisoned": 0, "unparsed": 0},
    }
    for fp in files:
        records = _as_records(fp)
        coll = _collect_call_ids(records)
        calls = coll["calls"]
        outputs = coll["outputs"]
        orphan_calls = [c for c in calls if c not in outputs]
        unparsed_count = sum(1 for r in records if r.get("_unparsed"))
        tasks = [
            r
            for r in records
            if r.get("type") == "event_msg"
            and (r.get("payload", {}) or {}).get("type") == "task_complete"
        ]
        last_task = tasks[-1] if tasks else None
        last_error: Optional[str] = None
        if last_task:
            err = (last_task.get("payload", {}) or {}).get("error")
            last_error = json.dumps(err, ensure_ascii=False) if err else None
        reported_call_id = _extract_reported_call_id(last_error)
        no_output_error = "No tool output found" in (last_error or "")
        # A file is poisoned when the last completed turn recorded the validation
        # error. The reported call_id should be a real function_call in this file
        # whose output is missing from the same contiguous turn sequence.
        poisoned = no_output_error or bool(reported_call_id and reported_call_id not in outputs)
        if poisoned:
            result["summary"]["poisoned"] += 1
        elif unparsed_count:
            result["summary"]["unparsed"] += 1
        else:
            result["summary"]["healthy"] += 1
        result["files"].append(
            {
                "path": str(fp),
                "bytes": fp.stat().st_size,
                "lines": len(records),
                "unparsed_lines": unparsed_count,
                "calls": len(calls),
                "outputs": len(outputs),
                "dangling_calls": orphan_calls,
                "reported_call_id": reported_call_id,
                "reported_call_present": reported_call_id in calls if reported_call_id else False,
                "reported_output_present": reported_call_id in outputs if reported_call_id else False,
                "last_turn_error": last_error,
                "poisoned": poisoned,
            }
        )
    return result


def _last_healthy_cut(records: List[Dict[str, Any]]) -> int:
    """Return the record index just after the last successfully completed turn."""
    last_good = -1
    for idx, rec in enumerate(records):
        if rec.get("type") == "event_msg":
            payload = rec.get("payload", {}) or {}
            if payload.get("type") == "task_complete":
                error = payload.get("error")
                if not error:
                    last_good = idx + 1
    # Always allow cutting after the last clean record even if no task marker.
    return last_good if last_good > 0 else len(records)


def repair(thread_id: str, codex_home: Path, write: bool) -> Dict[str, Any]:
    """Write a repaired rollout that stops after the last healthy milestone."""
    analysis = analyze(thread_id, codex_home)
    poisoned_entries = [e for e in analysis["files"] if e["poisoned"]]
    # Prefer the poisoning file that actually carries the reported call and the
    # real history; fall back to the most recently updated poisoned file.
    def sort_key(entry: Dict[str, Any]) -> tuple:
        main = entry.get("reported_call_present") or entry.get("calls", 0) > 0
        recency = Path(entry["path"]).stat().st_mtime
        return (1 if main else 0, entry.get("lines", 0), recency)

    file_entry = max(poisoned_entries, key=sort_key, default=None)
    if not file_entry:
        analysis["repaired"] = False
        analysis["reason"] = "no poisoned rollout found; nothing to repair"
        return analysis

    path = Path(file_entry["path"])
    records = _as_records(path)
    cut_index = _last_healthy_cut(records)
    final_records = list(records[:cut_index])
    removed_coll = _collect_call_ids(records[cut_index:])
    dangling = [c for c in removed_coll["calls"] if c not in removed_coll["outputs"]]

    out_path = path
    if not write:
        out_path = path.with_name(path.name + ".repaired.jsonl")
    backup_path: Optional[str] = None
    if write:
        backup_path = str(path.with_name(path.name + ".bak"))
        with open(backup_path, "w", encoding="utf-8") as bh:
            bh.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    with open(out_path, "w", encoding="utf-8") as oh:
        oh.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final_records))

    analysis["repaired"] = True
    analysis["original_path"] = str(path)
    analysis["repaired_path"] = str(out_path)
    analysis["backup_path"] = backup_path
    analysis["cut_at_record"] = cut_index
    analysis["kept_records"] = len(final_records)
    analysis["dropped_records"] = len(records) - len(final_records)
    analysis["dangling_removed"] = dangling
    return analysis


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("thread_id", help="Codex thread id, e.g. 01a08678-4e04-…")
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
        help="Path to the Codex home that holds sessions/. Default: ~/.codex",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Write a repaired rollout (into a .repaired.jsonl by default)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite the original rollout (with a .bak backup) instead",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    if args.fix:
        out = repair(args.thread_id, Path(args.codex_home), args.write)
    else:
        out = analyze(args.thread_id, Path(args.codex_home))

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"thread: {out['thread_id']}")
    print(f"codex_home: {out['codex_home']}")
    print(f"rollouts found: {out['files_found']}")
    if "summary" in out:
        print(
            "summary: "
            f"healthy={out['summary']['healthy']} "
            f"poisoned={out['summary']['poisoned']} "
            f"unparsed={out['summary']['unparsed']}"
        )
    for entry in out.get("files", []):
        print(f"  - {entry['path']} ({entry['bytes']} B)")
        print(
            f"    calls={entry['calls']} outputs={entry['outputs']} "
            f"dangling_calls={len(entry['dangling_calls'])} reported_call_id={entry.get('reported_call_id')} "
            f"unparsed_lines={entry['unparsed_lines']} poisoned={entry['poisoned']}"
        )
        if entry.get("last_turn_error"):
            print(f"    last_error={entry['last_turn_error']}")
        if entry.get("reported_call_id"):
            print(
                f"    → reported call_id={entry['reported_call_id']} "
                f"call_present={entry['reported_call_present']} "
                f"output_present={entry['reported_output_present']}"
            )
        if entry.get("dangling_calls"):
            print(f"    → additional unpaired call_ids: {entry['dangling_calls'][:8]}")
    if out.get("repaired"):
        print(f"repaired: {out['repaired']}")
        print(f"  original: {out['original_path']}")
        print(f"  repaired: {out['repaired_path']}")
        if out.get("backup_path"):
            print(f"  backup:   {out['backup_path']}")
        print(f"  cut_at_record={out['cut_at_record']} "
              f"kept={out['kept_records']} dropped={out['dropped_records']}")
        print(f"  dangling_removed={out['dangling_removed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
