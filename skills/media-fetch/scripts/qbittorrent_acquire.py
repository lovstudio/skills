#!/usr/bin/env python3
"""Probe ranked Magnet candidates, monitor the winner, and recover from stalls."""

from __future__ import annotations

import argparse
import base64
import http.cookiejar
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MIB = 1024**2
COMPLETE_STATES = {"uploading", "stalledup", "pausedup", "stoppedup", "forcedup"}


class QBitClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        response = self.request(
            "/api/v2/auth/login", {"username": username, "password": password}, raw=True
        )
        if response.strip() not in {"", "Ok."}:
            raise RuntimeError(f"qBittorrent login failed: {response[:120]}")

    def request(
        self, path: str, data: dict[str, Any] | None = None, raw: bool = False
    ) -> Any:
        encoded = urllib.parse.urlencode(data).encode("utf-8") if data is not None else None
        request = urllib.request.Request(self.base_url + path, data=encoded)
        request.add_header("Referer", self.base_url)
        try:
            with self.opener.open(request, timeout=30) as response:
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"qBittorrent HTTP {exc.code} for {path}: {detail[:300]}") from exc
        if raw:
            return text
        return json.loads(text) if text else {}

    def torrents(self) -> list[dict[str, Any]]:
        payload = self.request("/api/v2/torrents/info")
        return payload if isinstance(payload, list) else []

    def add(self, uri: str, save_path: Path, tag: str) -> None:
        self.request(
            "/api/v2/torrents/add",
            {
                "urls": uri,
                "savepath": str(save_path),
                "tags": tag,
                "stopped": "false",
                "paused": "false",
            },
            raw=True,
        )

    def action(self, action: str, hashes: list[str]) -> None:
        if not hashes:
            return
        joined = "|".join(hashes)
        paths = [f"/api/v2/torrents/{action}"]
        if action == "start":
            paths.append("/api/v2/torrents/resume")
        elif action == "stop":
            paths.append("/api/v2/torrents/pause")
        last_error: RuntimeError | None = None
        for path in paths:
            try:
                self.request(path, {"hashes": joined}, raw=True)
                return
            except RuntimeError as exc:
                last_error = exc
        if last_error:
            raise last_error

    def set_location(self, hash_value: str, location: Path) -> None:
        self.request(
            "/api/v2/torrents/setLocation",
            {"hashes": hash_value, "location": str(location)},
            raw=True,
        )

    def delete(self, hash_value: str, delete_files: bool) -> None:
        self.request(
            "/api/v2/torrents/delete",
            {"hashes": hash_value, "deleteFiles": str(delete_files).lower()},
            raw=True,
        )


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_info_hash(uri: str) -> str | None:
    match = re.search(r"(?:[?&]xt=urn:btih:)([A-Za-z0-9]+)", uri, re.I)
    if not match:
        return None
    value = match.group(1)
    if re.fullmatch(r"[0-9A-Fa-f]{40}", value):
        return value.lower()
    if re.fullmatch(r"[A-Z2-7]{32}", value.upper()):
        return base64.b32decode(value.upper()).hex().lower()
    return None


