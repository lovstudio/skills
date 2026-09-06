#!/usr/bin/env python3
"""Index real video frames and package reviewed Moments photographs. No model calls."""
import argparse
import concurrent.futures
import hashlib
import html
import json
import math
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat
from photographic_color import camera_color, resolve_mode


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip()[-2000:] or "Command failed")
    return result.stdout


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def replace_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    temporary.replace(path)


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Time must be finite")
    return value


def seconds(value):
    parts = str(value).split(":")
    if len(parts) > 3:
        raise ValueError("Use seconds or HH:MM:SS.mmm")
    result = 0.0
    for part in parts:
        result = result * 60 + finite(part)
    if result < 0:
        raise ValueError("Time cannot be negative")
    return result


def stamp(value):
    ms = round(value * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def source_info(path):
    path = Path(path).expanduser().resolve(strict=True)
    data = json.loads(run(["ffprobe", "-v", "error", "-show_format",
                           "-show_streams", "-of", "json", str(path)]))
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if not video:
        raise ValueError("Input has no video stream")
    duration = finite(video.get("duration") or data["format"]["duration"])
    if duration <= 0:
        raise ValueError("Input duration must be positive")
    stat = path.stat()
    fingerprint = hashlib.sha256()
    with path.open("rb") as stream:
        fingerprint.update(stream.read(1024 * 1024))
        stream.seek(max(0, stat.st_size - 1024 * 1024))
        fingerprint.update(stream.read(1024 * 1024))
    return {"path": str(path), "name": path.name, "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns, "duration": duration,
            "edge_sha256": fingerprint.hexdigest(),
            "width": video["width"], "height": video["height"],
            "fps": video.get("avg_frame_rate"),
            "pix_fmt": video.get("pix_fmt", "unknown"),
            "color_range": video.get("color_range", "unknown"),
            "color_space": video.get("color_space", "unknown"),
            "color_primaries": video.get("color_primaries", "unknown"),
            "color_transfer": video.get("color_transfer", "unknown"),
            "rotation": next((s["rotation"] for s in video.get("side_data_list", [])
                              if "rotation" in s), video.get("tags", {}).get("rotate", 0)),
            "camera_color": camera_color(path),
            "has_audio": any(s["codec_type"] == "audio" for s in data["streams"])}


def new_directory(path):
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=False)
    return path


def frame(source, time, target, width=None):
    if not 0 <= time < source["duration"]:
        raise ValueError(f"Timestamp outside video: {time}")
    if target.exists():
        raise ValueError(f"Frame target exists: {target.name}")
    temporary = target.with_name(f".{target.stem}-{uuid.uuid4().hex}{target.suffix}")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-ss", str(time),
           "-i", source["path"], "-map", "0:v:0", "-frames:v", "1", "-an", "-sn"]
    if width:
        cmd += ["-vf", f"scale={width}:-2"]
    try:
        run(cmd + ["-q:v", "2", str(temporary)])
        with Image.open(temporary) as im:
            im.load()
            gray = im.convert("L").resize((9, 8))
            px = list(gray.getdata())
            bits = [px[y * 9 + x] > px[y * 9 + x + 1] for y in range(8) for x in range(8)]
            dhash = sum(int(bit) << i for i, bit in enumerate(bits))
            # Metrics guide review; they cannot identify a good expression or important idea.
            luma = round(ImageStat.Stat(im.convert("L")).mean[0], 2)
            size = list(im.size)
        temporary.rename(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"time": round(time, 3), "timecode": stamp(time), "file": str(target),
            "size": size, "luma": luma, "dhash": f"{dhash:016x}"}


