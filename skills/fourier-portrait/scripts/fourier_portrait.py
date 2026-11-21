#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=1.26",
#   "opencv-python-headless>=4.9",
#   "scipy>=1.11",
#   "skia-python>=87.6",
#   "matplotlib>=3.8",
# ]
# ///
"""Photo -> line art -> Fourier epicycles -> vertical MP4.

  uv run fourier_portrait.py --photo selfie.heic --out portrait.mp4 --title "..." --logo logo.png
  uv run fourier_portrait.py --photo selfie.jpg --workdir work --stills-only    # QC stills only

Work files land in --workdir: input.png, mask.png, lineart.png, photo_cutout.png, path.npy,
stills/, stills_sheet.jpg, video_sheet.jpg and report.json.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import fourier  # noqa: E402
import lineart  # noqa: E402
import render  # noqa: E402


def contact_sheet(inputs, out, *, cols, rows, fps_filter=""):
    vf = f"{fps_filter}scale=270:-1,tile={cols}x{rows}:padding=4:color=gray"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-vf", vf, "-frames:v", "1", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photo", required=True, type=Path)
    ap.add_argument("--out", type=Path, help="output .mp4 (omit with --stills-only)")
    ap.add_argument("--workdir", type=Path, default=Path("fourier-work"))
    ap.add_argument("--mode", choices=["xy", "complex"], default="xy",
                    help="xy: two real series, chains on top and left (default); complex: one chain")
    ap.add_argument("--title", default="", help="title shown at the top; empty for none")
    ap.add_argument("--logo", type=Path, help="light logo PNG shown above the bottom safe area")
    ap.add_argument("--font", default="Songti SC", help="font family for the title (needs CJK glyphs)")
    ap.add_argument("--crop", default="auto", help="auto (face-based bust) | full | x0,y0,x1,y1 fractions")
    ap.add_argument("--block", type=int, default=35, help="adaptive threshold block size (odd)")
    ap.add_argument("--offset", type=int, default=8, help="adaptive threshold offset; higher = less ink")
    ap.add_argument("--blur", type=float, default=2.0)
    ap.add_argument("--min-area", type=int, default=60, help="drop ink specks smaller than this (px)")
    ap.add_argument("--points", type=int, default=8192, help="samples along the path")
    ap.add_argument("--stages", default="1,2,4,8,16,32,64,128,256,512,1024")
    ap.add_argument("--stage-seconds", default="1.4,1.4,1.6,1.8,2.0,2.4,2.8,3.2,3.8,4.4,5.4")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--stills-only", action="store_true", help="render QC stills, skip the video")
    a = ap.parse_args()

    stages = [int(v) for v in a.stages.split(",")]
    secs = [float(v) for v in a.stage_seconds.split(",")]
    if len(stages) != len(secs):
        ap.error("--stages and --stage-seconds need the same number of entries")
    if not a.stills_only and not a.out:
        ap.error("--out is required unless --stills-only")
    if a.block % 2 == 0:
        ap.error("--block must be odd")
    if not a.photo.is_file():
        ap.error(f"photo not found: {a.photo}")
    if a.logo and not a.logo.is_file():
        ap.error(f"logo not found: {a.logo}")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")

    t0 = time.time()
    ink, cutout, meta = lineart.make_lineart(a.photo, a.workdir, crop=a.crop, block=a.block, offset=a.offset,
                                             blur=a.blur, min_area=a.min_area)
    path = fourier.order_contours(ink)
    z = fourier.resample(path, a.points)
    np.save(a.workdir / "path.npy", z)
    sp = fourier.spectrum(z, a.mode)
    print(f"[lineart] segmented={meta['segmented']} faces={len(meta['faces'])} crop={meta['crop']}")
    print(f"[fourier] {len(path)} contour points -> {a.points} samples, mode={a.mode}")

    style = render.Style(fps=a.fps, title=a.title, logo=a.logo, font_family=a.font,
                         stages=stages, stage_seconds=secs)
    scene = render.Scene(z, sp, ink, cutout, style)
    for n, e in zip(stages, scene.errors):
        print(f"  N={n:<5d} error={e * 100:.2f}%")
    print(f"  r_k ~ k^-{scene.decay:.2f}")

    end = scene.draw_end
    still_times = [0.8, 2.0, 2.9] + [float(s + d * 0.6) for s, d in zip(scene.stage_start, secs)][::2] + \
                  [end + 0.3, end + 1.2, scene.duration - 0.1]
    out = None if a.stills_only else a.out
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
    render.render(scene, out, stills_dir=a.workdir / "stills", still_times=still_times)
    contact_sheet(["-pattern_type", "glob", "-i", str(a.workdir / "stills" / "still_*.png")],
                  a.workdir / "stills_sheet.jpg", cols=6, rows=2)

    report = {"photo": str(a.photo), "mode": a.mode, "lineart": meta, "points": a.points,
              "stages": [{"n": n, "seconds": s, "error": round(e, 6)} for n, s, e in zip(stages, secs, scene.errors)],
              "decay_exponent": round(scene.decay, 3), "duration": round(scene.duration, 2), "fps": a.fps,
              "audio": "none (silent video; add music in an editing step)",
              "output": str(out) if out else None, "stills_sheet": str(a.workdir / "stills_sheet.jpg")}
    if out:
        contact_sheet(["-i", str(out)], a.workdir / "video_sheet.jpg", cols=8, rows=2,
                      fps_filter=f"fps={16 / scene.duration:.4f},")
        report["video_sheet"] = str(a.workdir / "video_sheet.jpg")
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration,size:stream=codec_name,width,height,nb_frames",
                                "-of", "json", str(out)], capture_output=True, text=True)
        report["ffprobe"] = json.loads(probe.stdout or "{}")
    report["elapsed_seconds"] = round(time.time() - t0, 1)
    (a.workdir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"[done] {report['elapsed_seconds']}s, report: {a.workdir / 'report.json'}")


if __name__ == "__main__":
    main()
