#!/usr/bin/env python3
"""Prepare the real-person sticker: grab a video frame and/or crop a square around the face.

Examples:
  prep_photo.py --video clip.mp4 --time 00:12:03.5 --out frame.png
  prep_photo.py --image frame.png --crop 280,620,520,520 --out photo-crop.jpg
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", type=Path)
    src.add_argument("--image", type=Path)
    ap.add_argument("--time", default="0", help="Timestamp for --video (ffmpeg -ss syntax)")
    ap.add_argument("--crop", help="x,y,w,h in source pixels")
    ap.add_argument("--max-edge", type=int, default=1200)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    from PIL import Image
    tmp = None
    if args.video:
        if not shutil.which("ffmpeg"):
            sys.exit("ffmpeg is required for --video")
        tmp = Path(tempfile.mkdtemp(prefix="lookalike-frame-")) / "frame.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", args.time, "-i", str(args.video),
                        "-frames:v", "1", str(tmp)], check=True)
        img = Image.open(tmp)
    else:
        img = Image.open(args.image)
    img = img.convert("RGB")
    if args.crop:
        x, y, w, h = (int(v) for v in args.crop.split(","))
        img = img.crop((x, y, x + w, y + h))
    img.thumbnail((args.max_edge, args.max_edge))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.out, quality=92)
    if tmp:
        shutil.rmtree(tmp.parent, ignore_errors=True)
    print(json.dumps({"out": str(args.out), "size": list(img.size)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
