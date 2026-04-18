#!/usr/bin/env python3
"""Apply brand logo (and optional QR code) to generated slide images.

Designed to solve real-world pain points:
- AI-drawn page borders/cards clash with a composited logo
- Logo sits inside an AI-drawn frame → looks broken
- Need consistent branding without re-generating every slide

Usage:
    python3 apply-branding.py <slide-deck-dir> \\
        --logo /path/to/logo.png \\
        [--skip 1,N]  [--logo-h 56] [--pad-top 18] [--pad-right 24]
        [--qr /path/to/qr.png --qr-slide 23 --qr-box X1,Y1,X2,Y2]
        [--patch-slides 7,15,18,20]  [--frame-slides 2,21]

Destructive-safe: originals are copied to <deck>/_original/ on first run.
Idempotent: re-running rebuilds output from _original/.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def parse_int_set(s: str) -> set[int]:
    if not s:
        return set()
    return {int(x.strip()) for x in s.split(",") if x.strip()}


def parse_box(s: str) -> tuple[int, int, int, int]:
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 4:
        raise ValueError("box must be X1,Y1,X2,Y2")
    return tuple(parts)  # type: ignore


def strip_frame(img: Image.Image, border_px: int = 40) -> Image.Image:
    """Overwrite the 4 edge strips with a clean paper tile sampled from the
    interior. Picks a tile with the lowest luminance variance to avoid
    tiling text/lines across the edges.
    """
    w, h = img.size
    b = border_px
    tile_w, tile_h = 60, 60

    candidates = []
    for cy in range(b + 10, h - b - tile_h, 30):
        for cx in range(b + 10, w - b - tile_w, 60):
            patch = img.crop((cx, cy, cx + tile_w, cy + tile_h))
            pixels = list(patch.getdata())
            lums = [0.3 * r + 0.59 * g + 0.11 * bl for r, g, bl in pixels]
            var = statistics.pvariance(lums)
            mean_lum = sum(lums) / len(lums)
            if mean_lum > 230:  # only consider bright/paper patches
                candidates.append((var, cx, cy))

    if not candidates:
        # Fallback: fill with a neutral off-white
        draw = ImageDraw.Draw(img)
        c = (247, 247, 244)
        draw.rectangle([0, 0, w, b], fill=c)
        draw.rectangle([0, h - b, w, h], fill=c)
        draw.rectangle([0, 0, b, h], fill=c)
        draw.rectangle([w - b, 0, w, h], fill=c)
        return img

    candidates.sort()
    _, tx, ty = candidates[0]
    tile = img.crop((tx, ty, tx + tile_w, ty + tile_h))

    for y_start, strip_h in [(0, b), (h - b, b)]:
        for x in range(0, w, tile_w):
            for y in range(y_start, y_start + strip_h, tile_h):
                img.paste(tile, (x, y))
    for x_start, strip_w in [(0, b), (w - b, b)]:
        for y in range(0, h, tile_h):
            for x in range(x_start, x_start + strip_w, tile_w):
                img.paste(tile, (x, y))
    return img


def paint_logo_patch(img: Image.Image, logo_w: int, logo_h: int,
                     pad_t: int, pad_r: int) -> Image.Image:
    """Paint a feathered, paper-colored backdrop under where the logo will sit.
    Guarantees the logo reads cleanly even if the AI drew a card/frame edge
    directly beneath it.
    """
    w, h = img.size
    # Sample interior paper color (median of a center patch)
    cx, cy = w // 2 - 30, h // 2 - 30
    px = list(img.crop((cx, cy, cx + 60, cy + 60)).getdata())
    mr = int(statistics.median(p[0] for p in px))
    mg = int(statistics.median(p[1] for p in px))
    mb = int(statistics.median(p[2] for p in px))
    if (mr + mg + mb) // 3 < 230:
        mr, mg, mb = 249, 249, 246  # fallback to warm off-white

    # Patch region: generously wider and taller than logo for soft blend.
    # Covers the whole top-right corner region where AI frame edges live.
    bx1 = w - (logo_w + pad_r + 140)
    by1 = -20
    bx2 = w + 20
    by2 = pad_t + logo_h + 40

    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([bx1, by1, bx2, by2], radius=28, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=28))

    fill = Image.new("RGB", (w, h), (mr, mg, mb))
    return Image.composite(fill, img, mask)


def _load_logo(path: Path, target_h: int) -> Image.Image:
    """Load a logo, convert white background to alpha (for JPGs),
    tight-crop to visible pixels via getbbox(), then resize to target height."""
    im = Image.open(path).convert("RGBA")
    # Convert near-white pixels to transparent (handles JPG logos on white bg)
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r > 240 and g > 240 and b > 240:
                px[x, y] = (r, g, b, 0)
    # Tight-crop to visible (non-transparent) bounding box
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    cw, ch = im.size
    new_w = int(target_h * cw / ch)
    return im.resize((new_w, target_h), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("deck_dir", type=Path, help="Slide deck directory")
    ap.add_argument("--logo", type=Path, required=True, help="Primary logo path (PNG or JPG)")
    ap.add_argument("--logo2", type=Path, default=None, help="Secondary logo path (placed left of primary)")
    ap.add_argument("--logo2-gap", type=int, default=32, help="Gap between two logos in px (default: 32)")
    ap.add_argument("--skip", default="1", help="Slide numbers to skip (no logo). Default: 1 (cover)")
    ap.add_argument("--logo-h", type=int, default=46, help="Logo height in px (default: 46)")
    ap.add_argument("--pad-top", type=int, default=20, help="Top padding (default: 20)")
    ap.add_argument("--pad-right", type=int, default=26, help="Right padding (default: 26)")
    ap.add_argument("--patch-slides", default="", help="Slides that need a logo backdrop patch")
    ap.add_argument("--frame-slides", default="", help="Slides that need full edge frame-stripping")
    ap.add_argument("--border-px", type=int, default=40, help="Frame-strip width in px (default: 40)")
    ap.add_argument("--qr", type=Path, default=None, help="QR code PNG to composite")
    ap.add_argument("--qr-slide", type=int, default=0, help="Slide number to composite QR into")
    ap.add_argument("--qr-box", default="", help="QR placement box X1,Y1,X2,Y2")
    args = ap.parse_args()

    deck = args.deck_dir.resolve()
    if not deck.is_dir():
        print(f"ERROR: {deck} is not a directory", file=sys.stderr)
        sys.exit(1)
    if not args.logo.exists():
        print(f"ERROR: logo not found: {args.logo}", file=sys.stderr)
        sys.exit(1)

    orig_dir = deck / "_original"
    orig_dir.mkdir(exist_ok=True)

    # Backup once
    pngs = sorted(deck.glob("[0-9][0-9]-slide-*.png"))
    if not pngs:
        print(f"ERROR: no slide PNGs found in {deck}", file=sys.stderr)
        sys.exit(1)
    for p in pngs:
        backup = orig_dir / p.name
        if not backup.exists():
            backup.write_bytes(p.read_bytes())

    skip = parse_int_set(args.skip)
    patch_slides = parse_int_set(args.patch_slides)
    frame_slides = parse_int_set(args.frame_slides)

    # Prepare logo (tight-crop to visible pixels, convert white bg to alpha for JPGs)
    logo_r = _load_logo(args.logo, args.logo_h)
    new_lw = logo_r.width

    # Prepare secondary logo
    logo2_r = _load_logo(args.logo2, args.logo_h) if args.logo2 and args.logo2.exists() else None

    # Prepare QR if given
    qr_img = Image.open(args.qr).convert("RGBA") if args.qr and args.qr.exists() else None
    qr_box = parse_box(args.qr_box) if args.qr_box else None

    for src in sorted(orig_dir.glob("[0-9][0-9]-slide-*.png")):
        num = int(src.name[:2])
        base = Image.open(src).convert("RGB")
        notes = []

        if num in frame_slides:
            base = strip_frame(base, args.border_px)
            notes.append("frame-stripped")

        if num in patch_slides:
            base = paint_logo_patch(base, new_lw, args.logo_h, args.pad_top, args.pad_right)
            notes.append("backdrop")

        # Composite QR
        if qr_img is not None and num == args.qr_slide and qr_box is not None:
            bx, by, bx2, by2 = qr_box
            box_w, box_h = bx2 - bx, by2 - by
            qr_side = max(20, min(box_w, box_h) - 12)
            qr_r = qr_img.resize((qr_side, qr_side), Image.LANCZOS)
            rgba = base.convert("RGBA")
            cx = bx + (box_w - qr_side) // 2
            cy = by + (box_h - qr_side) // 2
            rgba.alpha_composite(qr_r, (cx, cy))
            base = rgba.convert("RGB")
            notes.append("QR")

        out = deck / src.name
        if num in skip:
            base.save(out, "PNG", optimize=True)
            tag = " (skip logo)" + (f" [{', '.join(notes)}]" if notes else "")
            print(f"  {src.name}{tag}")
            continue

        rgba = base.convert("RGBA")
        # Primary logo at top-right
        primary_x = rgba.width - args.pad_right - new_lw
        primary_cy = args.pad_top + args.logo_h // 2
        rgba.alpha_composite(logo_r, (primary_x, args.pad_top))
        # Secondary logo to the left of primary, optically center-aligned
        if logo2_r is not None:
            l2w, l2h = logo2_r.size
            l2_x = primary_x - args.logo2_gap - l2w
            l2_y = primary_cy - l2h // 2
            rgba.alpha_composite(logo2_r, (l2_x, l2_y))
        rgba.convert("RGB").save(out, "PNG", optimize=True)
        logo_tag = "+logos" if logo2_r else "+logo"
        tag = f" {logo_tag}" + (f" [{', '.join(notes)}]" if notes else "")
        print(f"  {src.name}{tag}")


if __name__ == "__main__":
    main()
