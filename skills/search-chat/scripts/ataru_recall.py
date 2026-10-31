#!/usr/bin/env python3
"""Recall past AI-agent context from the local Ataru memory index.

Wraps the `ataru` JSON CLI so an agent gets two things it can act on: ranked
hits carrying stable Project/Session/Turn identifiers, and a bounded read of the
original transcript around one of those hits. The raw CLI response is deliberate
about detail and can run to megabytes, so every command here returns a compact
projection and truncates message bodies unless asked not to.
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
MANIFEST_NAME = "search-index-manifest.json"
NS_PER_SECOND = 1_000_000_000
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


def data_local_dir() -> Path:
    """Mirror `dirs::data_local_dir()`, under which Ataru keeps its index."""

    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
    xdg = os.environ.get("XDG_DATA_HOME", "")
    return Path(xdg) if os.path.isabs(xdg) else home / ".local" / "share"


def _codex_rollouts(root: str) -> list[str]:
    try:
        entries = list(os.scandir(root))
    except OSError:
        return []
    found: list[str] = []
    for entry in entries:
        if entry.is_dir():
            found.extend(_codex_rollouts(entry.path))
        elif Path(entry.name).suffix == ".jsonl":
            found.append(entry.path)
    return found


def collect_sources(home: Path) -> list[tuple[str, str, str, int, int]]:
    """List (path, kind, session id, size, mtime) for every file Ataru indexes.

    Mirrors Ataru 0.41.x: top-level `*.jsonl` in each Claude project except
    `agent-*` sidechains, and every `*.jsonl` under the Codex session roots.
    Compressed `.jsonl.zst` rollouts stay out because this line cannot read them.
    """

    sources = []
    projects = home / ".claude" / "projects"
    if projects.exists():
        for project in os.scandir(projects):
            if not project.is_dir():
                continue
            for entry in os.scandir(project.path):
                if not entry.name.endswith(".jsonl") or entry.name.startswith("agent-"):
                    continue
                stat = entry.stat(follow_symlinks=False)
                session_id = entry.name[: -len(".jsonl")]
                mtime = stat.st_mtime_ns // NS_PER_SECOND
                sources.append((entry.path, "claude", session_id, stat.st_size, mtime))
    for root in ("sessions", "archived_sessions"):
        for path in _codex_rollouts(str(home / ".codex" / root)):
            try:
                stat = os.stat(path)
            except OSError:
                continue
            stem = Path(path).stem
            tail = stem[-36:]
            session_id = tail if len(stem) >= 36 and tail.count("-") == 4 else stem
            mtime = stat.st_mtime_ns // NS_PER_SECOND
            sources.append((path, "codex", session_id, stat.st_size, mtime))
    return sources


def index_drift() -> dict:
    """Count the sessions a non-forced `index build` would still have to touch.

    `index status` only echoes the totals stored in the manifest, so an index
    that stopped updating months ago still reports `ready`. Each source file is
    checked against its manifest entry with Ataru's own
    `previous_entry_matches_source` rule: same kind, session id, size and mtime,
    and indexed to the end.
    """

    try:
        manifest = json.loads(
            (data_local_dir() / "ataru" / MANIFEST_NAME).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        manifest = {}
    indexed_at = manifest.get("indexedAt")
    entries = {entry.get("path"): entry for entry in manifest.get("entries") or []}
    try:
        sources = collect_sources(Path.home())
    except OSError as exc:
        raise AtaruError(f"ATARU_SOURCES_UNREADABLE: {exc}") from exc

    pending = 0
    for path, kind, session_id, size, mtime in sources:
        entry = entries.get(path)
        if entry is None:
            # Ataru stores no entry for a Codex rollout it cannot tie to a project
            # and retries it on every build. One no newer than the manifest was
            # already seen and skipped; counting it would keep the index stale forever.
            if not (kind == "codex" and indexed_at is not None and mtime <= indexed_at):
                pending += 1
        elif (
            entry.get("sourceKind"), entry.get("sessionId"), entry.get("size"),
            entry.get("mtime"), entry.get("indexedSize"),
        ) != (kind, session_id, size, mtime, size):
            pending += 1
    current = {source[0] for source in sources}
    removed = sum(1 for path in entries if path not in current)
    return {
        "indexStale": bool(pending or removed),
        "pendingSessions": pending,
        "removedSessions": removed,
        "indexedAt": indexed_at,
    }


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


LEVELS = ("turn", "run", "session", "project")
DEFAULT_SNIPPET_CHARS = 600
DEFAULT_MESSAGE_CHARS = 2000


def clip(value: object, limit: int) -> object:
    if not isinstance(value, str) or limit <= 0 or len(value) <= limit:
        return value
    return value[:limit] + f"… [+{len(value) - limit} chars]"


def require_ready_index(binary: Path) -> dict:
    """Never let a missing index look like an empty result set."""

    status = run_json(binary, ["index", "status"], timeout=120.0)
    state = status.get("state")
    if state == "building":
        raise AtaruError(
            "ATARU_INDEX_BUILDING: the memory index is still being built "
            f"({status.get('processedMessages')}/{status.get('totalMessages')} messages). "
            "Wait for it to finish, or run the lov-ataru-indexing skill to track it."
        )
    if not status.get("searchAvailable"):
        raise AtaruError(
            f"ATARU_INDEX_NOT_READY: index state is '{state}'. Run the "
            "lov-ataru-indexing skill (`ataru_index.py ensure`) before searching. "
            f"Reported error: {status.get('error') or 'none'}"
        )
    return status


def stale_warning(drift: dict) -> str | None:
    """Say why a miss on a drifted index is not proof that nothing was found."""

    if not drift["indexStale"]:
        return None
    built_at = drift["indexedAt"]
    built = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(built_at)) if built_at else "never"
    return (
        f"ATARU_INDEX_STALE: since the index was built ({built}), "
        f"{drift['pendingSessions']} session files are new or changed and "
        f"{drift['removedSessions']} indexed sessions are gone from disk. Hits may be "
        "missing or unreadable; run lov-ataru-indexing (`ataru_index.py ensure`) "
        "before reporting a miss as not found."
    )


def project_hit(hit: dict, snippet_chars: int) -> dict:
    return {
        "id": hit.get("id"),
        "level": hit.get("level"),
        "score": hit.get("score"),
        "matchCount": hit.get("matchCount"),
        "title": hit.get("title") or hit.get("sessionTitle"),
        "role": hit.get("role"),
        "timestamp": hit.get("timestamp"),
        "snippet": clip(hit.get("snippet"), snippet_chars),
        "projectId": hit.get("projectId"),
        "projectPath": hit.get("projectPath"),
        "sessionId": hit.get("sessionId"),
        "messageId": hit.get("messageId"),
        "lineNumber": hit.get("lineNumber"),
        "runIndex": hit.get("runIndex"),
        "sessionCount": hit.get("sessionCount"),
    }


def cmd_search(binary: Path, args: argparse.Namespace) -> int:
    require_ready_index(binary)
    drift = index_drift()
    cli_args = ["search", args.query, "--level", args.level, "--limit", str(args.limit)]
    if args.project_id:
        cli_args += ["--project-id", args.project_id]
    response = run_json(binary, cli_args, timeout=args.timeout)

    warning = stale_warning(drift)
    warnings = ([warning] if warning else []) + (response.get("warnings") or [])
    freshness = {
        # The CLI status `updatedAt` is the moment it was read, so the manifest
        # time is the only honest "last built" stamp.
        "indexUpdatedAt": drift["indexedAt"],
        "indexStale": drift["indexStale"],
        "pendingSessions": drift["pendingSessions"],
        "removedSessions": drift["removedSessions"],
    }
    if args.full:
        emit({**response, **freshness, "warnings": warnings})
        return EXIT_OK

    hits = response.get("hits") or []
    emit(
        {
            "query": response.get("query"),
            "level": response.get("level"),
            "mode": response.get("mode"),
            "requestedMode": response.get("requestedMode"),
            "semanticAvailable": response.get("semanticAvailable"),
            "tookMs": response.get("tookMs"),
            "total": response.get("total"),
            "warnings": warnings,
            **freshness,
            "hits": [project_hit(hit, args.snippet_chars) for hit in hits],
        }
    )
    return EXIT_OK


def slice_messages(messages: list[dict], around: str | None, window: int) -> list[dict]:
    if not around:
        return messages if window <= 0 else messages[-window:]
    # `session read` emits Ataru's message struct as-is (`line_number`), unlike the
    # camelCase search hits; both count the same transcript lines.
    pivot = next(
        (
            position
            for position, message in enumerate(messages)
            if message.get("uuid") == around or str(message.get("line_number")) == around
        ),
        None,
    )
    if pivot is None:
        raise AtaruError(
            f"ATARU_MESSAGE_NOT_FOUND: no message with uuid or lineNumber '{around}' "
            "in this session. Use the messageId or lineNumber returned by search."
        )
    if window <= 0:
        return messages[pivot : pivot + 1]
    start = max(pivot - window, 0)
    return messages[start : pivot + window + 1]


def cmd_read(binary: Path, args: argparse.Namespace) -> int:
    messages = run_json(
        binary,
        [
            "session",
            "read",
            "--project-id",
            args.project_id,
            "--session-id",
            args.session_id,
        ],
        timeout=args.timeout,
    )
    if not isinstance(messages, list):
        raise AtaruError("ATARU_CLI_BAD_JSON: session read did not return a message list")

    selected = slice_messages(messages, args.around, args.window)
    emit(
        {
            "projectId": args.project_id,
            "sessionId": args.session_id,
            "totalMessages": len(messages),
            "returnedMessages": len(selected),
            "around": args.around,
            "window": args.window,
            "messages": [
                {
                    "uuid": message.get("uuid"),
                    "lineNumber": message.get("line_number"),
                    "role": message.get("role"),
                    "timestamp": message.get("timestamp"),
                    "content": clip(message.get("content"), args.message_chars),
                }
                for message in selected
            ],
        }
    )
    return EXIT_OK


def cmd_index_status(binary: Path, _args: argparse.Namespace) -> int:
    emit({**run_json(binary, ["index", "status"], timeout=120.0), **index_drift()})
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin", dest="binary", default=None, help="Path to the ataru executable")
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("resolve-bin", help="Print the resolved ataru executable")
    resolve.set_defaults(handler=cmd_resolve_bin)

    status = sub.add_parser("index-status", help="Report index readiness before searching")
    status.set_defaults(handler=cmd_index_status)

    search = sub.add_parser("search", help="Rank past context and return stable identifiers")
    search.add_argument("query")
    search.add_argument("--level", choices=LEVELS, default="turn")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--project-id", default=None, help="Restrict recall to one project id")
    search.add_argument("--snippet-chars", type=int, default=DEFAULT_SNIPPET_CHARS)
    search.add_argument("--timeout", type=float, default=180.0)
    search.add_argument("--full", action="store_true", help="Emit the raw CLI response")
    search.set_defaults(handler=cmd_search)

    read = sub.add_parser("read", help="Read the original transcript around a hit")
    read.add_argument("--project-id", required=True)
    read.add_argument("--session-id", required=True)
    read.add_argument("--around", default=None, help="messageId or lineNumber from a hit")
    read.add_argument("--window", type=int, default=6, help="Messages to keep on each side")
    read.add_argument("--message-chars", type=int, default=DEFAULT_MESSAGE_CHARS)
    read.add_argument("--timeout", type=float, default=300.0)
    read.set_defaults(handler=cmd_read)
    return parser


def cmd_resolve_bin(binary: Path, _args: argparse.Namespace) -> int:
    print(str(binary))
    return EXIT_OK


# Ataru project ids are path slugs and start with "-" (e.g. "-Users-me-code-app").
# argparse would read that as another option, so space-separated values for these
# flags are rewritten into the "--flag=value" form before parsing.
VALUE_FLAGS = ("--project-id", "--session-id", "--around", "--bin")


def normalize_argv(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in VALUE_FLAGS and index + 1 < len(argv):
            normalized.append(f"{token}={argv[index + 1]}")
            index += 2
            continue
        normalized.append(token)
        index += 1
    return normalized


def main() -> int:
    args = build_parser().parse_args(normalize_argv(sys.argv[1:]))
    try:
        binary = resolve_binary(args.binary)
        return args.handler(binary, args)
    except AtaruError as error:
        print(str(error), file=sys.stderr)
        return error.code


if __name__ == "__main__":
    raise SystemExit(main())
