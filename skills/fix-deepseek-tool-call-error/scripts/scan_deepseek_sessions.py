#!/usr/bin/env python3
"""Scan Codex rollout JSONL files for the DeepSeek "No tool output found" syndrome.

The scanner is read-only. It reports, per incident:

* session, thread, time, turn and the call id DeepSeek rejected;
* the name of the rejected call and the batch it was issued with;
* whether the batch contained a view_image call and whether Codex inserted an
  <image_resize_notice> developer message in that thread;
* how many later turns in the same thread failed with the same call id, which is
  the signature of a wedged thread.

Usage:
    python3 scripts/scan_deepseek_sessions.py
    python3 scripts/scan_deepseek_sessions.py --file <rollout.jsonl> --json
    python3 scripts/scan_deepseek_sessions.py --root ~/.codex/archived_sessions
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ERROR_RE = re.compile(r"No tool output found for tool call (call_[A-Za-z0-9_]+)")
DEFAULT_ROOTS = (
    os.path.expanduser("~/.codex/sessions"),
    os.path.expanduser("~/.codex/archived_sessions"),
)

# Cheap pre-filter: rollout files reach tens of megabytes, and only a few line
# shapes matter. Skipping the rest avoids parsing the whole transcript.
KEEP_MARKERS = ("session_meta", "function_call", "image_resize_notice", "task_complete")


def iter_rollouts(roots):
    for root in roots:
        root = os.path.expanduser(root)
        for path in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)):
            yield path


def load_items(path):
    items = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            if not any(marker in line for marker in KEEP_MARKERS):
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def scan_file(path):
    items = load_items(path)
    meta = {"session_id": os.path.basename(path).split("-")[-1].split(".")[0], "cwd": "", "model": "", "provider": ""}
    calls = {}
    outputs = set()
    notices = []
    failures = []

    for index, obj in enumerate(items):
        kind = obj.get("type")
        payload = obj.get("payload") or {}
        if kind == "session_meta":
            meta = {
                "session_id": payload.get("id") or meta["session_id"],
                "cwd": payload.get("cwd") or "",
                "model": payload.get("model") or "",
                "provider": payload.get("model_provider") or "",
            }
        elif kind == "response_item":
            item_type = payload.get("type")
            if item_type == "function_call":
                call_id = payload.get("call_id") or payload.get("id")
                calls[call_id] = {
                    "call_id": call_id,
                    "name": payload.get("name") or "",
                    "index": index,
                    "ts": obj.get("timestamp"),
                    "arguments": (payload.get("arguments") or "")[:160],
                }
            elif item_type in ("function_call_output", "custom_tool_call_output"):
                outputs.add(payload.get("call_id"))
            elif item_type == "message":
                blob = json.dumps(payload.get("content"), ensure_ascii=False)
                if "image_resize_notice" in blob:
                    notices.append({"index": index, "ts": obj.get("timestamp")})
        elif kind == "event_msg" and payload.get("type") == "task_complete":
            message = ((payload.get("error") or {}).get("message")) or ""
            match = ERROR_RE.search(message)
            if match:
                failures.append(
                    {
                        "call_id": match.group(1),
                        "turn_id": payload.get("turn_id"),
                        "ts": obj.get("timestamp"),
                        "duration_ms": payload.get("duration_ms"),
                        "index": index,
                    }
                )

    incidents = []
    for failure in failures:
        victim = calls.get(failure["call_id"], {})
        window = [call for call in calls.values() if failure["index"] - 8 <= call["index"] <= failure["index"] + 2]
        window.sort(key=lambda call: call["index"])
        batch = [
            {
                "call_id": call["call_id"],
                "name": call["name"],
                "has_output": call["call_id"] in outputs,
                "issued_before_victim": call["index"] <= victim.get("index", failure["index"]),
            }
            for call in window
        ]
        names = sorted({call["name"] for call in window if call["name"]})
        has_image = any(name == "view_image" for name in names)
        resize_seen = bool(notices)
        incidents.append(
            {
                "session_id": meta["session_id"],
                "cwd": meta["cwd"],
                "model": meta["model"],
                "provider": meta["provider"],
                "ts": failure["ts"],
                "turn_id": failure["turn_id"],
                "duration_ms": failure["duration_ms"],
                "victim_call_id": failure["call_id"],
                "victim_name": victim.get("name") or "unknown",
                "victim_arguments": victim.get("arguments") or "",
                "batch": batch,
                "batch_call_names": names,
                "batch_size": len(window),
                "contains_view_image": has_image,
                "resize_notice_in_thread": resize_seen,
                "variant": classify(has_image, resize_seen, names),
                "repeat_failures_same_call": sum(1 for f in failures if f["call_id"] == failure["call_id"]),
                "failure_count_in_thread": len(failures),
                "file": str(path),
            }
        )
    return meta, incidents


def classify(has_image, resize_seen, names):
    if has_image and resize_seen:
        return "image_batch_with_resize_notice"
    if has_image:
        return "image_batch_without_resize_notice"
    if len(names) > 1:
        return "non_image_batch"
    return "single_call_or_hook_message"


def format_rows(incidents):
    rows = []
    for incident in incidents:
        rows.append(
            " | ".join(
                [
                    (incident["ts"] or "")[5:19],
                    incident["session_id"][:8],
                    incident["victim_name"],
                    ",".join(incident["batch_call_names"]) or "-",
                    incident["variant"],
                    f"x{incident['repeat_failures_same_call']}",
                ]
            )
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", action="append", default=[], help="session root to scan (repeatable)")
    parser.add_argument("--file", action="append", default=[], help="rollout JSONL to scan (repeatable)")
    parser.add_argument("--json", action="store_true", help="print full JSON instead of a table")
    parser.add_argument("--all", action="store_true", help="include incidents from every rollout, not just sessions with a text match")
    args = parser.parse_args()

    paths = list(args.file) or list(iter_rollouts(args.root or DEFAULT_ROOTS))
    all_incidents = []
    for path in paths:
        try:
            _, incidents = scan_file(path)
        except OSError as error:
            print(f"skip {path}: {error}", file=sys.stderr)
            continue
        all_incidents.extend(incidents)

    all_incidents.sort(key=lambda incident: incident["ts"] or "")
    wedged = sorted({incident["session_id"] for incident in all_incidents if incident["repeat_failures_same_call"] > 1})

    if args.json:
        print(json.dumps({"incidents": all_incidents, "wedged_sessions": wedged}, ensure_ascii=False, indent=2))
        return 0

    if not all_incidents:
        print("no 'No tool output found' incidents found in the scanned rollouts")
        return 0

    print("time | session | victim | batch | variant | repeats")
    for row in format_rows(all_incidents):
        print(row)
    print()
    print(f"incidents={len(all_incidents)} sessions={len({i['session_id'] for i in all_incidents})} wedged={len(wedged)}")
    if wedged:
        print("wedged sessions: " + ", ".join(wedged))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