def sheet(rows, target):
    # Diagnostic contact sheet only; final photographs are never retouched here.
    cell_w, cell_h, cols = 400, 255, 4
    canvas = Image.new("RGB", (cols * cell_w, math.ceil(len(rows) / cols) * cell_h), "#181818")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)
    for i, row in enumerate(rows):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        with Image.open(row["file"]) as im:
            im.thumbnail((cell_w - 8, cell_h - 30))
            canvas.paste(im, (x + (cell_w - im.width) // 2, y))
        draw.text((x + 8, y + cell_h - 27), row["timecode"], font=font, fill="white")
    canvas.save(target, quality=88)


def index(args):
    source = source_info(args.video)
    start = seconds(args.start)
    end = seconds(args.end) if args.end is not None else source["duration"]
    step = finite(args.every)
    if not 0 <= start < end <= source["duration"] or step <= 0:
        raise ValueError("Require 0 <= start < end <= duration and every > 0")
    times = [round(start + i * step, 3) for i in range(math.ceil((end - start) / step))]
    if len(times) > args.max_frames:
        raise ValueError(f"{len(times)} samples exceed max-frames={args.max_frames}")
    if args.resume:
        out = Path(args.output).expanduser().resolve(strict=True)
        old = read(out / "run.json")
        for key in ("bytes", "duration", "edge_sha256"):
            if source[key] != old["source"][key]:
                raise ValueError("Resume source differs from the indexed video")
        if old["times"] != times or old["width"] != args.width:
            raise ValueError("Resume sampling parameters differ")
    else:
        out = new_directory(args.output)
        (out / "frames").mkdir()
        write(out / "run.json", {"source": source, "times": times, "width": args.width})
    completed = read(out / "progress.json") if args.resume and (out / "progress.json").exists() else {}
    def one(time):
        cached = completed.get(str(time))
        if cached:
            existing = out / "frames" / Path(cached["file"]).name
            with Image.open(existing) as im:
                im.load()
            return dict(cached, file=str(existing))
        return frame(source, time, out / "frames" / f"frame-{round(time * 1000):010d}.jpg", args.width)
    rows, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(one, time): time for time in times}
        for future in concurrent.futures.as_completed(futures):
            time = futures[future]
            try:
                row = future.result()
                rows.append(row)
                completed[str(time)] = row
                replace_json(out / "progress.json", completed)
            except (ValueError, OSError) as exc:
                failures.append({"time": time, "error": str(exc)})
    rows.sort(key=lambda row: row["time"])
    pages = []
    for n in range(0, len(rows), 24):
        path = out / f"contact-{n // 24 + 1:02d}.jpg"
        sheet(rows[n:n+24], path)
        pages.append(path.name)
    for row in rows:
        row["file"] = str(Path(row["file"]).relative_to(out))
    result = {"schema": "video-moments-index/v1", "source": source,
              "status": "partial" if failures else "indexed", "failures": failures,
              "coverage": {"start": start, "end": end, "sample_interval": step,
                           "mode": "sparse-visual-sampling", "semantic_review": False},
              "frames": rows, "contact_sheets": pages}
    replace_json(out / "index.json", result)
    print(json.dumps({"index": str(out / "index.json"), "frames": len(rows), "pages": pages}))
    if failures:
        raise ValueError(f"{len(failures)} frame(s) failed; restore source and resume. First error: {failures[0]['error']}")


def extract(args):
    source = source_info(args.video)
    times = [seconds(value) for value in args.at]
    if len(set(times)) != len(times) or any(t >= source["duration"] for t in times):
        raise ValueError("Timestamps must be distinct and inside the source")
    out = new_directory(args.output)
    rows = []
    for i, time in enumerate(times, 1):
        path = out / f"{i:02d}-{stamp(time).replace(':', '-')}.png"
        row = frame(source, time, path)
        row.update({"file": path.name, "sha256": digest(path), "id": f"moment-{i:02d}"})
        rows.append(row)
    write(out / "frames.json", {"schema": "video-moments-frames/v1", "source": source, "frames": rows})
    print(json.dumps({"manifest": str(out / "frames.json"), "count": len(rows)}))


def checked_image(path):
    path = Path(path).expanduser().resolve(strict=True)
    with Image.open(path) as im:
        im.load()
        if im.mode not in ("RGB", "RGBA", "L"):
            raise ValueError(f"Convert non-RGB source before packaging: {path.name}")
        return path, list(im.size)


def photographic(args):
    """Explicitly selected local photographic path; never generates new scene content."""
    from photographic_color import decode_video, grade, normalized_frame, srgb_profile
    source_manifest = Path(args.frames_manifest).expanduser().resolve(strict=True)
    data = read(source_manifest)
    if data.get("schema") != "video-moments-frames/v1":
        raise ValueError("Use the manifest produced by extract")
    source = data["source"]
    video_path = Path(args.source_video or source.get("path", "")).expanduser()
    if video_path.is_file():
        fresh = source_info(video_path)
        for key in ("bytes", "duration", "edge_sha256"):
            if fresh[key] != source[key]:
                raise ValueError("Source video differs from the extracted frame manifest")
        source = fresh
    elif args.source_video:
        raise ValueError("--source-video does not exist")
    mode = resolve_mode(source, args.color_mode)
    if mode != "srgb" and not video_path.is_file():
        raise ValueError("Color restoration needs the original video; use --source-video if it moved")
    if mode != "srgb" and finite(source.get("rotation", 0)) % 360:
        raise ValueError("Rotated video needs an explicit geometry plan before source color decoding")
    parameters = {key: finite(getattr(args, key)) for key in
                  ("gamma", "brightness", "contrast", "red", "green", "blue", "saturation", "exposure")}
    if not (0.8 <= args.gamma <= 1.8 and -0.1 <= args.brightness <= 0.1 and
            0.8 <= args.contrast <= 1.2 and 0.7 <= args.red <= 1.3 and
            0.7 <= args.green <= 1.3 and 0.7 <= args.blue <= 1.3 and
            0.7 <= args.saturation <= 1.3 and -3 <= args.exposure <= 3):
        raise ValueError("Adjustments exceed the restrained photographic range")
    if args.long_edge < 320 or args.long_edge > 3840:
        raise ValueError("long-edge must be 320-3840")
    checked, ids, times = [], set(), set()
    for row in data["frames"]:
        identifier = row["id"]
        if (not isinstance(identifier, str) or not identifier or
                any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in identifier)
                or identifier in ids):
            raise ValueError("Frame IDs must be unique filename-safe identifiers")
        ids.add(identifier)
        time = finite(row["time"])
        if not 0 <= time < source["duration"] or time in times:
            raise ValueError("Frame times must be distinct and inside the source")
        times.add(time)
        raw, size = checked_image(source_manifest.parent / row["file"])
        if digest(raw) != row["sha256"]:
            raise ValueError("Original frame hash mismatch")
        checked.append((row, raw, size))
    if not checked:
        raise ValueError("Frame manifest is empty")
    if len(set(tuple(size) for _, _, size in checked)) != 1:
        raise ValueError("Mixed source aspect ratios need a reviewed crop plan")
    out = new_directory(args.output)
    results, icc = [], srgb_profile()
    for row, raw, size in checked:
        factor = min(1, args.long_edge / max(size))
        width, height = [max(2, round(x * factor / 2) * 2) for x in size]
        final = out / (row["id"] + ".jpg")
        if mode == "srgb":
            rgb, decoding = normalized_frame(raw), {"input": str(raw), "mode": "normalized-srgb-frame"}
        else:
            rgb, decoding = decode_video(source, row["time"], args.input_range)
            if list(rgb.shape[1::-1]) != size:
                raise ValueError("Decoded source geometry differs from the reviewed original")
        photo = grade(rgb, mode, parameters)
        if photo.size != (width, height):
            photo = photo.resize((width, height), Image.Resampling.LANCZOS)
        photo.save(final, quality=95, subsampling=0, icc_profile=icc)
        _, final_size = checked_image(final)
        with Image.open(final) as im:
            pixel_hash = hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()
        results.append({"id": row["id"], "time": row["time"], "file": final.name,
                        "sha256": digest(final), "pixel_sha256": pixel_hash,
                        "original_sha256": row["sha256"], "decoding": decoding,
                        "size": final_size, "edit_method": "photographic"})
    write(out / "edits.json", {"schema": "video-moments-edits/v1", "tool": "ffmpeg+numpy+pillow",
          "parameters": parameters, "long_edge": args.long_edge, "images": results,
          "source": source, "frames_manifest": str(source_manifest), "color_mode": mode,
          "output_color": "sRGB ICC, JPEG 95, 4:4:4, no EXIF",
          "status": "needs-visual-review", "color_note": "Source-aware deterministic grading; no generated detail"})
    print(json.dumps({"output": str(out), "count": len(results), "status": "needs-visual-review"}))


