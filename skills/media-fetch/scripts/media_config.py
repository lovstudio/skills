#!/usr/bin/env python3
"""Resolve or initialize portable Media Fetch preferences."""

from __future__ import annotations

import argparse
import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULTS: dict[str, Any] = {
    "output_dir": "$HOME/Downloads/Media",
    "quality_mode": "balanced",
    "max_movie_size_gib": 24.0,
    "max_episode_size_gib": 6.0,
    "reserve_free_gib": 15.0,
    "parallel_probes": 3,
    "probe_seconds": 180,
    "warmup_seconds": 60,
    "probe_budget_mib": 512,
    "slow_speed_mib_s": 1.0,
    "stall_seconds": 180,
    "max_search_waves": 3,
    "preferred_audio": ["original", "zh", "en"],
    "preferred_subtitles": ["zh-Hans", "en"],
    "preferred_editions": [
        "director-cut",
        "extended",
        "uncut",
        "complete",
        "theatrical",
    ],
    "transport_backends": ["qbittorrent", "aria2"],
    "aria2_binary": "aria2c",
    "aria2_listen_port": 53555,
    "aria2_max_peers": 200,
    "aria2_max_restarts": 2,
    "subtitle_repair": "match-exact-release",
    "qbittorrent_url": "http://127.0.0.1:8080",
    "qbittorrent_username": "admin",
}

ENV_MAP = {
    "output_dir": "MEDIA_FETCH_OUTPUT_DIR",
    "max_movie_size_gib": "MEDIA_FETCH_MAX_MOVIE_SIZE_GIB",
    "max_episode_size_gib": "MEDIA_FETCH_MAX_EPISODE_SIZE_GIB",
    "reserve_free_gib": "MEDIA_FETCH_RESERVE_FREE_GIB",
    "parallel_probes": "MEDIA_FETCH_PARALLEL_PROBES",
    "slow_speed_mib_s": "MEDIA_FETCH_SLOW_SPEED_MIB_S",
    "transport_backends": "MEDIA_FETCH_TRANSPORT_BACKENDS",
    "aria2_binary": "MEDIA_FETCH_ARIA2_BIN",
    "aria2_listen_port": "MEDIA_FETCH_ARIA2_LISTEN_PORT",
    "aria2_max_peers": "MEDIA_FETCH_ARIA2_MAX_PEERS",
    "aria2_max_restarts": "MEDIA_FETCH_ARIA2_MAX_RESTARTS",
    "qbittorrent_url": "QBITTORRENT_URL",
    "qbittorrent_username": "QBITTORRENT_USERNAME",
}


def profile_path() -> Path:
    value = os.environ.get(
        "SKILL_PROFILE_PATH", str(Path.home() / ".skill-publisher/skills/profile.json")
    )
    return Path(os.path.expandvars(value)).expanduser()


def load_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: profile root must be an object: {path}")
    return data


def coerce(value: str, template: Any) -> Any:
    if isinstance(template, bool):
        return value.lower() in {"1", "true", "yes", "on"}
    if isinstance(template, int):
        return int(value)
    if isinstance(template, float):
        return float(value)
    if isinstance(template, list):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


def expand_value(key: str, value: Any) -> Any:
    if key.endswith("_dir") and isinstance(value, str):
        return str(Path(os.path.expandvars(value)).expanduser())
    return value


def resolve(profile: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(DEFAULTS)
    saved = profile.get("media_fetch")
    if isinstance(saved, dict):
        result.update({key: value for key, value in saved.items() if key in DEFAULTS})
    for key, env_name in ENV_MAP.items():
        if env_name in os.environ:
            result[key] = coerce(os.environ[env_name], DEFAULTS[key])
    for key, value in overrides.items():
        if value is None:
            continue
        if key in DEFAULTS:
            value = coerce(value, DEFAULTS[key]) if isinstance(value, str) else value
        result[key] = value
    return {key: expand_value(key, value) for key, value in result.items()}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    for name in ("show", "init"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--output-dir")
        cmd.add_argument("--max-movie-size-gib", type=float)
        cmd.add_argument("--max-episode-size-gib", type=float)
        cmd.add_argument("--reserve-free-gib", type=float)
        cmd.add_argument("--parallel-probes", type=int)
        cmd.add_argument("--slow-speed-mib-s", type=float)
        cmd.add_argument("--transport-backends")
        cmd.add_argument("--aria2-binary")
        cmd.add_argument("--aria2-listen-port", type=int)
        cmd.add_argument("--aria2-max-peers", type=int)
        cmd.add_argument("--aria2-max-restarts", type=int)
        cmd.add_argument("--json", action="store_true")
        if name == "init":
            cmd.add_argument("--write", action="store_true")
    return root


def main() -> int:
    args = parser().parse_args()
    path = profile_path()
    profile = load_profile(path)
    overrides = {
        "output_dir": args.output_dir,
        "max_movie_size_gib": args.max_movie_size_gib,
        "max_episode_size_gib": args.max_episode_size_gib,
        "reserve_free_gib": args.reserve_free_gib,
        "parallel_probes": args.parallel_probes,
        "slow_speed_mib_s": args.slow_speed_mib_s,
        "transport_backends": args.transport_backends,
        "aria2_binary": args.aria2_binary,
        "aria2_listen_port": args.aria2_listen_port,
        "aria2_max_peers": args.aria2_max_peers,
        "aria2_max_restarts": args.aria2_max_restarts,
    }
    resolved = resolve(profile, overrides)

    wrote = False
    if args.command == "init" and args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        profile["media_fetch"] = resolved
        path.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        wrote = True

    payload = {"profile_path": str(path), "resolved": resolved, "written": wrote}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"profile={path}")
        print(f"written={'yes' if wrote else 'no'}")
        for key, value in resolved.items():
            print(f"{key}={json.dumps(value, ensure_ascii=False)}")
        if args.command == "init" and not args.write:
            print("next=review these values, then rerun with --write")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
