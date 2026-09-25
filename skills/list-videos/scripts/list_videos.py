#!/usr/bin/env python3
"""List every video file under one or more roots with an incremental cache.

The scanner keeps one JSON cache keyed by absolute directory path. A directory
whose mtime has not changed is reused without listing it again, so repeated
runs cost roughly one ``stat`` per directory plus one ``stat`` per cached video
instead of a full walk. The cache lives next to the shared user Profile
(``~/.lovstudio/skills/lov-list-videos/cache.json`` by default) so every host
and every scope share the same index.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

SKILL_ID = "lov-list-videos"
CACHE_SCHEMA = "lov-list-videos/cache/v1"
RESULT_SCHEMA = "lov-list-videos/result/v1"

DEFAULT_EXTENSIONS = {
    "mp4", "m4v", "mov", "avi", "mkv", "webm", "flv", "wmv", "mpg", "mpeg",
    "mpe", "m2v", "m2ts", "mts", "ts", "3gp", "3g2", "vob", "ogv", "ogm",
    "mxf", "rm", "rmvb", "asf", "f4v", "divx", "dv", "insv", "braw", "r3d",
    "y4m", "hevc", "h264", "264", "265",
}

# Names are matched against a directory's basename; patterns containing "/"
# are matched against the end of the absolute path.
DEFAULT_EXCLUDES = [
    "node_modules", "venv", "__pycache__", "Caches",
    "Library/Application Support", "Library/Developer", "Library/Containers",
    "Library/Group Containers", "Library/Logs", "Library/Metadata",
    "Library/Biome", "Library/Daemon Containers", "Library/Suggestions",
    "System", "private", "dev", "cores", "Volumes/Recovery",
]
DEFAULT_BUNDLE_SUFFIXES = (
    ".app", ".framework", ".xcarchive", ".photoslibrary", ".tvlibrary",
    ".musiclibrary", ".aplibrary", ".imovielibrary",
)

SIZE_UNITS = {"": 1, "b": 1, "k": 1024, "m": 1024 ** 2, "g": 1024 ** 3, "t": 1024 ** 4}


# --------------------------------------------------------------------------- #
# Profile and cache location
# --------------------------------------------------------------------------- #
def config_dir() -> Path:
    configured = os.environ.get("SKILLS_CONFIG_DIR")
    if configured:
        return Path(os.path.expandvars(configured)).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(os.path.expandvars(xdg)).expanduser() / "agent-skills"
    return Path.home() / ".config" / "agent-skills"


def profile_path() -> Path:
    """Mirror scripts/profile_store.py so cache and Profile share one home."""
    configured = os.environ.get("SKILL_PROFILE_PATH") or os.environ.get("SKILLS_PROFILE_PATH")
    if configured:
        return Path(os.path.expandvars(configured)).expanduser()
    candidates = (
        Path.home() / ".lovstudio" / "skills" / "profile.json",
        Path.home() / ".skill-publisher" / "skills" / "profile.json",
        config_dir() / "profile.json",
    )
    return next((c for c in candidates if c.exists()), candidates[-1])


def read_profile_records() -> dict[str, Any]:
    path = profile_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    skills = data.get("skills") if isinstance(data, dict) else None
    entry = skills.get(SKILL_ID) if isinstance(skills, dict) else None
    records = entry.get("records") if isinstance(entry, dict) else None
    return records if isinstance(records, dict) else {}


def default_cache_path() -> Path:
    env = os.environ.get("LOV_LIST_VIDEOS_CACHE")
    if env:
        return Path(os.path.expandvars(env)).expanduser()
    return profile_path().parent / SKILL_ID / "cache.json"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def parse_size(text: str) -> int:
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([kmgtb]?)(?:i?b)?\s*", text, re.I)
    if not match:
        raise argparse.ArgumentTypeError(f"invalid size: {text!r} (use e.g. 500M, 1.5G)")
    return int(float(match.group(1)) * SIZE_UNITS[match.group(2).lower()])


def parse_since(text: str) -> float:
    match = re.fullmatch(r"\s*(\d+)\s*([hdwm])\s*", text, re.I)
    if match:
        amount = int(match.group(1))
        unit = match.group(2).lower()
        delta = {"h": timedelta(hours=amount), "d": timedelta(days=amount),
                 "w": timedelta(weeks=amount), "m": timedelta(days=30 * amount)}[unit]
        return (datetime.now() - delta).timestamp()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text.strip(), fmt).timestamp()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"invalid --since: {text!r} (use 7d, 24h, 2w or YYYY-MM-DD)")


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "K", "M", "G", "T"):
        if value < 1024 or unit == "T":
            return f"{value:.0f}{unit}" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}T"


def human_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "-"
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def file_ext(name: str) -> str:
    dot = name.rfind(".")
    return name[dot + 1:].lower() if dot > 0 else ""


def log(message: str, quiet: bool) -> None:
    if not quiet:
        print(message, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# Cache
# --------------------------------------------------------------------------- #
def empty_cache() -> dict[str, Any]:
    return {"schema": CACHE_SCHEMA, "extensions": [], "updated_at": None, "dirs": {}, "probe": {}}


def load_cache(path: Path, quiet: bool) -> dict[str, Any]:
    if not path.exists():
        return empty_cache()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log(f"cache unreadable, rebuilding: {path}: {exc}", quiet)
        return empty_cache()
    if not isinstance(data, dict) or data.get("schema") != CACHE_SCHEMA:
        log(f"cache schema mismatch, rebuilding: {path}", quiet)
        return empty_cache()
    data.setdefault("dirs", {})
    data.setdefault("probe", {})
    data.setdefault("extensions", [])
    return data


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cache["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    fd, tmp = tempfile.mkstemp(prefix=".cache-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(cache, handle, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------- #
# Scanner
# --------------------------------------------------------------------------- #
class Excluder:
    def __init__(self, patterns: Iterable[str], bundle_suffixes: Iterable[str], hidden: bool) -> None:
        self.names = {p for p in patterns if "/" not in p}
        self.paths = tuple("/" + p.strip("/") for p in patterns if "/" in p)
        self.suffixes = tuple(bundle_suffixes)
        self.hidden = hidden

    def skip(self, name: str, full_path: str) -> bool:
        if not self.hidden and name.startswith("."):
            return True
        if name in self.names:
            return True
        lowered = name.lower()
        if lowered.endswith(self.suffixes):
            return True
        return any(full_path.endswith(p) for p in self.paths)


class Scanner:
    def __init__(self, cache: dict[str, Any], extensions: set[str], excluder: Excluder,
                 rescan_all: bool, hidden: bool, quiet: bool) -> None:
        self.dirs: dict[str, Any] = cache["dirs"]
        self.extensions = extensions
        self.excluder = excluder
        self.rescan_all = rescan_all
        self.hidden = hidden
        self.quiet = quiet
        self.visited: set[str] = set()
        self.stats = {"dirs_visited": 0, "dirs_scanned": 0, "dirs_reused": 0,
                      "errors": 0, "videos": 0}
        self._last_progress = 0.0

    def _progress(self) -> None:
        if self.quiet or not sys.stderr.isatty():
            return
        now = time.monotonic()
        if now - self._last_progress < 0.5:
            return
        self._last_progress = now
        s = self.stats
        print(f"\r  dirs {s['dirs_visited']} (scanned {s['dirs_scanned']}, reused {s['dirs_reused']})"
              f"  videos {s['videos']}", end="", file=sys.stderr, flush=True)

    def _is_video_name(self, name: str) -> bool:
        if name.startswith("._"):
            return False  # AppleDouble sidecars on external volumes
        if not self.hidden and name.startswith("."):
            return False
        return file_ext(name) in self.extensions

    def _list_dir(self, path: str) -> tuple[list[str], dict[str, list[int]]]:
        subdirs: list[str] = []
        videos: dict[str, list[int]] = {}
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        subdirs.append(entry.name)
                    elif entry.is_file(follow_symlinks=False) and self._is_video_name(entry.name):
                        st = entry.stat(follow_symlinks=False)
                        videos[entry.name] = [st.st_size, st.st_mtime_ns]
                except OSError:
                    self.stats["errors"] += 1
        return subdirs, videos

    def _refresh_videos(self, path: str, videos: dict[str, list[int]]) -> None:
        # In-place edits do not bump the parent mtime, so re-stat cached videos.
        for name in list(videos):
            try:
                st = os.stat(os.path.join(path, name))
                videos[name] = [st.st_size, st.st_mtime_ns]
            except OSError:
                del videos[name]

    def walk(self, root: str) -> None:
        stack = [root]
        while stack:
            path = stack.pop()
            try:
                mtime = os.stat(path).st_mtime_ns
            except OSError:
                self.stats["errors"] += 1
                continue
            cached = self.dirs.get(path)
            if cached and cached.get("m") == mtime and not self.rescan_all:
                subdirs, videos = cached["d"], cached["v"]
                self._refresh_videos(path, videos)
                self.stats["dirs_reused"] += 1
            else:
                try:
                    subdirs, videos = self._list_dir(path)
                except OSError:
                    self.stats["errors"] += 1
                    continue
                self.dirs[path] = {"m": mtime, "d": subdirs, "v": videos}
                self.stats["dirs_scanned"] += 1
            self.visited.add(path)
            self.stats["dirs_visited"] += 1
            self.stats["videos"] += len(videos)
            self._progress()
            for name in subdirs:
                child = os.path.join(path, name)
                if not self.excluder.skip(name, child):
                    stack.append(child)

    def prune(self, roots: list[str]) -> int:
        """Drop cached directories that no longer exist under a scanned root."""
        removed = 0
        prefixes = tuple(r.rstrip("/") + "/" for r in roots)
        for key in sorted(self.dirs):
            if key in self.visited or not key.startswith(prefixes):
                continue
            parent, name = os.path.split(key)
            parent_entry = self.dirs.get(parent)
            if parent_entry is None or name not in parent_entry.get("d", ()):
                del self.dirs[key]
                removed += 1
        return removed

    def collect(self, roots: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        prefixes = tuple(r.rstrip("/") + "/" for r in roots)
        for path in self.visited:
            entry = self.dirs.get(path)
            if not entry:
                continue
            if not (path in roots or path.startswith(prefixes)):
                continue
            for name, (size, mtime_ns) in entry["v"].items():
                ext = file_ext(name)
                if ext not in self.extensions:
                    continue
                results.append({
                    "path": os.path.join(path, name),
                    "name": name,
                    "ext": ext,
                    "size": size,
                    "mtime": mtime_ns / 1e9,
                })
        return results


# --------------------------------------------------------------------------- #
# ffprobe
# --------------------------------------------------------------------------- #
def probe_one(path: str) -> dict[str, Any]:
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        data = json.loads(out.stdout or "{}")
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as exc:
        return {"error": str(exc)[:200]}
    fmt = data.get("format", {})
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    fps = None
    rate = video.get("avg_frame_rate") or video.get("r_frame_rate") or ""
    if "/" in rate:
        num, den = rate.split("/", 1)
        try:
            fps = round(float(num) / float(den), 3) if float(den) else None
        except ValueError:
            fps = None
    duration = fmt.get("duration") or video.get("duration")
    return {
        "duration": float(duration) if duration else None,
        "width": video.get("width"),
        "height": video.get("height"),
        "vcodec": video.get("codec_name"),
        "vprofile": video.get("profile"),
        "pix_fmt": video.get("pix_fmt"),
        "fps": fps,
        "acodec": audio.get("codec_name"),
        "bit_rate": int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        "container": fmt.get("format_name"),
    }


def probe_videos(videos: list[dict[str, Any]], cache: dict[str, Any], workers: int, quiet: bool) -> int:
    if shutil.which("ffprobe") is None:
        raise SystemExit("--probe requires ffprobe on PATH (brew install ffmpeg)")
    store: dict[str, Any] = cache["probe"]
    pending: list[dict[str, Any]] = []
    for item in videos:
        key = f"{item['size']}:{int(item['mtime'] * 1e9)}"
        hit = store.get(item["path"])
        if hit and hit.get("key") == key and "error" not in hit:
            item.update({k: v for k, v in hit.items() if k != "key"})
        else:
            item["_probe_key"] = key
            pending.append(item)
    if pending:
        log(f"probing {len(pending)} videos with ffprobe ...", quiet)
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            for item, meta in zip(pending, pool.map(lambda v: probe_one(v["path"]), pending)):
                key = item.pop("_probe_key")
                store[item["path"]] = {"key": key, **meta}
                item.update(meta)
    # Drop probe entries for files that no longer appear anywhere in the index.
    known = {os.path.join(d, n) for d, e in cache["dirs"].items() for n in e.get("v", {})}
    for path in [p for p in store if p not in known]:
        del store[path]
    return len(pending)


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def sort_videos(videos: list[dict[str, Any]], key: str, descending: bool) -> None:
    keyfn = {
        "size": lambda v: v["size"],
        "mtime": lambda v: v["mtime"],
        "path": lambda v: v["path"].lower(),
        "name": lambda v: v["name"].lower(),
        "duration": lambda v: v.get("duration") or 0.0,
    }[key]
    videos.sort(key=keyfn, reverse=descending)


def render_table(videos: list[dict[str, Any]], probed: bool, base: Optional[str]) -> str:
    rows = []
    header = ["SIZE", "MODIFIED"] + (["DURATION", "RES", "CODEC"] if probed else []) + ["PATH"]
    for v in videos:
        shown = os.path.relpath(v["path"], base) if base else v["path"]
        row = [human_size(v["size"]), datetime.fromtimestamp(v["mtime"]).strftime("%Y-%m-%d %H:%M")]
        if probed:
            res = f"{v.get('width')}x{v.get('height')}" if v.get("width") else "-"
            row += [human_duration(v.get("duration")), res, v.get("vcodec") or "-"]
        row.append(shown)
        rows.append(row)
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header) - 1)]
    lines = []
    for r in [header] + rows:
        cells = [str(c).rjust(widths[i]) if i == 0 else str(c).ljust(widths[i]) for i, c in enumerate(r[:-1])]
        lines.append("  ".join(cells + [str(r[-1])]))
    return "\n".join(lines)


def render_csv(videos: list[dict[str, Any]], probed: bool) -> str:
    fields = ["path", "name", "ext", "size", "mtime_iso"]
    if probed:
        fields += ["duration", "width", "height", "vcodec", "acodec", "fps", "bit_rate"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for v in videos:
        writer.writerow({**v, "mtime_iso": datetime.fromtimestamp(v["mtime"]).isoformat(timespec="seconds")})
    return buf.getvalue().rstrip("\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def resolve_roots(args: argparse.Namespace, records: dict[str, Any]) -> tuple[list[str], str]:
    if args.roots and args.global_scope:
        raise SystemExit("pass either ROOT paths or --global, not both")
    scope = "global" if args.global_scope else ("global" if not args.roots and records.get("default_scope") == "global" else "current")
    if scope == "global":
        configured = records.get("global_roots")
        if isinstance(configured, list) and configured:
            candidates = [os.path.expanduser(os.path.expandvars(str(r))) for r in configured]
        else:
            candidates = [str(Path.home())]
            volumes = Path("/Volumes")
            if volumes.is_dir():
                for vol in sorted(volumes.iterdir()):
                    try:
                        if vol.is_symlink() or not vol.is_dir() or os.path.realpath(vol) == "/":
                            continue
                    except OSError:
                        continue
                    candidates.append(str(vol))
        roots = candidates
    else:
        roots = args.roots or [os.getcwd()]
    resolved: list[str] = []
    for root in roots:
        real = os.path.realpath(os.path.abspath(os.path.expanduser(root)))
        if not os.path.isdir(real):
            raise SystemExit(f"root is not a directory: {root}")
        if real not in resolved:
            resolved.append(real)
    # Drop roots nested inside another requested root to avoid double counting.
    resolved = [r for r in resolved if not any(o != r and r.startswith(o.rstrip("/") + "/") for o in resolved)]
    return resolved, scope


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List all video files under the given roots using an incremental directory cache.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  list_videos.py                       # current directory\n"
            "  list_videos.py ~/Movies ~/Downloads  # several roots\n"
            "  list_videos.py --global --format json # home + mounted volumes\n"
            "  list_videos.py --since 7d --min-size 200M --probe\n"
        ),
    )
    parser.add_argument("roots", nargs="*", help="directories to scan (default: current directory)")
    parser.add_argument("--global", dest="global_scope", action="store_true",
                        help="scan the home directory and mounted volumes instead of ROOT")
    parser.add_argument("--cache", type=Path, default=None,
                        help="cache file (default: $LOV_LIST_VIDEOS_CACHE or <profile dir>/lov-list-videos/cache.json)")
    parser.add_argument("--full", action="store_true", help="ignore cached directory listings and rescan everything")
    parser.add_argument("--no-cache", action="store_true", help="neither read nor write the cache")
    parser.add_argument("--clear-cache", action="store_true", help="delete the cache file and exit")
    parser.add_argument("--hidden", action="store_true", help="include hidden directories and files")
    parser.add_argument("--ext", nargs="+", metavar="EXT", help="only list these extensions (added to the scan set)")
    parser.add_argument("--exclude", nargs="+", metavar="NAME", default=[],
                        help="extra directory names or path suffixes to skip")
    parser.add_argument("--no-default-excludes", action="store_true",
                        help="scan node_modules, Library caches, app bundles and other noisy folders too")
    parser.add_argument("--format", choices=("table", "json", "paths", "csv"), default=None)
    parser.add_argument("--sort", choices=("mtime", "size", "path", "name", "duration"), default=None)
    parser.add_argument("--asc", action="store_true", help="ascending order (default for path/name)")
    parser.add_argument("--desc", action="store_true", help="descending order (default for mtime/size/duration)")
    parser.add_argument("--limit", type=int, default=None, help="show at most N videos after sorting")
    parser.add_argument("--min-size", type=parse_size, default=None, help="e.g. 100M, 1.5G")
    parser.add_argument("--max-size", type=parse_size, default=None)
    parser.add_argument("--since", type=parse_since, default=None, help="modified after: 7d, 24h, 2w or YYYY-MM-DD")
    parser.add_argument("--match", default=None, help="case-insensitive substring the path must contain")
    parser.add_argument("--probe", action="store_true", help="add duration/resolution/codec via ffprobe (cached)")
    parser.add_argument("--workers", type=int, default=4, help="parallel ffprobe processes")
    parser.add_argument("--relative", action="store_true", help="print paths relative to the single root")
    parser.add_argument("--quiet", "-q", action="store_true", help="suppress progress and summary on stderr")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    records = read_profile_records()
    cache_path = args.cache or default_cache_path()

    if args.clear_cache:
        if cache_path.exists():
            cache_path.unlink()
            log(f"cache removed: {cache_path}", args.quiet)
        else:
            log(f"no cache at: {cache_path}", args.quiet)
        return 0

    roots, scope = resolve_roots(args, records)
    fmt = args.format or str(records.get("default_format") or "table")
    sort_key = args.sort or str(records.get("default_sort") or "mtime")
    descending = args.desc or (sort_key in ("mtime", "size", "duration") and not args.asc)

    list_exts = {e.lower().lstrip(".") for e in (args.ext or [])}
    scan_exts = set(DEFAULT_EXTENSIONS) | list_exts
    for extra in records.get("extra_extensions") or []:
        scan_exts.add(str(extra).lower().lstrip("."))
    filter_exts = list_exts or scan_exts

    excludes = [] if args.no_default_excludes else list(DEFAULT_EXCLUDES)
    excludes += [str(e) for e in (records.get("extra_excludes") or [])]
    excludes += args.exclude
    bundles = () if args.no_default_excludes else DEFAULT_BUNDLE_SUFFIXES
    excluder = Excluder(excludes, bundles, args.hidden)

    cache = empty_cache() if args.no_cache else load_cache(cache_path, args.quiet)
    cached_exts = set(cache.get("extensions") or [])
    rescan_all = args.full or not scan_exts <= cached_exts or bool(cache.get("hidden")) != args.hidden
    if rescan_all and cache["dirs"] and not args.full:
        log("scan settings changed (extensions or hidden); relisting directories", args.quiet)

    started = time.monotonic()
    scanner = Scanner(cache, scan_exts, excluder, rescan_all, args.hidden, args.quiet)
    log(f"scanning {scope}: " + ", ".join(roots), args.quiet)
    for root in roots:
        scanner.walk(root)
    if not args.quiet and sys.stderr.isatty():
        print("", file=sys.stderr)
    pruned = scanner.prune(roots)
    scanner.extensions = filter_exts
    videos = scanner.collect(roots)
    elapsed = time.monotonic() - started

    if args.min_size is not None:
        videos = [v for v in videos if v["size"] >= args.min_size]
    if args.max_size is not None:
        videos = [v for v in videos if v["size"] <= args.max_size]
    if args.since is not None:
        videos = [v for v in videos if v["mtime"] >= args.since]
    if args.match:
        needle = args.match.lower()
        videos = [v for v in videos if needle in v["path"].lower()]

    matched = len(videos)
    matched_bytes = sum(v["size"] for v in videos)
    if sort_key == "duration" and not args.probe:
        args.probe = True
    if args.probe and sort_key != "duration":
        # Probe only what will be shown; sorting by duration needs every probe first.
        sort_videos(videos, sort_key, descending)
        if args.limit is not None:
            videos = videos[: args.limit]
        probe_videos(videos, cache, args.workers, args.quiet)
    else:
        if args.probe:
            probe_videos(videos, cache, args.workers, args.quiet)
        sort_videos(videos, sort_key, descending)
        if args.limit is not None:
            videos = videos[: args.limit]

    if not args.no_cache:
        cache["extensions"] = sorted(scan_exts | cached_exts)
        cache["hidden"] = args.hidden
        save_cache(cache_path, cache)

    stats = {
        **scanner.stats,
        "pruned": pruned,
        "elapsed_s": round(elapsed, 3),
        "cache_path": None if args.no_cache else str(cache_path),
        "cache_hit_ratio": round(scanner.stats["dirs_reused"] / scanner.stats["dirs_visited"], 3)
        if scanner.stats["dirs_visited"] else 0.0,
    }
    base = roots[0] if args.relative and len(roots) == 1 else None

    if fmt == "json":
        for v in videos:
            v["mtime_iso"] = datetime.fromtimestamp(v["mtime"]).isoformat(timespec="seconds")
        payload = {
            "schema": RESULT_SCHEMA, "scope": scope, "roots": roots,
            "matched": matched, "shown": len(videos),
            "total_bytes": matched_bytes, "total_human": human_size(matched_bytes),
            "probed": bool(args.probe), "videos": videos, "scan": stats,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif fmt == "paths":
        for v in videos:
            print(os.path.relpath(v["path"], base) if base else v["path"])
    elif fmt == "csv":
        print(render_csv(videos, bool(args.probe)))
    else:
        if videos:
            print(render_table(videos, bool(args.probe), base))
        else:
            print("no videos found")

    shown = f"showing {len(videos)} of " if len(videos) != matched else ""
    log(
        f"{shown}{matched} videos, {human_size(matched_bytes)} total | dirs {stats['dirs_visited']} "
        f"(scanned {stats['dirs_scanned']}, reused {stats['dirs_reused']}, pruned {pruned}, "
        f"errors {stats['errors']}) | {elapsed:.2f}s | cache: {stats['cache_path'] or 'off'}",
        args.quiet,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)