def validate_selection(data, parent):
    if data.get("schema") != "video-moments-selection/v1":
        raise ValueError("Expected video-moments-selection/v1")
    source = data.get("source", {})
    frames_path = (parent / data["frames_manifest"]).resolve(strict=True)
    frames = read(frames_path)
    if frames.get("schema") != "video-moments-frames/v1":
        raise ValueError("Source frame manifest must come from extract")
    for key in ("name", "duration"):
        if source.get(key) != frames["source"][key]:
            raise ValueError("Selection source differs from frame manifest")
    if data.get("selection_basis") not in ("visual", "audiovisual"):
        raise ValueError("Specify visual or audiovisual selection basis")
    duration = finite(source["duration"])
    if duration <= 0:
        raise ValueError("Invalid source duration")
    moments = data.get("moments", [])
    if not 1 <= len(moments) <= 9:
        raise ValueError("Selection must contain 1-9 genuinely distinct moments")
    ids, times, paths, sizes = set(), set(), set(), []
    for item in moments:
        identifier = item["id"]
        if identifier in ids:
            raise ValueError("Duplicate moment ID")
        ids.add(identifier)
        time = finite(item["time"])
        if not 0 <= time < duration or time in times:
            raise ValueError("Invalid or duplicate timestamp")
        times.add(time)
        for key in ("reason", "category", "evidence", "edit_method"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"Moment requires {key}")
        if item["edit_method"] not in ("imagegen", "photographic", "original"):
            raise ValueError("Unknown edit method")
        if item.get("quote") and not item.get("quote_verified"):
            raise ValueError("Quotation requires verified audio/transcript evidence")
        review = item.get("review", {})
        for key in ("source_match", "identity", "screen_text", "composition", "privacy"):
            if review.get(key) is not True:
                raise ValueError(f"Moment {identifier} needs explicit visual review: {key}")
        raw, _ = checked_image(parent / item["original"])
        final, size = checked_image(parent / item["final"])
        if raw == final and item["edit_method"] != "original":
            raise ValueError("Edited and source files must differ")
        if final in paths:
            raise ValueError("Final image is reused")
        paths.add(final)
        sizes.append(size)
        if digest(raw) != item["original_sha256"]:
            raise ValueError("Source frame hash mismatch")
        bound = next((row for row in frames["frames"] if row["time"] == time and
                      (frames_path.parent / row["file"]).resolve() == raw), None)
        if not bound or bound["sha256"] != item["original_sha256"]:
            raise ValueError("Timestamp and original image are not bound by the source frame manifest")
        if digest(final) != item["final_sha256"]:
            raise ValueError("Final image hash mismatch; repeat visual review after edits")
    if len(set(tuple(s) for s in sizes)) != 1:
        raise ValueError("Final images must have the same dimensions before packaging")
    return sizes[0]


