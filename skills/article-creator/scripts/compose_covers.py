#!/usr/bin/env python3
"""Compose official brand assets onto wide cover and 4:3 body-hero canvases."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps


SCHEMA = "lovstudio/wechat-cover-package/v2"
RESAMPLE = Image.Resampling.LANCZOS
MIN_HORIZONTAL_LOGO_RATIO = 1.8
MIN_WHITE_PIXEL_RATIO = 0.98


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_size(raw: str) -> tuple[int, int]:
    try:
        width, height = (int(value) for value in raw.lower().split("x", 1))
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("size must look like 1880x800") from error
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("size dimensions must be positive")
    return width, height


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dim_bottom(image: Image.Image, strength: float) -> Image.Image:
    width, height = image.size
    start = int(height * 0.38)
    mask = Image.new("L", (1, height), 0)
    pixels = mask.load()
    for y in range(start, height):
        progress = (y - start) / max(1, height - start - 1)
        pixels[0, y] = round(255 * strength * progress)
    mask = mask.resize((width, height))
    return Image.composite(Image.new("RGB", image.size, "black"), image.convert("RGB"), mask)


def fit_logo(logo: Image.Image, max_width: int, max_height: int) -> Image.Image:
    scale = min(max_width / logo.width, max_height / logo.height, 1.0)
    size = (max(1, round(logo.width * scale)), max(1, round(logo.height * scale)))
    return logo.resize(size, RESAMPLE) if size != logo.size else logo.copy()


def white_pixel_ratio(logo: Image.Image) -> float:
    visible = [pixel for pixel in logo.getdata() if pixel[3] >= 32]
    if not visible:
        return 0.0
    white = sum(1 for red, green, blue, _ in visible if min(red, green, blue) >= 245)
    return white / len(visible)


def make_canvas(
    art: Image.Image,
    logo: Image.Image,
    size: tuple[int, int],
    strength: float,
    mode: str,
) -> Image.Image:
    width, height = size
    canvas = ImageOps.fit(art.convert("RGB"), size, method=RESAMPLE, centering=(0.5, 0.5))
    canvas = dim_bottom(canvas, strength).convert("RGBA")
    if mode == "wide":
        placed_logo = fit_logo(logo, round(width * 0.24), round(height * 0.45))
        x = (width - placed_logo.width) // 2
        y = (height - placed_logo.height) // 2
    else:
        placed_logo = fit_logo(logo, round(width * 0.36), round(height * 0.10))
        x = (width - placed_logo.width) // 2
        y = height - round(height * 0.05) - placed_logo.height
    canvas.alpha_composite(placed_logo, (x, y))
    return canvas.convert("RGB")


def write_pair(image: Image.Image, png_path: Path, jpg_path: Path) -> dict[str, str]:
    image.save(png_path, format="PNG", optimize=True)
    image.save(jpg_path, format="JPEG", quality=92, optimize=True, progressive=True)
    return {"png": sha256(png_path), "jpg": sha256(jpg_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--art", required=True, type=Path)
    parser.add_argument("--logo", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--brand-name", required=True)
    parser.add_argument("--publication-name", default="")
    parser.add_argument("--wide-size", default="1880x800", type=parse_size)
    parser.add_argument(
        "--opening-size",
        "--vertical-size",
        dest="opening_size",
        default="1600x1200",
        type=parse_size,
        help="4:3 body opening image size; --vertical-size is a deprecated alias",
    )
    parser.add_argument("--dimming", default=0.45, type=float)
    args = parser.parse_args()

    if not 0 <= args.dimming <= 1:
        parser.error("dimming must be between 0 and 1")
    if not args.art.is_file():
        parser.error(f"art master not found: {args.art}")
    if not args.logo.is_file():
        parser.error(f"official raster logo not found: {args.logo}")

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    art = Image.open(args.art)
    logo = Image.open(args.logo).convert("RGBA")
    logo_bbox = logo.getbbox()
    if logo_bbox is None:
        parser.error("official logo is fully transparent")
    logo_content_width = logo_bbox[2] - logo_bbox[0]
    logo_content_height = logo_bbox[3] - logo_bbox[1]
    logo_aspect_ratio = logo_content_width / logo_content_height
    if logo_aspect_ratio < MIN_HORIZONTAL_LOGO_RATIO:
        parser.error(
            "cover logo must be the official horizontal lockup "
            f"(content ratio >= {MIN_HORIZONTAL_LOGO_RATIO:.1f}; got {logo_aspect_ratio:.2f})"
        )
    logo_white_ratio = white_pixel_ratio(logo)
    if logo_white_ratio < MIN_WHITE_PIXEL_RATIO:
        parser.error(
            "cover logo must be the official white lockup "
            f"(white pixel ratio >= {MIN_WHITE_PIXEL_RATIO:.2f}; got {logo_white_ratio:.3f})"
        )

    art_master = output / "art-master.png"
    art.convert("RGB").save(art_master, format="PNG", optimize=True)
    wide_png = output / "wechat-cover-wide.png"
    wide_jpg = output / "wechat-cover-wide.jpg"
    opening_png = output / "article-opening-4x3.png"
    opening_jpg = output / "article-opening-4x3.jpg"

    wide = make_canvas(art, logo, args.wide_size, args.dimming, "wide")
    opening = make_canvas(art, logo, args.opening_size, args.dimming, "opening")
    wide_hashes = write_pair(wide, wide_png, wide_jpg)
    opening_hashes = write_pair(opening, opening_png, opening_jpg)

    manifest = {
        "schema": SCHEMA,
        "brand": {"name": args.brand_name},
        "publication": {
            "name": args.publication_name or args.brand_name,
            "logo_source": "profile:skills.lov-article-creator.records.cover_logo_path",
            "logo_variant": "horizontal-lockup",
            "logo_color": "white",
            "logo_aspect_ratio": round(logo_aspect_ratio, 3),
            "logo_white_pixel_ratio": round(logo_white_ratio, 4),
        },
        "created_at": now_iso(),
        "art_master_path": "cover/art-master.png",
        "art_master_sha256": sha256(art_master),
        "wide": {
            "png_path": "cover/wechat-cover-wide.png",
            "jpg_path": "cover/wechat-cover-wide.jpg",
            "width": args.wide_size[0],
            "height": args.wide_size[1],
            "ratio": "2.35:1",
            "logo_position": "center",
            "sha256": wide_hashes,
        },
        "opening": {
            "png_path": "cover/article-opening-4x3.png",
            "jpg_path": "cover/article-opening-4x3.jpg",
            "width": args.opening_size[0],
            "height": args.opening_size[1],
            "ratio": "4:3",
            "logo_position": "bottom-center",
            "sha256": opening_hashes,
        },
    }
    (output / "cover-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "cover_dir": str(output),
                "wide": list(args.wide_size),
                "opening": list(args.opening_size),
                "logo_variant": "horizontal-lockup",
                "logo_color": "white",
                "logo_aspect_ratio": round(logo_aspect_ratio, 3),
                "publication_name": args.publication_name or args.brand_name,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
