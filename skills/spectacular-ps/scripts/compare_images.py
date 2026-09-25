#!/usr/bin/env python3
"""Compose actual before/after files without cropping or generative editing."""

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageCms, ImageOps


def positive_int(value):
    number = int(value)
    if not 1 <= number <= 4096:
        raise argparse.ArgumentTypeError("must be between 1 and 4096")
    return number


def read_image(path):
    raw = path.read_bytes()
    with Image.open(io.BytesIO(raw)) as source:
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError("animated or multipage input is not supported")
        if source.width * source.height > 50_000_000:
            raise ValueError("input exceeds 50 megapixels")
        stored_size = list(source.size)
        icc = source.info.get("icc_profile")
        oriented = ImageOps.exif_transpose(source)
        rgba = oriented.convert("RGBA")
        if icc:
            profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            base = oriented if oriented.mode in ("RGB", "CMYK", "LAB", "L") else oriented.convert("RGB")
            converted = ImageCms.profileToProfile(base, profile, ImageCms.createProfile("sRGB"), outputMode="RGB")
            converted.putalpha(rgba.getchannel("A"))
            rgba = converted
        record = {
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "stored_size": stored_size,
            "oriented_size": list(rgba.size),
            "color_management": "embedded-icc-to-srgb" if icc else "assumed-srgb",
        }
        return rgba.copy(), record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--height", type=positive_int, help="common panel height; default is the smaller source height, capped at 1600")
    parser.add_argument("--padding", type=positive_int, default=24)
    args = parser.parse_args()
    before_path = args.before.expanduser().resolve()
    after_path = args.after.expanduser().resolve()
    output_path = args.output.expanduser().absolute()
    if output_path.suffix.lower() != ".png":
        parser.error("output must use the .png extension")
    if output_path.resolve() in (before_path, after_path):
        parser.error("output must not replace an input")
    if output_path.exists() or output_path.is_symlink():
        parser.error("output already exists; choose a new filename")
    try:
        before, before_record = read_image(before_path)
        after, after_record = read_image(after_path)
        height = args.height or min(before.height, after.height, 1600)
        widths = [max(1, round(img.width * height / img.height)) for img in (before, after)]
        size = (sum(widths) + args.padding * 3, height + args.padding * 2)
        if size[0] * size[1] > 50_000_000:
            raise ValueError("comparison exceeds 50 megapixels; reduce height")
        canvas = Image.new("RGB", size, (24, 24, 24))
        x = args.padding
        panels = []
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        for role, img, width, record in zip(("before", "after"), (before, after), widths, (before_record, after_record)):
            scaled = img.resize((width, height), resampling)
            canvas.paste(scaled, (x, args.padding), scaled.getchannel("A"))
            panels.append({"role": role, "box": [x, args.padding, x + width, args.padding + height],
                           "resized": list(img.size) != [width, height], "source": record})
            x += width + args.padding
        buffer = io.BytesIO()
        srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        canvas.save(buffer, format="PNG", icc_profile=srgb)
        png = buffer.getvalue()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("xb") as destination:
            destination.write(png)
        with Image.open(output_path) as saved:
            saved.load()
            if saved.size != size:
                raise ValueError("output readback size mismatch")
        print(json.dumps({"status": "verified", "output": str(output_path), "format": "PNG",
                          "size": list(size), "bytes": len(png), "sha256": hashlib.sha256(png).hexdigest(),
                          "panels": panels, "operation": "exif-orient, color-manage, contain-resize, composite",
                          "generative_edit": False, "pixel_identical_to_inputs": False}, ensure_ascii=False))
    except (OSError, ValueError, Image.DecompressionBombError, ImageCms.PyCMSError) as exc:
        parser.exit(2, "comparison failed: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
