#!/usr/bin/env python3
"""Drive the local Ataru memory index from a headless agent.

The desktop app builds its index through Tauri commands that need a window to
emit progress. Agents and scripts have no window, so this wrapper speaks the
JSON CLI instead: it resolves the `ataru` binary, reports index state, and runs
`ensure_index` to completion before anyone issues a query.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

BIN_ENV = "ATARU_BIN"
# `ataru index status|build` landed in 0.41.3. Older builds silently fall through
# to the desktop entry point and open a window instead of answering, so a
# candidate is only accepted after it reports a new enough version.
MIN_VERSION = (0, 41, 3)
VERSION_PROBE_TIMEOUT = 30.0
CANDIDATE_NAMES = ("ataru", "lovcode")
BUNDLE_PATHS = (
    "/Applications/Ataru.app/Contents/MacOS/ataru",
    "~/Applications/Ataru.app/Contents/MacOS/ataru",
    "/Applications/Lovcode.app/Contents/MacOS/lovcode",
)
REPO_BUILDS = (
    "src-tauri/target/release/ataru",
    "src-tauri/target/debug/ataru",
)
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_NO_BINARY = 3
EXIT_TIMEOUT = 4


class AtaruError(RuntimeError):
    def __init__(self, message: str, code: int = EXIT_FAILED) -> None:
        super().__init__(message)
        self.code = code


def _candidates() -> list[Path]:
    found: list[Path] = []
    for name in CANDIDATE_NAMES:
        located = shutil.which(name)
        if located:
            found.append(Path(located))
    for raw in BUNDLE_PATHS:
        found.append(Path(raw).expanduser())
    for directory in (Path.cwd(), *Path.cwd().parents):
        for relative in REPO_BUILDS:
            found.append(directory / relative)
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in found:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def probe_version(candidate: Path) -> tuple[int, int, int] | None:
    """Read `<bin> --version` and parse the semver triple, or return None."""

    try:
        completed = subprocess.run(
            [str(candidate), "--version"],
            capture_output=True,
            text=True,
            timeout=VERSION_PROBE_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", completed.stdout)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _version_text(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def resolve_binary(explicit: str | None = None) -> Path:
    """Find an Ataru executable that actually implements the index CLI.

    Order: explicit flag, ATARU_BIN, PATH, installed app bundle, local dev
    build discovered by walking up from the current directory. Each candidate is
    version-gated first, because an older binary treats `index status` as a
    desktop launch argument and would open a window instead of replying.
    """

    pinned = explicit or os.environ.get(BIN_ENV, "").strip() or None
    if pinned:
        candidate = Path(pinned).expanduser()
        if not candidate.is_file():
            raise AtaruError(
                f"ATARU_BIN_NOT_FOUND: {candidate} is not a file", EXIT_NO_BINARY
            )
        version = probe_version(candidate)
        if version is None or version < MIN_VERSION:
            raise AtaruError(
                f"ATARU_BIN_TOO_OLD: {candidate} reports "
                f"{_version_text(version) if version else 'no version'}; the index CLI "
                f"needs {_version_text(MIN_VERSION)} or newer.",
                EXIT_NO_BINARY,
            )
        return candidate

    rejected: list[str] = []
    for candidate in _candidates():
        if not candidate.is_file():
            continue
        version = probe_version(candidate)
        if version is None:
            rejected.append(f"{candidate} (no readable version)")
            continue
        if version < MIN_VERSION:
            rejected.append(f"{candidate} ({_version_text(version)})")
            continue
        return candidate

    detail = "; ".join(rejected) if rejected else "no candidate found"
    raise AtaruError(
        "ATARU_BIN_NOT_FOUND: no ataru executable at "
        f"{_version_text(MIN_VERSION)} or newer. Checked: {detail}. "
        f"Set {BIN_ENV} to the binary path.",
        EXIT_NO_BINARY,
    )


def run_json(binary: Path, args: list[str], timeout: float = 300.0) -> dict:
    command = [str(binary), *args, "--json"]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        raise AtaruError(
            f"ATARU_CLI_TIMEOUT: {' '.join(command)} exceeded {timeout}s", EXIT_TIMEOUT
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise AtaruError(
            f"ATARU_CLI_FAILED: {' '.join(command)} exited {completed.returncode}: {detail}"
        )
    payload = completed.stdout.strip()
    if not payload:
        raise AtaruError(f"ATARU_CLI_EMPTY: {' '.join(command)} produced no JSON")
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise AtaruError(f"ATARU_CLI_BAD_JSON: {exc}") from exc


def summarize(status: dict) -> dict:
    """Add the decision an agent actually needs on top of the raw status."""

    state = status.get("state") or "unknown"
    searchable = bool(status.get("searchAvailable"))
    total = status.get("totalMessages") or 0
    done = status.get("processedMessages") or 0
    percent = round(done / total * 100, 1) if total else None
    return {
        "state": state,
        "mode": status.get("mode"),
        "searchAvailable": searchable,
        "needsBuild": state in {"idle", "error", "unknown"} or not searchable,
        "isBuilding": state == "building",
        "progressPercent": percent,
        "indexedMessages": status.get("indexedMessages"),
        "totalMessages": total,
        "totalSessions": status.get("totalSessions"),
        "indexSizeBytes": status.get("indexSizeBytes"),
        "updatedAt": status.get("updatedAt"),
        "error": status.get("error"),
    }


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_status(binary: Path, args: argparse.Namespace) -> int:
    status = run_json(binary, ["index", "status"])
    emit({"binary": str(binary), **summarize(status), "raw": status} if args.raw
         else {"binary": str(binary), **summarize(status)})
    return EXIT_OK


def wait_for_ready(binary: Path, deadline: float, poll: float) -> dict:
    while True:
        status = run_json(binary, ["index", "status"])
        state = status.get("state")
        if state != "building":
            return status
        if time.monotonic() >= deadline:
            raise AtaruError(
                "ATARU_INDEX_WAIT_TIMEOUT: another process is still building the "
                "index. Re-run with a longer --timeout, or let the desktop app finish.",
                EXIT_TIMEOUT,
            )
        time.sleep(poll)


def cmd_ensure(binary: Path, args: argparse.Namespace) -> int:
    deadline = time.monotonic() + args.timeout
    status = run_json(binary, ["index", "status"])
    actions: list[str] = []

    if status.get("state") == "building":
        actions.append("waited-for-running-build")
        status = wait_for_ready(binary, deadline, args.poll)

    view = summarize(status)
    if view["needsBuild"] or args.force:
        actions.append("full-rebuild" if args.force else "catch-up-build")
        remaining = max(deadline - time.monotonic(), 1.0)
        build_args = ["index", "build"] + (["--force"] if args.force else [])
        status = run_json(binary, build_args, timeout=remaining)
        view = summarize(status)
    else:
        actions.append("already-ready")

    view["actions"] = actions
    view["binary"] = str(binary)
    if view["state"] == "error" or not view["searchAvailable"]:
        emit(view)
        return EXIT_FAILED
    emit(view)
    return EXIT_OK


def cmd_semantic_preview(binary: Path, _args: argparse.Namespace) -> int:
    emit(run_json(binary, ["semantic", "preview"]))
    return EXIT_OK


def cmd_resolve_bin(binary: Path, _args: argparse.Namespace) -> int:
    print(str(binary))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin", dest="binary", default=None, help="Path to the ataru executable")
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("resolve-bin", help="Print the resolved ataru executable")
    resolve.set_defaults(handler=cmd_resolve_bin)

    status = sub.add_parser("status", help="Report index state and whether a build is needed")
    status.add_argument("--raw", action="store_true", help="Include the raw CLI status payload")
    status.set_defaults(handler=cmd_status)

    ensure = sub.add_parser("ensure", help="Make the index searchable, building only if needed")
    ensure.add_argument("--force", action="store_true", help="Force a full rebuild")
    ensure.add_argument("--timeout", type=float, default=3600.0, help="Overall budget in seconds")
    ensure.add_argument("--poll", type=float, default=3.0, help="Poll interval while another build runs")
    ensure.set_defaults(handler=cmd_ensure)

    semantic = sub.add_parser(
        "semantic-preview", help="Estimate the cost of initializing the optional semantic index"
    )
    semantic.set_defaults(handler=cmd_semantic_preview)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        binary = resolve_binary(args.binary)
        return args.handler(binary, args)
    except AtaruError as error:
        print(str(error), file=sys.stderr)
        return error.code


if __name__ == "__main__":
    raise SystemExit(main())