def package(args):
    selection = Path(args.selection).expanduser().resolve(strict=True)
    data = read(selection)
    size = validate_selection(data, selection.parent)
    originals_only = all(item["edit_method"] == "original" for item in data["moments"])
    status = "originals-preview" if originals_only else "local-reviewed"
    out = new_directory(args.output)
    (out / "images").mkdir()
    cards, records, previews = [], [], []
    for i, item in enumerate(data["moments"], 1):
        final = (selection.parent / item["final"]).resolve()
        destination = out / "images" / f"{i:02d}{final.suffix.lower()}"
        shutil.copyfile(final, destination)
        rel = str(destination.relative_to(out))
        records.append({"order": i, "file": rel, "id": item["id"], "time": item["time"],
                        "timecode": stamp(item["time"]), "reason": item["reason"],
                        "category": item["category"], "edit_method": item["edit_method"],
                        "sha256": digest(destination), "bytes": destination.stat().st_size,
                        "size": size, "review": item["review"]})
        cards.append('<figure><img src="' + html.escape(rel, quote=True) + '"><figcaption>' +
                     f'{i:02d} · {stamp(item["time"])} · ' + html.escape(item["reason"]) + '</figcaption></figure>')
        previews.append({"file": str(destination), "timecode": f'{i:02d}  {stamp(item["time"])}'})
    sheet(previews, out / "overview.jpg")
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>课程现场照片</title><style>body{margin:32px;background:#f9f9f7;color:#181818;font:16px system-ui}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}figure{margin:0}img{width:100%}figcaption{line-height:1.6;margin:8px 0}</style><h1>课程现场照片</h1><p>按编号选择图片。时间码和筛选说明只用于本地审阅。</p><main>' + ''.join(cards) + '</main></html>'
    if originals_only:
        page = page.replace("<h1>课程现场照片</h1>", "<h1>课程现场照片 · 原帧预选</h1><p>以下为未经美化的原始帧。</p>")
    (out / "gallery.html").write_text(page, encoding="utf-8")
    write(out / "manifest.json", {"schema": "video-moments-package/v1", "status": status,
          "source_name": data["source"]["name"], "duration": data["source"]["duration"],
          "selection_basis": data.get("selection_basis", "visual"), "images": records})
    verify_directory(out)
    print(json.dumps({"output": str(out), "count": len(records), "size": size, "status": status}))


def verify_directory(out):
    data = read(out / "manifest.json")
    for row in data["images"]:
        path = (out / row["file"]).resolve(strict=True)
        if out.resolve() not in path.parents:
            raise ValueError("Package path escapes its directory")
        _, size = checked_image(path)
        if size != row["size"] or digest(path) != row["sha256"]:
            raise ValueError("Package image differs from manifest")
    return len(data["images"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("probe", help="Inspect input without copying it")
    p.add_argument("video")
    p = commands.add_parser("index", help="Build timecoded diagnostic contact sheets")
    p.add_argument("video")
    p.add_argument("--output", required=True)
    p.add_argument("--start", default="0")
    p.add_argument("--end")
    p.add_argument("--every", type=float, default=60)
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--max-frames", type=int, default=600)
    p.add_argument("--workers", type=int, choices=range(1, 5), default=2)
    p.add_argument("--resume", action="store_true")
    p = commands.add_parser("extract", help="Extract unretouched full-resolution originals")
    p.add_argument("video")
    p.add_argument("--at", nargs="+", required=True)
    p.add_argument("--output", required=True)
    p = commands.add_parser("package", help="Copy and verify already standardized, visually reviewed images")
    p.add_argument("selection")
    p.add_argument("--output", required=True)
    p = commands.add_parser("photographic", help="Explicit local photo corrections, no generative edits")
    p.add_argument("frames_manifest")
    p.add_argument("--output", required=True)
    p.add_argument("--long-edge", type=int, default=1920)
    p.add_argument("--color-mode", choices=("auto", "srgb", "bt709", "slog3-sgamut3cine"), default="auto")
    p.add_argument("--source-video", help="Relocated original; source fingerprint must still match")
    p.add_argument("--input-range", choices=("pc", "tv"), help="Explicit range when source metadata is unknown")
    p.add_argument("--exposure", type=float, default=0.0, help="Exposure adjustment in stops, after color restoration")
    p.add_argument("--gamma", type=float, default=1.0)
    p.add_argument("--brightness", type=float, default=0.0)
    p.add_argument("--contrast", type=float, default=1.0)
    p.add_argument("--red", type=float, default=1.0)
    p.add_argument("--green", type=float, default=1.0)
    p.add_argument("--blue", type=float, default=1.0)
    p.add_argument("--saturation", type=float, default=1.0)
    p = commands.add_parser("verify", help="Read actual package pixels and verify SHA-256")
    p.add_argument("directory")
    args = parser.parse_args()
    try:
        if args.command == "probe":
            print(json.dumps(source_info(args.video), ensure_ascii=False, indent=2))
        elif args.command == "index":
            if args.width < 64 or args.width > 1920 or args.max_frames < 1:
                raise ValueError("Invalid thumbnail width or frame limit")
            index(args)
        elif args.command == "extract":
            extract(args)
        elif args.command == "package":
            package(args)
        elif args.command == "photographic":
            photographic(args)
        else:
            print(json.dumps({"verified": verify_directory(Path(args.directory))}))
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"video-moments: {exc}\n")


if __name__ == "__main__":
    main()
