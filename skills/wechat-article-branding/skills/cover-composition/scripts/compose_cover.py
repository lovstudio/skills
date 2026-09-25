#!/usr/bin/env python3
"""Compose branded WeChat cover variants from one artwork and an official logo."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat


WIDE_SIZE = (1880, 800)
SQUARE_SIZE = (800, 800)
VERTICAL_SIZE = (1200, 1600)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_background(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)


def dim_bottom(image: Image.Image, *, start_ratio: float = 0.38, strength: float = 0.45) -> Image.Image:
    if not 0 <= start_ratio < 1 or not 0 <= strength <= 1:
        raise ValueError("start_ratio and strength must be between 0 and 1")
    width, height = image.size
    start = round(height * start_ratio)
    alpha = Image.new("L", (1, height), 0)
    draw = ImageDraw.Draw(alpha)
    span = max(1, height - start - 1)
    for y in range(start, height):
        draw.point((0, y), fill=round(255 * strength * (y - start) / span))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 255))
    overlay.putalpha(alpha.resize(image.size))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def load_visible_logo(path: Path) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    alpha_bbox = logo.getchannel("A").getbbox()
    if alpha_bbox is None:
        raise ValueError("Logo does not contain visible pixels")
    logo = logo.crop(alpha_bbox)
    if logo.width < 2 or logo.height < 2:
        raise ValueError("Logo visible bounds are too small")
    return logo


def validate_logo_variant(logo: Image.Image, variant: str) -> list[float]:
    sample = logo.copy()
    sample.thumbnail((256, 256), Image.Resampling.LANCZOS)
    alpha = sample.getchannel("A")
    means = [round(value, 2) for value in ImageStat.Stat(sample.convert("RGB"), mask=alpha).mean]
    if variant == "white" and (min(means) < 225 or max(means) - min(means) > 20):
        raise ValueError(
            f"Logo variant is declared white but visible pixel mean is RGB {means}; "
            "pass the official white cover logo"
        )
    return means


def scale_logo(logo: Image.Image, canvas: tuple[int, int], max_width: float, max_height: float) -> Image.Image:
    width_limit = max(1, round(canvas[0] * max_width))
    height_limit = max(1, round(canvas[1] * max_height))
    scale = min(width_limit / logo.width, height_limit / logo.height)
    return logo.resize(
        (max(1, round(logo.width * scale)), max(1, round(logo.height * scale))),
        Image.Resampling.LANCZOS,
    )


def overlay_logo(
    background: Image.Image,
    logo: Image.Image,
    *,
    max_width: float,
    max_height: float,
    position: str,
    bottom_margin: float = 0.0,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    scaled = scale_logo(logo, background.size, max_width, max_height)
    x = (background.width - scaled.width) // 2
    if position == "center":
        y = (background.height - scaled.height) // 2
    elif position == "bottom_center":
        y = background.height - round(background.height * bottom_margin) - scaled.height
    else:
        raise ValueError(f"unsupported logo position: {position}")
    if x < 0 or y < 0:
        raise ValueError("Logo placement falls outside the canvas")
    result = background.convert("RGBA")
    result.alpha_composite(scaled, (x, y))
    bbox = (x, y, x + scaled.width, y + scaled.height)
    if ImageChops.difference(background.convert("RGB").crop(bbox), result.convert("RGB").crop(bbox)).getbbox() is None:
        raise ValueError("Logo composition produced no visible pixel difference")
    return result.convert("RGB"), bbox


def save_pair(image: Image.Image, output_dir: Path, stem: str) -> dict[str, str]:
    png = output_dir / f"{stem}.png"
    jpg = output_dir / f"{stem}.jpg"
    image.save(png, format="PNG", optimize=True)
    image.save(jpg, format="JPEG", quality=92, optimize=True, progressive=True)
    return {"png": str(png.resolve()), "jpg": str(jpg.resolve())}


def compose(
    background_path: Path,
    logo_path: Path,
    output_dir: Path,
    opening_hero: bool,
    logo_variant: str = "profile",
) -> dict[str, Any]:
    if not background_path.is_file():
        raise FileNotFoundError(f"background not found: {background_path}")
    if not logo_path.is_file():
        raise FileNotFoundError(f"logo not found: {logo_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    artwork = Image.open(background_path)
    logo = load_visible_logo(logo_path)
    logo_rgb_mean = validate_logo_variant(logo, logo_variant)

    wide_background = dim_bottom(fit_background(artwork, WIDE_SIZE))
    wide_background_path = output_dir / "share-cover-wide-background.png"
    wide_background.save(wide_background_path, format="PNG", optimize=True)
    wide, wide_bbox = overlay_logo(
        wide_background,
        logo,
        max_width=0.24,
        max_height=0.45,
        position="center",
    )

    square_background = ImageOps.fit(
        wide_background,
        SQUARE_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    square, square_bbox = overlay_logo(
        square_background,
        logo,
        max_width=0.36,
        max_height=0.15,
        position="bottom_center",
        bottom_margin=0.05,
    )

    artifacts: dict[str, Any] = {
        "wide": {**save_pair(wide, output_dir, "share-cover-wide-logo"), "size": list(WIDE_SIZE), "logoBBox": list(wide_bbox)},
        "square": {**save_pair(square, output_dir, "share-cover-square-logo"), "size": list(SQUARE_SIZE), "logoBBox": list(square_bbox)},
    }

    if opening_hero:
        vertical_background = dim_bottom(fit_background(artwork, VERTICAL_SIZE), start_ratio=0.48, strength=0.5)
        vertical, vertical_bbox = overlay_logo(
            vertical_background,
            logo,
            max_width=0.42,
            max_height=0.16,
            position="bottom_center",
            bottom_margin=0.08,
        )
        artifacts["openingHero"] = {
            **save_pair(vertical, output_dir, "opening-hero-vertical-logo"),
            "size": list(VERTICAL_SIZE),
            "logoBBox": list(vertical_bbox),
        }

    receipt = {
        "schema": "lov-wechat-cover-composition/v1",
        "background": str(background_path.resolve()),
        "logo": str(logo_path.resolve()),
        "logoSha256": sha256(logo_path),
        "logoVariant": logo_variant,
        "logoVisiblePixelMeanRgb": logo_rgb_mean,
        "publisherLogoPresent": True,
        "shareCoverUpload": artifacts["wide"]["jpg"],
        "artifacts": artifacts,
    }
    receipt_path = output_dir / "cover-composition.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt["receipt"] = str(receipt_path.resolve())
    return receipt


def self_test() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        background = root / "background.png"
        logo = root / "logo.png"
        Image.new("RGB", (1200, 700), (80, 110, 140)).save(background)
        logo_image = Image.new("RGBA", (360, 120), (0, 0, 0, 0))
        ImageDraw.Draw(logo_image).rectangle((20, 20, 340, 100), fill=(255, 255, 255, 255))
        logo_image.save(logo)
        result = compose(background, logo, root / "out", opening_hero=True, logo_variant="white")
        assert result["publisherLogoPresent"] is True
        assert result["logoVariant"] == "white"
        assert Image.open(result["artifacts"]["wide"]["jpg"]).size == WIDE_SIZE
        assert Image.open(result["artifacts"]["square"]["jpg"]).size == SQUARE_SIZE
        assert Image.open(result["artifacts"]["openingHero"]["jpg"]).size == VERTICAL_SIZE
        orange = Image.new("RGBA", (360, 120), (0, 0, 0, 0))
        ImageDraw.Draw(orange).rectangle((20, 20, 340, 100), fill=(220, 110, 75, 255))
        orange_path = root / "orange.png"
        orange.save(orange_path)
        try:
            compose(background, orange_path, root / "invalid", opening_hero=False, logo_variant="white")
        except ValueError as error:
            assert "declared white" in str(error)
        else:
            raise AssertionError("orange logo was accepted as white")
    print("SELF-TEST PASSED")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--background", type=Path)
    parser.add_argument("--logo", type=Path)
    parser.add_argument("--logo-variant", default="profile")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--opening-hero", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        return self_test()
    if args.background is None or args.logo is None or args.output_dir is None:
        raise SystemExit("--background, --logo, and --output-dir are required")
    result = compose(
        args.background,
        args.logo,
        args.output_dir,
        args.opening_hero,
        logo_variant=args.logo_variant,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["receipt"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
