#!/usr/bin/env python3
"""Run a resumable aria2 transfer for a direct URL, Magnet, or Torrent input."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VIDEO_SUFFIXES = {".mkv", ".mp4", ".m4v", ".mov", ".ts", ".m2ts", ".webm", ".avi"}
DEFAULT_TRACKERS = (
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.cyberia.is:6969/announce",
    "udp://tracker.moeking.me:6969/announce",
    "udp://tracker1.bt.moack.co.kr:80/announce",
    "udp://tracker.tiny-vps.com:6969/announce",
    "http://tracker.openbittorrent.com:80/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://tracker.publictracker.xyz:6969/announce",
    "udp://tracker.dler.org:6969/announce",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def media_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for item in root.rglob("*"):
        if not item.is_file() or item.suffix.lower() not in VIDEO_SUFFIXES:
            continue
        try:
            item.stat()
        except FileNotFoundError:
            continue
        files.append(item)
    return sorted(files, key=lambda item: item.stat().st_size, reverse=True)


def control_files(root: Path) -> list[Path]:
    return sorted(item for item in root.rglob("*.aria2") if item.is_file())


def without_proxy(environment: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in environment.items() if "proxy" not in key.lower()}


def load_trackers(args: argparse.Namespace) -> list[str]:
    values = list(DEFAULT_TRACKERS)
    for tracker_file in args.tracker_file:
        path = Path(tracker_file).expanduser()
        values.extend(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    values.extend(args.tracker)
    return list(dict.fromkeys(values))


def resolve_binary(value: str | None) -> str:
    candidate = value or os.environ.get("MEDIA_FETCH_ARIA2_BIN") or "aria2c"
    expanded = str(Path(candidate).expanduser())
    resolved = shutil.which(expanded) or (expanded if Path(expanded).is_file() else None)
    if not resolved:
        raise SystemExit("ERROR: aria2c is required for the primary transfer backend")
    return resolved


def classify_input(value: str) -> str:
    lowered = value.lower()
    if lowered.startswith("magnet:"):
        return "bittorrent"
    parsed = urlparse(value)
    path = parsed.path if parsed.scheme else value
    if path.lower().endswith(".torrent"):
        return "bittorrent"
    return "direct"


def validate_output_name(value: str | None) -> str | None:
    if value is None:
        return None
    name = value.strip()
    if not name or Path(name).name != name or name in {".", ".."}:
        raise SystemExit("ERROR: --output-name must be a plain file name")
    return name


def port_is_available(port: int, *, udp: bool) -> bool:
    socket_type = socket.SOCK_DGRAM if udp else socket.SOCK_STREAM
    with socket.socket(socket.AF_INET, socket_type) as handle:
        try:
            handle.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def find_port(seed: int, *, require_udp: bool, excluded: set[int]) -> int:
    for offset in range(20000):
        port = 40000 + ((seed - 40000 + offset) % 20000)
        if port in excluded:
            continue
        if port_is_available(port, udp=False) and (
            not require_udp or port_is_available(port, udp=True)
        ):
            return port
    raise SystemExit("ERROR: no available local port found for aria2")


def resolve_ports(
    job_id: str,
    input_kind: str,
    requested_listen: int,
    requested_rpc: int | None,
) -> tuple[int | None, int]:
    seed = 40000 + int(hashlib.sha1(job_id.encode("utf-8")).hexdigest()[:8], 16) % 20000
    listen_port: int | None = None
    if input_kind == "bittorrent":
        if requested_listen > 0:
            listen_port = requested_listen
        else:
            listen_port = find_port(seed, require_udp=True, excluded=set())
    if requested_rpc and requested_rpc > 0:
        rpc_port = requested_rpc
    else:
        rpc_port = find_port(
            seed + 1,
            require_udp=False,
            excluded={listen_port} if listen_port else set(),
        )
    return listen_port, rpc_port


def build_command(
    args: argparse.Namespace,
    probe_root: Path,
    binary: str,
    trackers: list[str],
    input_kind: str,
    listen_port: int | None,
    rpc_port: int,
) -> list[str]:
    command = [
        binary,
        f"--dir={probe_root}",
        "--file-allocation=none",
        "--continue=true",
        "--enable-rpc=true",
        "--rpc-listen-all=false",
        f"--rpc-listen-port={rpc_port}",
        "--max-connection-per-server=16",
        "--split=16",
        "--min-split-size=1M",
        "--max-tries=0",
        "--retry-wait=2",
        "--connect-timeout=15",
        "--timeout=60",
        f"--summary-interval={args.summary_interval}",
        "--console-log-level=notice",
        "--auto-file-renaming=false",
    ]
    if args.output_name:
        command.append(f"--out={args.output_name}")
    if input_kind == "bittorrent":
        if listen_port is None:
            raise ValueError("BitTorrent input requires a listen port")
        command.extend(
            [
                "--seed-time=0",
                "--enable-dht=true",
                "--bt-enable-lpd=true",
                "--enable-peer-exchange=true",
                f"--dht-listen-port={listen_port}",
                f"--listen-port={listen_port}",
                "--bt-tracker-connect-timeout=15",
                "--bt-tracker-interval=30",
                f"--bt-max-peers={args.max_peers}",
                "--bt-request-peer-speed-limit=1M",
                f"--bt-tracker={','.join(trackers)}",
            ]
        )
    command.append(args.input)
    return command


def rpc_request(rpc_port: int, method: str, params: list[Any]) -> Any:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "media-fetch",
            "method": method,
            "params": params,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{rpc_port}/jsonrpc",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            document = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return document.get("result") if isinstance(document, dict) else None


def rpc_transfer(rpc_port: int) -> dict[str, Any] | None:
    keys = ["status", "completedLength", "totalLength", "downloadSpeed"]
    tasks = rpc_request(rpc_port, "aria2.tellActive", [keys])
    source = "active"
    if not isinstance(tasks, list) or not tasks:
        tasks = rpc_request(rpc_port, "aria2.tellStopped", [0, 10, keys])
        source = "stopped"
    if not isinstance(tasks, list) or not tasks:
        return None
    statuses = [str(item.get("status") or "") for item in tasks]
    return {
        "completed_bytes": sum(int(item.get("completedLength") or 0) for item in tasks),
        "total_bytes": sum(int(item.get("totalLength") or 0) for item in tasks),
        "download_speed_bytes_per_second": sum(
            int(item.get("downloadSpeed") or 0) for item in tasks
        ),
        "rpc_source": source,
        "rpc_statuses": statuses,
        "rpc_complete": source == "stopped" and all(status == "complete" for status in statuses),
    }


def snapshot(probe_root: Path) -> dict[str, Any]:
    files = media_files(probe_root)
    stats = [item.stat() for item in files]
    return {
        "media_files": len(files),
        "media_bytes_logical": sum(info.st_size for info in stats),
        "media_bytes_allocated": sum(
            info.st_size
            if getattr(info, "st_blocks", None) is None
            else int(info.st_blocks) * 512
            for info in stats
        ),
        "control_files": [str(item.relative_to(probe_root)) for item in control_files(probe_root)],
    }


def write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        help="HTTP(S) URL, Magnet URI, local .torrent, or .torrent URL",
    )
    parser.add_argument(
        "--output-name",
        help="Plain output file name for a direct URL whose path has no useful media suffix",
    )
    parser.add_argument("--output-dir", type=Path, default=Path.home() / "Downloads/Media")
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--aria2-bin")
    parser.add_argument(
        "--listen-port",
        type=int,
        default=0,
        help="BitTorrent listen port; 0 selects a job-specific available port",
    )
    parser.add_argument("--rpc-listen-port", type=int)
    parser.add_argument("--max-peers", type=int, default=200)
    parser.add_argument("--summary-interval", type=int, default=15)
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--stall-seconds", type=int, default=180)
    parser.add_argument("--slow-speed-mib-s", type=float, default=1.0)
    parser.add_argument("--max-runtime-hours", type=float, default=48.0)
    parser.add_argument("--max-restarts", type=int, default=2)
    parser.add_argument("--restart-delay-seconds", type=int, default=15)
    parser.add_argument("--tracker", action="append", default=[])
    parser.add_argument("--tracker-file", action="append", default=[])
    parser.add_argument("--no-proxy", action="store_true")
    parser.add_argument("--watch", action="store_true", help="Restart a stalled aria2 process while its .aria2 state remains")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.output_name = validate_output_name(args.output_name)

    output_dir = args.output_dir.expanduser().resolve(strict=False)
    job_id = "".join(
        character if character.isalnum() or character in "-_." else "_"
        for character in args.job_id
    ).strip("._") or "media-job"
    probe_root = output_dir / ".media-fetch-probes" / job_id
    probe_root.mkdir(parents=True, exist_ok=True)
    log_path = probe_root / "aria2.log"
    binary = resolve_binary(args.aria2_bin)
    trackers = load_trackers(args)
    input_kind = classify_input(args.input)
    listen_port, rpc_port = resolve_ports(
        job_id,
        input_kind,
        args.listen_port,
        args.rpc_listen_port,
    )
    command = build_command(
        args,
        probe_root,
        binary,
        trackers,
        input_kind,
        listen_port,
        rpc_port,
    )
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "job_id": job_id,
        "backend": "aria2",
        "input_kind": input_kind,
        "input": args.input,
        "destination": str(output_dir),
        "probe_root": str(probe_root),
        "log_path": str(log_path),
        "started_at": now(),
        "status": "planned" if args.dry_run else "running",
        "trackers_count": len(trackers) if input_kind == "bittorrent" else 0,
        "listen_port": listen_port,
        "rpc_port": rpc_port,
        "events": [],
    }
    if args.dry_run:
        result["command"] = command
        result["environment_mode"] = "direct" if args.no_proxy else "inherited"
        result["download_status"] = result["status"]
        write_result(args.result, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    environment = without_proxy(dict(os.environ)) if args.no_proxy else dict(os.environ)
    deadline = time.monotonic() + max(0.1, args.max_runtime_hours) * 3600
    restarts = 0
    process: subprocess.Popen[Any] | None = None

    try:
        while time.monotonic() < deadline:
            stalled = False
            stall_reason = ""
            completed_via_rpc = False
            started_monotonic = time.monotonic()
            last_progress_monotonic = started_monotonic
            last_completed_bytes = 0
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"\n[{now()}] starting aria2: {' '.join(command)}\n")
                log.flush()
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=environment,
                )
                result["events"].append({"at": now(), "type": "backend_started", "pid": process.pid})
                write_result(args.result, result)
                while process.poll() is None and time.monotonic() < deadline:
                    state = snapshot(probe_root)
                    sample_monotonic = time.monotonic()
                    transfer = rpc_transfer(rpc_port) or {
                        "completed_bytes": last_completed_bytes,
                        "total_bytes": 0,
                        "download_speed_bytes_per_second": 0,
                        "rpc_source": "unavailable",
                        "rpc_statuses": [],
                        "rpc_complete": False,
                    }
                    completed_bytes = int(transfer["completed_bytes"])
                    delta_bytes = max(0, completed_bytes - last_completed_bytes)
                    observed_speed = int(transfer["download_speed_bytes_per_second"])
                    if delta_bytes > 0:
                        last_progress_monotonic = sample_monotonic
                        last_completed_bytes = completed_bytes
                    print(
                        json.dumps(
                            {
                                "event": "aria2_progress",
                                "elapsed_seconds": int(max(0, sample_monotonic - started_monotonic)),
                                "completed_bytes": completed_bytes,
                                "total_bytes": int(transfer["total_bytes"]),
                                "observed_speed_bytes_per_second": observed_speed,
                                "rpc_source": transfer["rpc_source"],
                                "rpc_statuses": transfer["rpc_statuses"],
                                **state,
                            },
                        ensure_ascii=False,
                        ),
                        flush=True,
                    )
                    has_payload = state["media_files"] > 0
                    if (
                        bool(transfer["rpc_complete"])
                        and has_payload
                        and not state["control_files"]
                    ):
                        completed_via_rpc = True
                        result["events"].append(
                            {
                                "at": now(),
                                "type": "backend_completed",
                                "completed_bytes": completed_bytes,
                            }
                        )
                        process.send_signal(signal.SIGTERM)
                        process.wait(timeout=30)
                        break
                    stalled_for = sample_monotonic - last_progress_monotonic
                    if (
                        args.watch
                        and has_payload
                        and stalled_for >= max(1, args.stall_seconds)
                        and observed_speed < max(0.0, args.slow_speed_mib_s) * 1024 * 1024
                    ):
                        stalled = True
                        stall_reason = (
                            f"no payload growth for {int(stalled_for)}s; "
                            f"observed speed {observed_speed} B/s"
                        )
                        result["events"].append(
                            {"at": now(), "type": "backend_stalled", "reason": stall_reason}
                        )
                        write_result(args.result, result)
                        process.send_signal(signal.SIGTERM)
                        process.wait(timeout=30)
                        break
                    time.sleep(max(1, args.poll_seconds))
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=30)
                result["status"] = "runtime_limit"
                break
            if completed_via_rpc:
                result["status"] = "complete"
                result["completed_at"] = now()
                result["last_snapshot"] = snapshot(probe_root)
                break
            if stalled:
                state = snapshot(probe_root)
                if restarts >= max(0, args.max_restarts):
                    result["status"] = "needs_more_sources"
                    result["last_snapshot"] = state
                    break
                restarts += 1
                result["events"].append(
                    {
                        "at": now(),
                        "type": "backend_restarted",
                        "restart": restarts,
                        "reason": stall_reason,
                    }
                )
                write_result(args.result, result)
                time.sleep(max(1, args.restart_delay_seconds))
                continue
            return_code = int(process.returncode or 0)
            state = snapshot(probe_root)
            result["last_exit_code"] = return_code
            result["last_snapshot"] = state
            if return_code == 0 and state["media_files"] > 0 and not state["control_files"]:
                result["status"] = "complete"
                result["completed_at"] = now()
                break
            if not args.watch or restarts >= max(0, args.max_restarts):
                result["status"] = "needs_more_sources" if state["control_files"] else "client_error"
                break
            restarts += 1
            result["events"].append({"at": now(), "type": "backend_restarted", "restart": restarts, "exit_code": return_code})
            write_result(args.result, result)
            time.sleep(max(1, args.restart_delay_seconds))
    except KeyboardInterrupt:
        if process and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=30)
        result["status"] = "cancelled"
    finally:
        result["finished_at"] = now()
        result["restarts"] = restarts
        result["final_snapshot"] = snapshot(probe_root)
        result["download_status"] = result["status"]
        write_result(args.result, result)

    print(json.dumps({"status": result["status"], "result": str(args.result)}, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "complete" else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