def load_decision(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: cannot read decision JSON {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("ranked"), list):
        raise SystemExit("ERROR: decision document must contain a ranked array")
    return data


def controlled_candidates(
    decision: dict[str, Any], selected_id: str | None, limit: int
) -> list[dict[str, Any]]:
    selected = selected_id or decision.get("selected_id")
    if decision.get("choice_required") and not selected_id:
        reasons = "; ".join(str(value) for value in decision.get("reasons") or [])
        raise SystemExit(f"ERROR: choice_required; provide --selected-id ({reasons})")
    candidates: list[dict[str, Any]] = []
    for row in decision["ranked"]:
        candidate = row.get("candidate") if isinstance(row, dict) else None
        if not isinstance(candidate, dict):
            continue
        uri = str(candidate.get("uri") or "")
        hash_value = str(candidate.get("info_hash") or "").lower() or parse_info_hash(uri)
        if not uri.startswith("magnet:") or not hash_value:
            continue
        item = dict(candidate)
        item["info_hash"] = hash_value
        cap_gib = float(decision.get("max_size_gib") or 0)
        size_bytes = int(item.get("size_bytes") or 0)
        if cap_gib and size_bytes > cap_gib * 1024**3 and item.get("id") != selected:
            continue
        candidates.append(item)
    candidates.sort(key=lambda item: item.get("id") != selected)
    return candidates[: max(1, limit)]


def is_within(path_value: str, parent: Path) -> bool:
    try:
        Path(path_value).expanduser().resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def task_map(client: QBitClient, hashes: set[str]) -> dict[str, dict[str, Any]]:
    return {
        str(task.get("hash", "")).lower(): task
        for task in client.torrents()
        if str(task.get("hash", "")).lower() in hashes
    }


def write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--selected-id")
    parser.add_argument("--output-dir", type=Path, default=Path.home() / "Downloads/Media")
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--job-id")
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--probe-seconds", type=int, default=180)
    parser.add_argument("--warmup-seconds", type=int, default=60)
    parser.add_argument("--probe-budget-mib", type=int, default=512)
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--slow-speed-mib-s", type=float, default=1.0)
    parser.add_argument("--stall-seconds", type=int, default=180)
    parser.add_argument("--wait-complete", action="store_true")
    parser.add_argument("--max-runtime-hours", type=float, default=48.0)
    parser.add_argument("--cleanup-losers", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    decision = load_decision(args.decision)
    candidates = controlled_candidates(decision, args.selected_id, args.parallel)
    if not candidates:
        raise SystemExit("ERROR: no probeable Magnet candidates")
    output_dir = args.output_dir.expanduser().resolve(strict=False)
    job_id = args.job_id or uuid.uuid4().hex[:12]
    tag = f"media-fetch-{job_id}"
    probe_root = output_dir / ".media-fetch-probes" / job_id
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "job_id": job_id,
        "tag": tag,
        "started_at": now(),
        "status": "planned" if args.dry_run else "probing",
        "destination": str(output_dir),
        "probe_root": str(probe_root),
        "candidate_ids": [item.get("id") for item in candidates],
        "events": [],
    }
    if args.dry_run:
        result["selected_id"] = candidates[0].get("id")
        result["planned_hashes"] = [item["info_hash"] for item in candidates]
        write_result(args.result, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    password = os.environ.get("QBITTORRENT_PASSWORD", "")
    if not password:
        raise SystemExit("ERROR: QBITTORRENT_PASSWORD is required")
    client = QBitClient(
        os.environ.get("QBITTORRENT_URL", "http://127.0.0.1:8080"),
        os.environ.get("QBITTORRENT_USERNAME", "admin"),
        password,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    probe_root.mkdir(parents=True, exist_ok=False)
    hashes = {item["info_hash"] for item in candidates}
    preexisting = set(task_map(client, hashes))
    created: list[dict[str, Any]] = []
    for candidate in candidates:
        hash_value = candidate["info_hash"]
        if hash_value in preexisting:
            result["events"].append(
                {"at": now(), "type": "preexisting_skipped", "hash": hash_value, "candidate_id": candidate.get("id")}
            )
            continue
        candidate_dir = probe_root / str(candidate.get("id"))
        candidate_dir.mkdir(parents=True, exist_ok=False)
        client.add(str(candidate["uri"]), candidate_dir, tag)
        created.append(candidate)
        result["events"].append(
            {"at": now(), "type": "added", "hash": hash_value, "candidate_id": candidate.get("id"), "path": str(candidate_dir)}
        )
    if not created:
        result["status"] = "client_error"
        result["error"] = "all candidate hashes already exist; existing tasks were left unchanged"
        write_result(args.result, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 4

    created_hashes = {item["info_hash"] for item in created}
    ready_deadline = time.monotonic() + 60
    while time.monotonic() < ready_deadline:
        if created_hashes.issubset(task_map(client, created_hashes)):
            break
        time.sleep(2)
    metrics: dict[str, dict[str, Any]] = {
        item["info_hash"]: {
            "speeds": [],
            "warm_speeds": [],
            "peak_speed": 0,
            "probe_capped": False,
            "candidate": item,
        }
        for item in created
    }
    probe_started = time.monotonic()
    probe_end = probe_started + max(args.probe_seconds, args.warmup_seconds + 1)
    while time.monotonic() < probe_end:
        current = task_map(client, created_hashes)
        elapsed = time.monotonic() - probe_started
        for hash_value, metric in metrics.items():
            task = current.get(hash_value, {})
            speed = int(task.get("dlspeed") or 0)
            metric["peak_speed"] = max(metric["peak_speed"], speed)
            metric["availability"] = float(task.get("availability") or 0)
            metric["num_seeds"] = int(task.get("num_seeds") or 0)
            metric["progress"] = float(task.get("progress") or 0)
            metric["state"] = str(task.get("state") or "missing")
            downloaded = int(task.get("downloaded") or task.get("total_downloaded") or 0)
            metric["downloaded_bytes"] = downloaded
            if not metric["probe_capped"] and elapsed < args.warmup_seconds:
                metric["warm_speeds"].append(speed)
            elif not metric["probe_capped"]:
                metric["speeds"].append(speed)
            if (
                not metric["probe_capped"]
                and downloaded >= max(1, args.probe_budget_mib) * MIB
            ):
                client.action("stop", [hash_value])
                metric["probe_capped"] = True
        if int(elapsed) % 30 < max(1, args.poll_seconds):
            print(json.dumps({"event": "probe_progress", "elapsed_seconds": int(elapsed), "tasks": {key: {"speed_mib_s": round((value["speeds"][-1] if value["speeds"] else 0) / MIB, 2), "progress": round(float(value.get("progress", 0)) * 100, 2)} for key, value in metrics.items()}}, ensure_ascii=False), flush=True)
        time.sleep(max(1, args.poll_seconds))

    ranked_probe: list[dict[str, Any]] = []
    for hash_value, metric in metrics.items():
        speeds = metric.pop("speeds") or metric.pop("warm_speeds")
        metric.pop("warm_speeds", None)
        metric["average_speed"] = int(statistics.fmean(speeds)) if speeds else 0
        metric["median_speed"] = int(statistics.median(speeds)) if speeds else 0
        metric["hash"] = hash_value
        metric["candidate_id"] = metric["candidate"].get("id")
        ranked_probe.append(metric)
    ranked_probe.sort(
        key=lambda item: (
            item["median_speed"],
            item["average_speed"],
            float(item.get("availability", 0)),
            int(item.get("num_seeds", 0)),
        ),
        reverse=True,
    )
    result["probe_results"] = [
        {key: value for key, value in item.items() if key != "candidate"} for item in ranked_probe
    ]
    threshold = int(max(0.0, args.slow_speed_mib_s) * MIB)
    if not ranked_probe or ranked_probe[0]["median_speed"] < threshold:
        client.action("stop", list(created_hashes))
        result["status"] = "needs_more_sources"
        result["finished_at"] = now()
        write_result(args.result, result)
        print(json.dumps({"status": result["status"], "result": str(args.result)}, ensure_ascii=False, indent=2))
        return 3

    order = [item["hash"] for item in ranked_probe]
    client.action("stop", order)
    active_index = 0
    active_hash = order[active_index]
    client.action("start", [active_hash])
    result["selected_hash"] = active_hash
    result["selected_id"] = metrics[active_hash]["candidate"].get("id")
    result["status"] = "downloading"
    result["events"].append({"at": now(), "type": "winner_started", "hash": active_hash})
    write_result(args.result, result)
    if not args.wait_complete:
        print(json.dumps({"status": "downloading", "selected_id": result["selected_id"], "result": str(args.result)}, ensure_ascii=False, indent=2))
        return 0

    runtime_deadline = time.monotonic() + max(0.1, args.max_runtime_hours) * 3600
    last_progress = 0.0
    last_activity = time.monotonic()
    last_report = 0.0
    winner_task: dict[str, Any] = {}
    while time.monotonic() < runtime_deadline:
        current = task_map(client, created_hashes)
        task = current.get(active_hash, {})
        winner_task = task
        progress = float(task.get("progress") or 0)
        speed = int(task.get("dlspeed") or 0)
        state = str(task.get("state") or "").lower()
        if progress > last_progress + 0.000001 or speed >= threshold:
            last_activity = time.monotonic()
            last_progress = max(last_progress, progress)
        if progress >= 0.999999 or state in COMPLETE_STATES:
            result["status"] = "complete"
            break
        if time.monotonic() - last_activity >= max(30, args.stall_seconds):
            if active_index + 1 >= len(order):
                result["status"] = "needs_more_sources"
                result["events"].append({"at": now(), "type": "all_candidates_stalled", "hash": active_hash})
                client.action("stop", [active_hash])
                break
            client.action("stop", [active_hash])
            previous = active_hash
            active_index += 1
            active_hash = order[active_index]
            client.action("start", [active_hash])
            last_progress = 0.0
            last_activity = time.monotonic()
            result["events"].append({"at": now(), "type": "switched_after_stall", "from": previous, "to": active_hash})
            result["selected_hash"] = active_hash
            result["selected_id"] = metrics[active_hash]["candidate"].get("id")
            write_result(args.result, result)
        if time.monotonic() - last_report >= 60:
            print(json.dumps({"event": "download_progress", "candidate_id": result["selected_id"], "progress_percent": round(progress * 100, 2), "speed_mib_s": round(speed / MIB, 2), "state": state, "eta_seconds": int(task.get("eta") or 0)}, ensure_ascii=False), flush=True)
            last_report = time.monotonic()
        time.sleep(max(1, args.poll_seconds))
    else:
        result["status"] = "runtime_limit"

    if result["status"] == "complete":
        client.set_location(active_hash, output_dir)
        move_deadline = time.monotonic() + 120
        final_path = ""
        while time.monotonic() < move_deadline:
            moved = task_map(client, {active_hash}).get(active_hash, {})
            candidate_path = str(moved.get("content_path") or "")
            if candidate_path and is_within(candidate_path, output_dir) and Path(candidate_path).exists():
                final_path = candidate_path
                break
            time.sleep(2)
        if not final_path:
            result["status"] = "client_error"
            result["error"] = "download completed but final relocation was not confirmed within 120 seconds"
        else:
            result["final_path"] = final_path
            result["completed_at"] = now()
        if args.cleanup_losers:
            for hash_value in order:
                if hash_value == active_hash:
                    continue
                task = task_map(client, {hash_value}).get(hash_value, {})
                safe = is_within(str(task.get("save_path") or ""), probe_root)
                client.delete(hash_value, delete_files=safe)
                result["events"].append({"at": now(), "type": "loser_removed", "hash": hash_value, "files_deleted": safe})
    result["finished_at"] = now()
    write_result(args.result, result)
    print(json.dumps({"status": result["status"], "selected_id": result.get("selected_id"), "result": str(args.result)}, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "complete" else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
