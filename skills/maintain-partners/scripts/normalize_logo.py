#!/usr/bin/env python3
"""Trim transparent edges and resize a logo to a fixed canvas height.

Standard for the Skill Publisher partners strip: 80px tall, width auto, optimized PNG.
Optionally invert white-on-transparent logos to black so they remain visible
against the light grayscale strip.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Missing dependency: pip install Pillow --break-system-packages")


def detect_white_on_transparent(img: "Image.Image", threshold: int = 200) -> bool:
    """True if the average opaque pixel is near-white (logo invisible on white bg)."""
    px = img.load()
    rs, gs, bs, n = 0, 0, 0, 0
    step_y = max(1, img.height // 50)
    step_x = max(1, img.width // 50)
    for y in range(0, img.height, step_y):
        for x in range(0, img.width, step_x):
            r, g, b, a = px[x, y]
            if a > 128:
                rs += r
                gs += g
                bs += b
                n += 1
    if not n:
        return False
    return (rs // n) > threshold and (gs // n) > threshold and (bs // n) > threshold


def whiten_to_transparent(img: "Image.Image", threshold: int = 245) -> "Image.Image":
    """JPEG inputs have white backgrounds; convert near-white to transparent for tight crop."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if r > threshold and g > threshold and b > threshold:
                px[x, y] = (255, 255, 255, 0)
    return img


def invert_rgb_keep_alpha(img: "Image.Image") -> "Image.Image":
    """Invert color channels but preserve alpha — turns white-on-transparent into black-on-transparent."""
    r, g, b, a = img.split()
    inv = ImageOps.invert(Image.merge("RGB", (r, g, b)))
    ir, ig, ib = inv.split()
    return Image.merge("RGBA", (ir, ig, ib, a))


def selective_white_to_black(img: "Image.Image") -> "Image.Image":
    """Turn only near-white pixels black; preserve colored content (e.g. blue icon, white wordmark)."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a > 0 and r > 200 and g > 200 and b > 200:
                px[x, y] = (0, 0, 0, a)
    return img


def normalize(src: Path, dst: Path, height: int, invert_mode: str) -> tuple[int, int]:
    img = Image.open(src).convert("RGBA")

    if src.suffix.lower() in (".jpg", ".jpeg"):
        img = whiten_to_transparent(img)

    if invert_mode == "auto":
        if detect_white_on_transparent(img):
            invert_mode = "full"
        else:
            invert_mode = "off"

    if invert_mode == "full":
        img = invert_rgb_keep_alpha(img)
    elif invert_mode == "selective":
        img = selective_white_to_black(img)

    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    w, h = img.size
    new_w = int(w * height / h)
    img = img.resize((new_w, height), Image.LANCZOS)

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, optimize=True)
    return new_w, height


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, help="Source image path (PNG/JPG/SVG-rasterized)")
    ap.add_argument("--dst", required=True, help="Output PNG path")
    ap.add_argument("--height", type=int, default=80, help="Target content height in pixels (default: 80)")
    ap.add_argument(
        "--invert",
        choices=["auto", "off", "full", "selective"],
        default="auto",
        help="auto: detect white-on-transparent and full-invert; "
        "selective: only flip near-white pixels to black (preserves colored icons); "
        "off: no inversion",
    )
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    dst = Path(args.dst).expanduser()
    if not src.exists():
        sys.exit(f"src not found: {src}")

    w, h = normalize(src, dst, args.height, args.invert)
    print(f"{dst}: {w}x{h}")


if __name__ == "__main__":
    main()
