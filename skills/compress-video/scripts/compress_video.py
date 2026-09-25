#!/usr/bin/env python3
"""Compress a video file to the smallest size that still looks good.

Defaults to HEVC (libx265) at CRF 28 with AAC 96k audio, keeps resolution and
frame rate, and writes ``<stem>-compressed.mp4`` next to the source. A quality
preset or explicit CRF adjusts the trade-off; ``--min-vmaf`` measures the
result with libvmaf and re-encodes at a lower CRF when the score is too low;
``--target-size`` switches to two-pass bitrate mode. The source file is never
modified, and an output that would be larger than the source is discarded
unless ``--force`` is given.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

SKILL_ID = "lov-compress-video"
RESULT_SCHEMA = "lov-compress-video/result/v1"

QUALITIES = ("smallest", "small", "balanced", "high")
CODECS = ("hevc", "h264", "av1")

# CRF (or VideoToolbox -q:v) per codec and quality preset.
CRF_TABLE = {
    "hevc": {"smallest": 32, "small": 28, "balanced": 25, "high": 22},
    "h264": {"smallest": 28, "small": 25, "balanced": 22, "high": 19},
    "av1": {"smallest": 44, "small": 38, "balanced": 33, "high": 28},
    "vt": {"smallest": 35, "small": 45, "balanced": 55, "high": 65},
}
CRF_STEP = {"hevc": 3, "h264": 3, "av1": 5, "vt": -8}
AUDIO_TABLE = {"smallest": 64, "small": 96, "balanced": 128, "high": 160}
PRESET_TABLE = {"smallest": "slow", "small": "medium", "balanced": "medium", "high": "medium"}
MAX_EDGE_TABLE = {"smallest": 1080, "small": None, "balanced": None, "high": None}

SIZE_UNITS = {"": 1, "b": 1, "k": 1024, "m": 1024 ** 2, "g": 1024 ** 3, "t": 1024 ** 4}


# --------------------------------------------------------------------------- #
# Profile
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


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def parse_size(text: str) -> int:
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([kmgtb]?)(?:i?b)?\s*", text, re.I)
    if not match:
        raise argparse.ArgumentTypeError(f"invalid size: {text!r} (use e.g. 50M, 1.5G)")
    return int(float(match.group(1)) * SIZE_UNITS[match.group(2).lower()])


def parse_bitrate(text: str) -> int:
    """Return kbit/s from '96k', '128', '1.5m'."""
    match = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([km]?)(?:bps|bit/s|b)?\s*", text, re.I)
    if not match:
        raise argparse.ArgumentTypeError(f"invalid bitrate: {text!r} (use e.g. 96k)")
    value = float(match.group(1))
    unit = match.group(2).lower()
    return int(value * 1000) if unit == "m" else int(value)


def human_size(size: float) -> str:
    value = float(size)
    for unit in ("B", "K", "M", "G", "T"):
        if value < 1024 or unit == "T":
            return f"{value:.0f}{unit}" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}T"


def human_time(seconds: float) -> str:
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def log(message: str, quiet: bool) -> None:
    if not quiet:
        print(message, file=sys.stderr, flush=True)


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"{name} not found on PATH (brew install ffmpeg)")
    return path


def ffprobe(path: Path) -> dict[str, Any]:
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"ffprobe failed for {path}: {proc.stderr.strip()[:300]}")
    data = json.loads(proc.stdout or "{}")
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"
                  and s.get("disposition", {}).get("attached_pic", 0) != 1), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if video is None:
        raise SystemExit(f"no video stream in {path}")
    fps = None
    rate = video.get("avg_frame_rate") or video.get("r_frame_rate") or ""
    if "/" in rate:
        num, den = rate.split("/", 1)
        try:
            fps = float(num) / float(den) if float(den) else None
        except ValueError:
            fps = None
    duration = fmt.get("duration") or video.get("duration")
    return {
        "size": int(fmt.get("size") or path.stat().st_size),
        "duration": float(duration) if duration else 0.0,
        "bit_rate": int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
        "container": fmt.get("format_name"),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "vcodec": video.get("codec_name"),
        "pix_fmt": video.get("pix_fmt") or "yuv420p",
        "fps": fps,
        "vbit_rate": int(video["bit_rate"]) if video.get("bit_rate") else None,
        "acodec": audio.get("codec_name") if audio else None,
        "abit_rate": int(audio["bit_rate"]) if audio and audio.get("bit_rate") else None,
        "channels": int(audio.get("channels") or 0) if audio else 0,
        "has_audio": audio is not None,
    }


def is_ten_bit(pix_fmt: str) -> bool:
    return bool(re.search(r"(10|12)(le|be)?$", pix_fmt))


# --------------------------------------------------------------------------- #
# Encoding plan
# --------------------------------------------------------------------------- #
class Plan:
    def __init__(self, args: argparse.Namespace, records: dict[str, Any], info: dict[str, Any]) -> None:
        self.quality = args.quality or str(records.get("default_quality") or "small")
        if self.quality not in QUALITIES:
            raise SystemExit(f"unknown quality {self.quality!r}; use one of {', '.join(QUALITIES)}")
        self.codec = args.codec or str(records.get("default_codec") or "hevc")
        if self.codec not in CODECS:
            raise SystemExit(f"unknown codec {self.codec!r}; use one of {', '.join(CODECS)}")
        self.fast = bool(args.fast)
        if self.fast and self.codec == "av1":
            raise SystemExit("--fast (VideoToolbox) supports hevc and h264 only")
        if self.fast and platform.system() != "Darwin":
            raise SystemExit("--fast uses VideoToolbox and requires macOS")
        table_key = "vt" if self.fast else self.codec
        self.crf = args.crf if args.crf is not None else CRF_TABLE[table_key][self.quality]
        self.crf_step = CRF_STEP[table_key]
        self.preset = args.preset or str(records.get("default_preset") or PRESET_TABLE[self.quality])
        self.audio_kbps = args.audio_bitrate if args.audio_bitrate is not None else int(
            records.get("audio_bitrate") or AUDIO_TABLE[self.quality])
        max_edge = args.max_edge if args.max_edge is not None else records.get("max_edge") or MAX_EDGE_TABLE[self.quality]
        self.max_edge = int(max_edge) if max_edge else None
        self.fps = args.fps
        self.target_size = args.target_size
        if self.target_size and (self.fast or self.codec == "av1"):
            raise SystemExit("--target-size uses two-pass software encoding; choose hevc or h264 without --fast")
        self.ten_bit = is_ten_bit(info["pix_fmt"])
        self.info = info
        self.hwaccel = platform.system() == "Darwin" and not args.no_hwaccel

    # -- derived values ----------------------------------------------------- #
    def scale_filter(self) -> Optional[str]:
        w, h = self.info["width"], self.info["height"]
        if not self.max_edge or max(w, h) <= self.max_edge:
            return None
        return f"scale={self.max_edge}:-2" if w >= h else f"scale=-2:{self.max_edge}"

    def video_filters(self) -> list[str]:
        filters = []
        scale = self.scale_filter()
        if scale:
            filters.append(scale)
        if self.fps and self.info["fps"] and self.fps < self.info["fps"] - 0.01:
            filters.append(f"fps={self.fps}")
        return filters

    def pix_fmt(self) -> str:
        if self.fast:
            return "p010le" if self.ten_bit else "nv12"
        return "yuv420p10le" if self.ten_bit else "yuv420p"

    def audio_args(self) -> tuple[list[str], str]:
        info = self.info
        if not info["has_audio"]:
            return ["-an"], "none"
        src_kbps = (info["abit_rate"] or 0) / 1000
        if info["acodec"] == "aac" and src_kbps and src_kbps <= self.audio_kbps * 1.15:
            return ["-c:a", "copy"], f"copy (aac {src_kbps:.0f}k)"
        args = ["-c:a", "aac", "-b:a", f"{self.audio_kbps}k"]
        if info["channels"] > 2:
            args += ["-ac", "2"]
        return args, f"aac {self.audio_kbps}k"

    def video_args(self, crf: float, pass_no: int = 0, passlog: str = "", vbitrate_kbps: int = 0) -> list[str]:
        args: list[str] = []
        if self.fast:
            encoder = "hevc_videotoolbox" if self.codec == "hevc" else "h264_videotoolbox"
            args += ["-c:v", encoder, "-q:v", str(int(crf)), "-allow_sw", "1"]
            if self.codec == "hevc":
                args += ["-tag:v", "hvc1"]
                if self.ten_bit:
                    args += ["-profile:v", "main10"]
            return args
        if self.codec == "hevc":
            args += ["-c:v", "libx265", "-preset", self.preset, "-tag:v", "hvc1"]
            params = ["log-level=error"]
            if pass_no:
                params += [f"pass={pass_no}", f"stats={passlog}"]
                args += ["-b:v", f"{vbitrate_kbps}k"]
            else:
                args += ["-crf", str(crf)]
            args += ["-x265-params", ":".join(params)]
        elif self.codec == "h264":
            args += ["-c:v", "libx264", "-preset", self.preset]
            if pass_no:
                args += ["-b:v", f"{vbitrate_kbps}k", "-pass", str(pass_no), "-passlogfile", passlog]
            else:
                args += ["-crf", str(crf)]
        else:
            svt_preset = {"ultrafast": 10, "veryfast": 9, "faster": 8, "fast": 7, "medium": 6,
                          "slow": 4, "slower": 3, "veryslow": 2}.get(self.preset, 6)
            args += ["-c:v", "libsvtav1", "-crf", str(int(crf)), "-preset", str(svt_preset)]
        return args

    def describe(self, crf: float) -> str:
        enc = ("VideoToolbox " + self.codec.upper()) if self.fast else {
            "hevc": "libx265", "h264": "libx264", "av1": "libsvtav1"}[self.codec]
        parts = [enc, f"q={crf}" if self.fast else f"crf={crf}", f"preset={self.preset}", self.pix_fmt()]
        filters = self.video_filters()
        if filters:
            parts.append(",".join(filters))
        return " ".join(parts)


# --------------------------------------------------------------------------- #
# ffmpeg execution
# --------------------------------------------------------------------------- #
def run_ffmpeg(cmd: list[str], duration: float, quiet: bool, label: str) -> None:
    """Run ffmpeg with -progress on stdout, show percent/speed/ETA on a tty."""
    full = cmd + ["-progress", "pipe:1", "-nostats"]
    started = time.monotonic()
    proc = subprocess.Popen(full, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    show = not quiet and sys.stderr.isatty()
    last = 0.0
    assert proc.stdout is not None
    for line in proc.stdout:
        if not show or not line.startswith("out_time_"):
            continue
        key, _, value = line.strip().partition("=")
        try:
            if key == "out_time_us":
                seconds = int(value) / 1_000_000
            elif key == "out_time_ms":
                seconds = int(value) / 1_000_000
            else:
                continue
        except ValueError:
            continue
        now = time.monotonic()
        if now - last < 0.5:
            continue
        last = now
        elapsed = now - started
        pct = min(100.0, seconds / duration * 100) if duration else 0.0
        speed = seconds / elapsed if elapsed else 0.0
        eta = (duration - seconds) / speed if speed > 0 and duration else 0.0
        print(f"\r  {label}: {pct:5.1f}%  {speed:4.1f}x  ETA {human_time(eta)}   ",
              end="", file=sys.stderr, flush=True)
    stderr = proc.stderr.read() if proc.stderr else ""
    proc.wait()
    if show:
        print("\r" + " " * 60 + "\r", end="", file=sys.stderr, flush=True)
    if proc.returncode != 0:
        tail = "\n".join(stderr.strip().splitlines()[-15:])
        raise RuntimeError(f"ffmpeg exited {proc.returncode}\n{tail}")


def base_input_args(plan: Plan, src: Path, hwaccel: bool) -> list[str]:
    args = ["ffmpeg", "-hide_banner", "-y", "-loglevel", "error"]
    if hwaccel:
        args += ["-hwaccel", "videotoolbox"]
    args += ["-i", str(src)]
    return args


def output_common(plan: Plan, dest: Path) -> list[str]:
    args = ["-map", "0:v:0", "-map", "0:a?", "-sn", "-dn", "-map_metadata", "0",
            "-map_chapters", "0", "-pix_fmt", plan.pix_fmt()]
    filters = plan.video_filters()
    if filters:
        args += ["-vf", ",".join(filters)]
    args += ["-movflags", "+faststart", str(dest)]
    return args


def encode(plan: Plan, src: Path, dest: Path, crf: float, quiet: bool) -> list[str]:
    """Encode once (CRF mode or two-pass target-size mode). Returns the command used."""
    audio_args, _ = plan.audio_args()
    duration = plan.info["duration"]

    def attempt(hwaccel: bool) -> list[str]:
        if plan.target_size:
            audio_kbps = 0 if not plan.info["has_audio"] else plan.audio_kbps
            if plan.info["has_audio"] and audio_args[1] == "copy":
                audio_kbps = int((plan.info["abit_rate"] or 0) / 1000)
            total_kbps = plan.target_size * 8 / 1000 / max(duration, 0.1)
            vbitrate = int(total_kbps * 0.97 - audio_kbps)
            if vbitrate < 50:
                raise SystemExit(f"--target-size {human_size(plan.target_size)} is too small for {human_time(duration)} of video")
            with tempfile.TemporaryDirectory(prefix="compress-video-") as tmp:
                passlog = os.path.join(tmp, "pass")
                first = base_input_args(plan, src, hwaccel) + plan.video_args(crf, 1, passlog, vbitrate) + [
                    "-an", "-pix_fmt", plan.pix_fmt()]
                filters = plan.video_filters()
                if filters:
                    first += ["-vf", ",".join(filters)]
                first += ["-f", "null", os.devnull]
                run_ffmpeg(first, duration, quiet, "pass 1/2")
                second = base_input_args(plan, src, hwaccel) + plan.video_args(crf, 2, passlog, vbitrate) + audio_args + output_common(plan, dest)
                run_ffmpeg(second, duration, quiet, "pass 2/2")
                return second
        cmd = base_input_args(plan, src, hwaccel) + plan.video_args(crf) + audio_args + output_common(plan, dest)
        run_ffmpeg(cmd, duration, quiet, "encoding")
        return cmd

    try:
        return attempt(plan.hwaccel)
    except RuntimeError as exc:
        if not plan.hwaccel:
            raise
        log(f"hardware decode failed, retrying with software decode: {str(exc).splitlines()[-1][:120]}", quiet)
        return attempt(False)


def measure_vmaf(plan: Plan, src: Path, dest: Path, quiet: bool) -> Optional[float]:
    """VMAF of dest against src; dest is rescaled to the source size when needed."""
    threads = max(1, (os.cpu_count() or 4))
    w, h = plan.info["width"], plan.info["height"]
    chain_out = f"[0:v]scale={w}:{h}:flags=bicubic,format=yuv420p,setpts=PTS-STARTPTS[o]"
    ref_filters = ["format=yuv420p", "setpts=PTS-STARTPTS"]
    if plan.fps and plan.info["fps"] and plan.fps < plan.info["fps"] - 0.01:
        ref_filters.insert(0, f"fps={plan.fps}")
    chain_ref = "[1:v]" + ",".join(ref_filters) + "[r]"
    graph = f"{chain_out};{chain_ref};[o][r]libvmaf=n_threads={threads}"
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(dest), "-i", str(src),
           "-lavfi", graph, "-f", "null", "-"]
    log("  measuring VMAF ...", quiet)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    match = re.search(r"VMAF score:\s*([0-9.]+)", proc.stderr)
    if not match:
        log("  VMAF unavailable: " + proc.stderr.strip().splitlines()[-1][:160] if proc.stderr.strip() else "  VMAF unavailable", quiet)
        return None
    return round(float(match.group(1)), 2)


# --------------------------------------------------------------------------- #
# Per-file driver
# --------------------------------------------------------------------------- #
def default_output(src: Path, output_dir: Optional[Path]) -> Path:
    folder = output_dir or src.parent
    return folder / f"{src.stem}-compressed.mp4"


def compress_one(src: Path, args: argparse.Namespace, records: dict[str, Any]) -> dict[str, Any]:
    quiet = args.quiet
    src = src.expanduser().resolve()
    if not src.is_file():
        raise SystemExit(f"input not found: {src}")
    info = ffprobe(src)
    plan = Plan(args, records, info)
    replace = bool(args.replace or (not args.output and not args.output_dir and records.get("replace_original") is True))
    if replace and (args.output or args.output_dir):
        raise SystemExit("--replace writes next to the source; drop --output/--output-dir")
    output_dir = args.output_dir or (Path(str(records["output_dir"])).expanduser() if records.get("output_dir") else None)
    if replace:
        dest = src.with_suffix(".mp4")
    else:
        dest = (args.output.expanduser().resolve() if args.output else default_output(src, output_dir))
        if dest == src:
            raise SystemExit("output path equals the input; use --replace to swap the source")
    if dest.exists() and dest != src and not args.overwrite:
        raise SystemExit(f"output exists: {dest} (use --overwrite)")
    dest.parent.mkdir(parents=True, exist_ok=True)

    min_vmaf = args.min_vmaf if args.min_vmaf is not None else (
        float(records["min_vmaf"]) if records.get("min_vmaf") else None)
    want_vmaf = bool(args.vmaf or min_vmaf is not None)

    _, audio_desc = plan.audio_args()
    log(f"{src.name}: {human_size(info['size'])}, {info['width']}x{info['height']} {info['vcodec']} "
        f"{human_time(info['duration'])}, audio {info['acodec'] or 'none'}", quiet)
    log(f"  plan: {plan.describe(plan.crf)}, audio {audio_desc}"
        + (f", target {human_size(plan.target_size)}" if plan.target_size else ""), quiet)

    if args.dry_run:
        cmd = base_input_args(plan, src, plan.hwaccel) + plan.video_args(plan.crf) + plan.audio_args()[0] + output_common(plan, dest)
        if not args.json:
            print(" ".join(shlex.quote(c) for c in cmd))
        return {"input": str(src), "output": str(dest), "status": "dry-run", "command": cmd,
                "plan": plan.describe(plan.crf), "replaced": False}

    started = time.monotonic()
    crf = plan.crf
    attempts: list[dict[str, Any]] = []
    max_retries = 2 if min_vmaf is not None and not plan.target_size else 0
    tmp_dest = dest.with_name(dest.stem + ".part.mp4")
    trashed: Optional[str] = None
    try:
        for attempt in range(max_retries + 1):
            command = encode(plan, src, tmp_dest, crf, quiet)
            out_info = ffprobe(tmp_dest)
            record = {"crf": crf, "size": out_info["size"], "vmaf": None}
            if want_vmaf:
                record["vmaf"] = measure_vmaf(plan, src, tmp_dest, quiet)
            attempts.append(record)
            log(f"  attempt {attempt + 1}: {plan.describe(crf)} -> {human_size(out_info['size'])}"
                + (f", VMAF {record['vmaf']}" if record["vmaf"] is not None else ""), quiet)
            if min_vmaf is None or record["vmaf"] is None or record["vmaf"] >= min_vmaf:
                break
            if attempt == max_retries:
                log(f"  VMAF still below {min_vmaf} after {attempt + 1} attempts; keeping last result", quiet)
                break
            crf = crf - plan.crf_step
            log(f"  VMAF {record['vmaf']} < {min_vmaf}; re-encoding at {'q' if plan.fast else 'crf'}={crf}", quiet)

        elapsed = time.monotonic() - started
        out_info = ffprobe(tmp_dest)
        duration_diff = abs(out_info["duration"] - info["duration"])
        duration_ok = duration_diff <= max(0.5, info["duration"] * 0.01)
        ratio = out_info["size"] / info["size"] if info["size"] else 1.0
        status = "compressed"
        if not duration_ok:
            status = "duration-mismatch"
        elif out_info["size"] >= info["size"] and not args.force:
            status = "skipped-larger"

        if status != "compressed":
            tmp_dest.unlink(missing_ok=True)
            final_path = None
        else:
            if replace:
                trashed = move_to_trash(src, args.permanent)
                if trashed is None:
                    # Could not move the source aside: keep both files instead of losing work.
                    dest = default_output(src, None)
                    replace = False
                    log("  could not move the original to Trash; keeping both files "
                        "(re-run with --replace --permanent to delete it outright)", quiet)
            if dest.exists() and dest != src:
                dest.unlink()
            os.replace(tmp_dest, dest)
            final_path = dest
    except BaseException:
        tmp_dest.unlink(missing_ok=True)
        raise

    result = {
        "input": str(src),
        "output": str(final_path) if final_path else None,
        "status": status,
        "replaced": replace and status == "compressed",
        "original_moved_to": trashed,
        "input_size": info["size"],
        "output_size": out_info["size"],
        "ratio": round(ratio, 4),
        "saved_bytes": info["size"] - out_info["size"],
        "input_video": f"{info['width']}x{info['height']} {info['vcodec']} {info['pix_fmt']}",
        "output_video": f"{out_info['width']}x{out_info['height']} {out_info['vcodec']} {out_info['pix_fmt']}",
        "input_duration": round(info["duration"], 3),
        "output_duration": round(out_info["duration"], 3),
        "duration_ok": duration_ok,
        "codec": plan.codec,
        "encoder": "videotoolbox" if plan.fast else {"hevc": "libx265", "h264": "libx264", "av1": "libsvtav1"}[plan.codec],
        "quality": plan.quality,
        "crf": crf,
        "preset": plan.preset,
        "audio": audio_desc,
        "filters": plan.video_filters(),
        "vmaf": attempts[-1]["vmaf"] if attempts else None,
        "min_vmaf": min_vmaf,
        "attempts": attempts,
        "elapsed_s": round(elapsed, 1),
        "command": command,
        "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    summary = (f"  {status}: {human_size(info['size'])} -> {human_size(out_info['size'])} "
               f"({ratio * 100:.1f}%, saved {human_size(max(0, info['size'] - out_info['size']))}) in {human_time(elapsed)}")
    if result["vmaf"] is not None:
        summary += f", VMAF {result['vmaf']}"
    if status == "skipped-larger":
        summary += " | output discarded: source is already smaller (use --force to keep)"
    elif status == "duration-mismatch":
        summary += f" | output discarded: duration differs by {duration_diff:.2f}s"
    log(summary, quiet)
    if final_path:
        log(f"  -> {final_path}", quiet)
    if trashed:
        log(f"  original moved to {trashed}", quiet)
    return result


def move_to_trash(path: Path, permanent: bool) -> Optional[str]:
    """Move the source out of the way. Finder's Trash on macOS; permanent delete only when asked."""
    if permanent:
        path.unlink()
        return "deleted permanently"
    if platform.system() == "Darwin":
        escaped = str(path).replace("\\", "\\\\").replace('"', '\\"')
        script = f'tell application "Finder" to delete POSIX file "{escaped}"'
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False, timeout=60)
        if proc.returncode == 0 and not path.exists():
            return "Trash"
        # Finder may be unavailable in headless sessions; fall back to the home Trash (same volume only).
        home_trash = Path.home() / ".Trash"
        if home_trash.is_dir():
            target = home_trash / path.name
            counter = 1
            while target.exists():
                target = home_trash / f"{path.stem} {counter}{path.suffix}"
                counter += 1
            try:
                os.rename(path, target)
                return str(target)
            except OSError:
                return None
    return None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compress a video to the smallest size that still looks good (HEVC CRF 28 by default).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  compress_video.py talk.mov                       # -> talk-compressed.mp4\n"
            "  compress_video.py talk.mov --quality smallest    # crf 32, slow, 1080p cap, 64k audio\n"
            "  compress_video.py talk.mov --min-vmaf 90         # re-encode until VMAF >= 90\n"
            "  compress_video.py talk.mov --target-size 50M     # two-pass to fit 50 MB\n"
            "  compress_video.py talk.mov --codec h264          # maximum compatibility\n"
            "  compress_video.py *.MP4 --output-dir ~/out --fast  # VideoToolbox, much faster, larger\n"
        ),
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="video file(s) to compress")
    parser.add_argument("--output", "-o", type=Path, help="output file (single input only)")
    parser.add_argument("--output-dir", type=Path, help="folder for outputs (default: next to each input)")
    parser.add_argument("--quality", choices=QUALITIES, default=None,
                        help="smallest | small (default) | balanced | high")
    parser.add_argument("--crf", type=float, default=None, help="explicit CRF (or VideoToolbox -q:v with --fast)")
    parser.add_argument("--codec", choices=CODECS, default=None, help="hevc (default) | h264 | av1")
    parser.add_argument("--preset", default=None, help="x264/x265 preset, e.g. medium, slow, veryslow")
    parser.add_argument("--max-edge", type=int, default=None, help="cap the longer edge in pixels, e.g. 1080")
    parser.add_argument("--fps", type=float, default=None, help="cap the frame rate, e.g. 30")
    parser.add_argument("--audio-bitrate", type=parse_bitrate, default=None, help="AAC bitrate in kbit/s, e.g. 96k")
    parser.add_argument("--target-size", type=parse_size, default=None, help="two-pass encode to fit, e.g. 50M")
    parser.add_argument("--fast", action="store_true", help="use VideoToolbox hardware encoding (macOS; faster, larger)")
    parser.add_argument("--no-hwaccel", action="store_true", help="disable VideoToolbox hardware decoding")
    parser.add_argument("--vmaf", action="store_true", help="measure VMAF of the result against the source")
    parser.add_argument("--min-vmaf", type=float, default=None,
                        help="re-encode at a lower CRF (up to 2 retries) until VMAF reaches this score, e.g. 90")
    parser.add_argument("--replace", action="store_true",
                        help="replace mode: write <stem>.mp4 next to the source and move the original to Trash")
    parser.add_argument("--permanent", action="store_true",
                        help="with --replace: delete the original outright instead of moving it to Trash")
    parser.add_argument("--force", action="store_true", help="keep the output even if it is larger than the source")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output file")
    parser.add_argument("--dry-run", action="store_true", help="print the ffmpeg command and exit")
    parser.add_argument("--json", action="store_true", help="print a JSON result to stdout")
    parser.add_argument("--quiet", "-q", action="store_true", help="suppress progress and summaries on stderr")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output and len(args.inputs) > 1:
        raise SystemExit("--output accepts a single input; use --output-dir for several files")
    if args.permanent and not args.replace:
        raise SystemExit("--permanent only makes sense together with --replace")
    require_tool("ffmpeg")
    require_tool("ffprobe")
    records = read_profile_records()
    results = []
    failures = 0
    for src in args.inputs:
        try:
            results.append(compress_one(src, args, records))
        except (SystemExit, RuntimeError) as exc:
            failures += 1
            message = str(exc)
            log(f"{src}: FAILED: {message}", args.quiet)
            results.append({"input": str(src), "status": "failed", "error": message})
            if len(args.inputs) == 1:
                if args.json:
                    print(json.dumps({"schema": RESULT_SCHEMA, "results": results}, ensure_ascii=False, indent=2))
                return 1
    if args.json:
        print(json.dumps({"schema": RESULT_SCHEMA, "results": results}, ensure_ascii=False, indent=2))
    if len(results) > 1 and not args.quiet:
        saved = sum(r.get("saved_bytes", 0) for r in results if r.get("status") == "compressed")
        done = sum(1 for r in results if r.get("status") == "compressed")
        log(f"{done}/{len(results)} compressed, {failures} failed, saved {human_size(max(0, saved))}", args.quiet)
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)
