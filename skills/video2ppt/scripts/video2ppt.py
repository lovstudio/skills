#!/usr/bin/env python3
"""Extract a deduplicated slide deck from a local video.

Port of the video2ppt desktop pipeline:
1. ffprobe reads the duration.
2. ffmpeg samples the (optionally trimmed and cropped) video at --fps.
3. Each frame gets a 16-bin per-channel RGB histogram; a frame starts a new
   segment when its histogram intersection with the last segment start is
   below --similarity.
4. One frame per segment is written as PNG and packed into PDF and PPTX.

`pack` rebuilds the PDF/PPTX after slides are dropped during review.
Requires ffmpeg/ffprobe on PATH and Pillow; python-pptx only for pptx output.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BINS = 16
THUMB_W = 160
METHODS = ("hist", "pixel")
FORMATS = ("png", "pdf", "pptx")
PDF_DPI = 300
MANIFEST = "manifest.json"

# 5x7 bitmap glyphs (MSB = left column), identical to the desktop app.
GLYPHS = {
    "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    "2": [0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111],
    "3": [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
    "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    "5": [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    "6": [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    "7": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    ":": [0b00000, 0b00100, 0b00100, 0b00000, 0b00100, 0b00100, 0b00000],
}


class CliError(Exception):
    pass


def parse_time(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return float(value)
    parts = value.split(":")
    if not 2 <= len(parts) <= 3 or not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        raise CliError(f"invalid time '{value}', use HH:MM:SS, MM:SS or seconds")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def parse_indices(spec: str) -> set[int]:
    out: set[int] = set()
    for part in filter(None, (p.strip() for p in spec.split(","))):
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not match:
            raise CliError(f"invalid index '{part}', use e.g. 3,7-9")
        lo, hi = int(match.group(1)), int(match.group(2) or match.group(1))
        out.update(range(min(lo, hi), max(lo, hi) + 1))
    return out


def format_hms(total: float) -> str:
    total = int(max(total, 0.0))
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"


def require_tool(name: str) -> None:
    if not shutil.which(name):
        raise CliError(f"{name} not found on PATH; install ffmpeg (macOS: brew install ffmpeg)")


def require_pillow():
    try:
        from PIL import Image
    except ImportError as exc:
        raise CliError("Pillow is required: python3 -m pip install pillow") from exc
    return Image


def probe(input_path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=duration:stream=width,height", "-of", "json", str(input_path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise CliError(f"ffprobe failed: {out.stderr.strip()}")
    data = json.loads(out.stdout or "{}")
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration <= 0:
        raise CliError("could not determine video duration")
    stream = (data.get("streams") or [{}])[0]
    return {"duration_sec": duration, "width": stream.get("width"), "height": stream.get("height")}


def sample_frames(input_path: Path, start: float, end: float, fps: float,
                  crop: str | None, out_dir: Path) -> list[Path]:
    vf = f"fps={fps}" + (f",crop={crop}" if crop else "")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", str(input_path),
        "-vf", vf, str(out_dir / "frame_%06d.png"),
    ]
    result = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if result.returncode != 0:
        raise CliError(f"ffmpeg exited with {result.returncode}: {result.stderr.strip()}")
    return sorted(out_dir.glob("frame_*.png"))


def fingerprint(image, method: str = "hist"):
    if method == "pixel":
        # Layout-aware: catches text/diagram changes on same-colour slides that histograms miss.
        return image.convert("L").resize((THUMB_W, max(1, round(THUMB_W * image.height / image.width))))
    hist = image.histogram()  # 256 counts per channel for RGB
    pixels = image.width * image.height or 1
    step = 256 // BINS
    return [
        [sum(hist[c * 256 + b * step: c * 256 + (b + 1) * step]) / pixels for b in range(BINS)]
        for c in range(3)
    ]


def similarity(a, b) -> float:
    if isinstance(a, list):
        total = sum(min(x, y) for ca, cb in zip(a, b) for x, y in zip(ca, cb))
        return max(0.0, min(1.0, total / 3.0))
    from PIL import ImageChops, ImageStat

    return 1.0 - ImageStat.Stat(ImageChops.difference(a, b)).mean[0] / 255.0


def segment(fps_list: list, threshold: float) -> list[tuple[int, int, float | None]]:
    """Original keep rule: a frame opens a segment when it differs from the last opener."""
    starts: list[tuple[int, float | None]] = []
    last = None
    for i, fp in enumerate(fps_list):
        score = None if last is None else similarity(fp, last)
        if score is None or score < threshold:
            starts.append((i, score))
            last = fp
    bounds = [s for s, _ in starts[1:]] + [len(fps_list)]
    return [(s, e, score) for (s, score), e in zip(starts, bounds)]


def steadiest(fps_list: list, start: int, end: int, window: int) -> int:
    """Within the first `window` frames of a segment, pick the one most similar to its successor,
    which skips frames caught mid-crossfade."""
    best, best_score = start, -1.0
    for j in range(start, min(start + max(window, 1), end)):
        nxt = j + 1 if j + 1 < len(fps_list) else j - 1
        score = similarity(fps_list[j], fps_list[nxt]) if nxt >= 0 else 1.0
        if score > best_score:
            best, best_score = j, score
    return best


def burn_timestamp(image, text: str) -> None:
    scale = max(image.height // 90, 2)
    pad = 4 * scale
    char_w, char_h = 5 * scale, 7 * scale
    text_w = char_w * len(text) + max(len(text) - 1, 0) * scale
    panel_w, panel_h = text_w + pad * 2, char_h + pad * 2
    if panel_w > image.width or panel_h > image.height:
        return
    y0 = image.height - panel_h
    box = (0, y0, panel_w, image.height)
    image.paste(image.crop(box).point(lambda v: v // 3), box)
    px = image.load()
    for i, ch in enumerate(text):
        rows = GLYPHS.get(ch)
        if rows is None:
            continue
        cx = pad + (char_w + scale) * i
        for r, bits in enumerate(rows):
            for col in range(5):
                if (bits >> (4 - col)) & 1:
                    for dy in range(scale):
                        for dx in range(scale):
                            px[cx + col * scale + dx, y0 + pad + r * scale + dy] = (255, 255, 255)


def write_pdf(paths: list[Path], target: Path) -> None:
    Image = require_pillow()
    images = [Image.open(p).convert("RGB") for p in paths]
    images[0].save(target, "PDF", save_all=True, append_images=images[1:], resolution=PDF_DPI)


def write_pptx(frames: list[dict], frame_dir: Path, target: Path) -> None:
    try:
        from pptx import Presentation
        from pptx.util import Emu
    except ImportError as exc:
        raise CliError("pptx output needs python-pptx: python3 -m pip install python-pptx") from exc
    Image = require_pillow()

    width_px, height_px = Image.open(frame_dir / frames[0]["file"]).size
    slide_w = Emu(12192000)  # 13.333in, the standard widescreen width
    slide_h = Emu(round(12192000 * height_px / width_px))
    deck = Presentation()
    deck.slide_width, deck.slide_height = slide_w, slide_h
    blank = deck.slide_layouts[6]
    for frame in frames:
        slide = deck.slides.add_slide(blank)
        slide.shapes.add_picture(str(frame_dir / frame["file"]), 0, 0, width=slide_w, height=slide_h)
        slide.notes_slide.notes_text_frame.text = frame["timestamp"]
    deck.save(target)


def write_contact_sheet(frames: list[dict], frame_dir: Path, target: Path,
                        columns: int = 6, thumb_w: int = 320) -> None:
    Image = require_pillow()
    from PIL import ImageDraw

    first = Image.open(frame_dir / frames[0]["file"])
    thumb_h = round(thumb_w * first.height / first.width)
    label_h = 22
    rows = math.ceil(len(frames) / columns)
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(frames):
        x, y = (i % columns) * thumb_w, (i // columns) * (thumb_h + label_h)
        thumb = Image.open(frame_dir / frame["file"]).convert("RGB").resize((thumb_w, thumb_h))
        sheet.paste(thumb, (x, y))
        draw.text((x + 4, y + thumb_h + 4), f"#{frame['index']}  {frame['timestamp']}", fill="black")
    sheet.save(target, quality=85)


def export(report: dict, out_dir: Path) -> dict:
    frames = report["frames"]
    if not frames:
        raise CliError("no frames were kept; nothing to export")
    frame_dir = out_dir / "frames"
    name, formats = report["params"]["name"], report["params"]["formats"]
    outputs = {"frames_dir": str(frame_dir)}
    if "pdf" in formats:
        write_pdf([frame_dir / f["file"] for f in frames], out_dir / f"{name}.pdf")
        outputs["pdf"] = str(out_dir / f"{name}.pdf")
    if "pptx" in formats:
        write_pptx(frames, frame_dir, out_dir / f"{name}.pptx")
        outputs["pptx"] = str(out_dir / f"{name}.pptx")
    if report["params"].get("contact_sheet", True):
        write_contact_sheet(frames, frame_dir, out_dir / "contact-sheet.jpg")
        outputs["contact_sheet"] = str(out_dir / "contact-sheet.jpg")
    outputs["manifest"] = str(out_dir / MANIFEST)
    report["frames_kept"] = len(frames)
    report["outputs"] = outputs
    (out_dir / MANIFEST).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def cmd_extract(args: argparse.Namespace) -> dict:
    Image = require_pillow()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        raise CliError(f"input video not found: {input_path}")
    formats = [f.strip() for f in args.format.split(",") if f.strip()]
    unknown = sorted(set(formats) - set(FORMATS))
    if unknown or not formats:
        raise CliError(f"unknown format {unknown}; choose from {','.join(FORMATS)}")
    if not 0 < args.similarity <= 1:
        raise CliError("--similarity must be in (0, 1]")
    if args.crop and not re.fullmatch(r"\d+:\d+:\d+:\d+", args.crop):
        raise CliError("--crop must be W:H:X:Y in pixels, e.g. 981:551:288:11")
    require_tool("ffmpeg")
    require_tool("ffprobe")

    out_dir = Path(args.output).expanduser().resolve()
    name = args.name or input_path.stem
    frame_dir = out_dir / "frames"
    occupied = [p for p in (frame_dir, out_dir / f"{name}.pdf", out_dir / f"{name}.pptx") if p.exists()]
    if occupied and not args.overwrite:
        raise CliError(f"output already exists: {occupied[0]} (pass --overwrite to replace)")

    started = time.time()
    info = probe(input_path)
    start = max(parse_time(args.start) or 0.0, 0.0)
    end = min(parse_time(args.end) or info["duration_sec"], info["duration_sec"])
    if end <= start:
        raise CliError(f"empty time range: {start}..{end}")
    fps = max(0.1, min(args.fps, 30.0))

    print(f"[video2ppt] sampling {format_hms(start)}-{format_hms(end)} at {fps} fps", file=sys.stderr)
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True)

    frames: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="video2ppt-") as tmp:
        sampled = sample_frames(input_path, start, end, fps, args.crop, Path(tmp))
        if not sampled:
            raise CliError("ffmpeg produced no frames; check --start/--end/--crop")
        fps_list = []
        for idx, path in enumerate(sampled):
            fps_list.append(fingerprint(Image.open(path).convert("RGB"), args.method))
            if idx % 120 == 0:
                print(f"[video2ppt] fingerprinted {format_hms(start + idx / fps)}", file=sys.stderr)

        window = round(args.settle * fps)
        for seg_start, seg_end, score in segment(fps_list, args.similarity):
            if (seg_end - seg_start) / fps < args.min_duration:
                continue
            pick = steadiest(fps_list, seg_start, seg_end, window) if window > 0 else seg_start
            ts = start + pick / fps
            image = Image.open(sampled[pick]).convert("RGB")
            if args.add_timestamp:
                burn_timestamp(image, format_hms(ts))
            stem = f"timestamp_{format_hms(ts).replace(':', '-')}"
            file_name = f"{stem}.png" if not (frame_dir / f"{stem}.png").exists() else f"{stem}_{pick:06d}.png"
            image.save(frame_dir / file_name)
            frames.append({
                "index": len(frames) + 1,
                "timestamp_sec": round(ts, 3),
                "timestamp": format_hms(ts),
                "segment": [format_hms(start + seg_start / fps), format_hms(start + seg_end / fps)],
                "similarity_to_previous": None if score is None else round(score, 4),
                "file": file_name,
            })

    report = {
        "status": "ok",
        "input": str(input_path),
        "video": info,
        "params": {"name": name, "formats": formats, "method": args.method,
                   "similarity": args.similarity, "fps": fps,
                   "start_sec": start, "end_sec": end, "crop": args.crop, "settle": args.settle,
                   "min_duration": args.min_duration, "add_timestamp": args.add_timestamp,
                   "contact_sheet": not args.no_contact_sheet},
        "frames_sampled": len(sampled),
        "frames": frames,
    }
    report = export(report, out_dir)
    report["elapsed_sec"] = round(time.time() - started, 2)
    return report


def grab_frame(report: dict, frame_dir: Path, ts: float) -> dict:
    """Pull one frame the segmenter skipped (e.g. an embedded demo) with the same crop/overlay."""
    Image = require_pillow()
    require_tool("ffmpeg")
    input_path = Path(report["input"])
    if not input_path.is_file():
        raise CliError(f"source video no longer at {input_path}; cannot --add")
    if not 0 <= ts <= report["video"]["duration_sec"]:
        raise CliError(f"--add time {format_hms(ts)} is outside the video")
    params = report["params"]
    file_name = f"timestamp_{format_hms(ts).replace(':', '-')}.png"
    if (frame_dir / file_name).exists():
        raise CliError(f"slide at {format_hms(ts)} already exists")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
           "-ss", f"{ts:.3f}", "-i", str(input_path), "-frames:v", "1"]
    if params.get("crop"):
        cmd += ["-vf", f"crop={params['crop']}"]
    result = subprocess.run(cmd + [str(frame_dir / file_name)], stdin=subprocess.DEVNULL,
                            capture_output=True, text=True)
    if result.returncode != 0 or not (frame_dir / file_name).exists():
        raise CliError(f"ffmpeg could not grab {format_hms(ts)}: {result.stderr.strip()}")
    if params.get("add_timestamp"):
        image = Image.open(frame_dir / file_name).convert("RGB")
        burn_timestamp(image, format_hms(ts))
        image.save(frame_dir / file_name)
    return {"index": 0, "timestamp_sec": round(ts, 3), "timestamp": format_hms(ts),
            "segment": None, "similarity_to_previous": None, "file": file_name, "added": True}


def cmd_pack(args: argparse.Namespace) -> dict:
    out_dir = Path(args.output).expanduser().resolve()
    manifest = out_dir / MANIFEST
    if not manifest.is_file():
        raise CliError(f"no {MANIFEST} in {out_dir}; run extract first")
    report = json.loads(manifest.read_text(encoding="utf-8"))
    drop = parse_indices(args.drop or "")
    known = {f["index"] for f in report["frames"]}
    if drop - known:
        raise CliError(f"unknown slide index {sorted(drop - known)}; valid 1..{len(known)}")

    dropped_dir = out_dir / "dropped"
    kept = []
    for frame in report["frames"]:
        if frame["index"] in drop:
            dropped_dir.mkdir(exist_ok=True)
            shutil.move(str(out_dir / "frames" / frame["file"]), str(dropped_dir / frame["file"]))
            report.setdefault("dropped", []).append(frame)
        else:
            kept.append(frame)
    for spec in filter(None, (s.strip() for s in (args.add or "").split(","))):
        kept.append(grab_frame(report, out_dir / "frames", parse_time(spec)))
    kept.sort(key=lambda f: f["timestamp_sec"])
    for i, frame in enumerate(kept, 1):
        frame["index"] = i
    report["frames"] = kept
    if args.format:
        report["params"]["formats"] = [f.strip() for f in args.format.split(",") if f.strip()]
    if args.name:
        report["params"]["name"] = args.name
    return export(report, out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract a deduplicated slide deck (PNG/PDF/PPTX) from a video.")
    sub = parser.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("extract", help="sample a video and export unique slides")
    ex.add_argument("input", help="local video file")
    ex.add_argument("output", help="output directory")
    ex.add_argument("--format", default="png,pdf,pptx",
                    help="comma list of png,pdf,pptx (frames are always kept as PNG)")
    ex.add_argument("--similarity", type=float, default=0.6,
                    help="start a new slide when similarity to the last slide is below this (0-1]; default 0.6")
    ex.add_argument("--method", choices=METHODS, default="hist",
                    help="hist = RGB histogram (desktop app default); pixel = downscaled grayscale "
                         "difference, better for same-colour slides")
    ex.add_argument("--fps", type=float, default=1.0, help="sampling rate, 0.1-30 (default 1)")
    ex.add_argument("--start", help="start time, HH:MM:SS or seconds")
    ex.add_argument("--end", help="end time, HH:MM:SS or seconds")
    ex.add_argument("--crop", help="W:H:X:Y pixel region used for both comparison and output")
    ex.add_argument("--settle", type=float, default=0.0,
                    help="seconds at the start of each slide to search for the steadiest frame (0 = first frame)")
    ex.add_argument("--min-duration", type=float, default=0.0,
                    help="drop slides shown for fewer seconds than this (filters crossfade frames)")
    ex.add_argument("--add-timestamp", action="store_true", help="burn HH:MM:SS into each slide")
    ex.add_argument("--name", help="base file name for pdf/pptx (default: video file stem)")
    ex.add_argument("--overwrite", action="store_true", help="replace existing outputs")
    ex.add_argument("--no-contact-sheet", action="store_true", help="skip contact-sheet.jpg")
    ex.add_argument("--json", action="store_true", help="print the report as JSON on stdout")

    pk = sub.add_parser("pack", help="drop/add reviewed slides and rebuild pdf/pptx from manifest.json")
    pk.add_argument("output", help="output directory produced by extract")
    pk.add_argument("--drop", help="1-based slide indices to drop, e.g. 3,7-9 (moved to dropped/)")
    pk.add_argument("--add", help="comma list of times (HH:MM:SS) to grab from the source video")
    pk.add_argument("--format", help="override formats, comma list of png,pdf,pptx")
    pk.add_argument("--name", help="override base file name")
    pk.add_argument("--json", action="store_true", help="print the report as JSON on stdout")

    args = parser.parse_args(argv)
    try:
        report = cmd_extract(args) if args.command == "extract" else cmd_pack(args)
    except CliError as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({k: v for k, v in report.items() if k not in ("frames", "dropped")},
                         ensure_ascii=False, indent=2))
    else:
        print(f"kept {report['frames_kept']} slides")
        for key, value in report["outputs"].items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
