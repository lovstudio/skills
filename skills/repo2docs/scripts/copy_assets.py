#!/usr/bin/env python3
"""
Copy images from a source folder into a Fumadocs site's public/ tree and emit a
path mapping the agent uses to embed them in MDX.

Images in a content folder are first-class — they must end up under the site's
`public/` so MDX can reference them as `/assets/<...>`. With Next.js basePath
'/docs', a `/assets/x.png` reference resolves to `/docs/assets/x.png`
automatically, so MDX should use root-relative `/assets/...` paths.

Optionally downsizes/transcodes large or non-web-friendly images (HEIC/TIFF/BMP)
to web formats when Pillow is available; otherwise copies verbatim.

Usage:
    python3 copy_assets.py --src ./my-folder --site ./my-docs
    python3 copy_assets.py --src ./my-folder --site ./my-docs --max-width 1600
    python3 copy_assets.py --src ./my-folder --site ./my-docs --out assets-map.json

Output (JSON): { "<source-rel-path>": "/assets/<dest-rel-path>", ... }
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif",
              ".bmp", ".heic", ".heif", ".tiff"}
# Formats we transcode to web-friendly when Pillow is present.
TRANSCODE = {".heic", ".heif", ".tiff", ".bmp"}
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "out",
             "__pycache__", ".venv", "venv", ".obsidian"}


def find_images(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if Path(fn).suffix.lower() in IMAGE_EXTS:
                yield Path(dirpath) / fn


def try_pillow():
    try:
        from PIL import Image  # noqa
        return True
    except Exception:
        return False


def process(src_img: Path, dest_img: Path, max_width: int, has_pillow: bool) -> Path:
    """Copy or transcode/resize. Returns the final dest path (extension may
    change when transcoding)."""
    ext = src_img.suffix.lower()
    dest_img.parent.mkdir(parents=True, exist_ok=True)

    needs_transcode = ext in TRANSCODE
    if not has_pillow or (ext == ".svg") or (ext == ".gif"):
        # Verbatim copy (SVG/GIF must not be rasterized; no Pillow → no resize).
        shutil.copy2(src_img, dest_img)
        return dest_img

    try:
        from PIL import Image
        with Image.open(src_img) as im:
            if needs_transcode:
                dest_img = dest_img.with_suffix(".jpg" if im.mode == "RGB" else ".png")
            if im.width > max_width:
                ratio = max_width / im.width
                im = im.resize((max_width, max(1, int(im.height * ratio))))
            save_kwargs = {}
            if dest_img.suffix.lower() in (".jpg", ".jpeg"):
                im = im.convert("RGB")
                save_kwargs = {"quality": 85, "optimize": True}
            im.save(dest_img, **save_kwargs)
        return dest_img
    except Exception as exc:
        print(f"WARN: {src_img}: {exc}; copying verbatim", file=sys.stderr)
        dest_img = dest_img.with_suffix(ext)
        shutil.copy2(src_img, dest_img)
        return dest_img


def main():
    ap = argparse.ArgumentParser(description="Copy/optimize images into a Fumadocs public/ tree")
    ap.add_argument("--src", required=True, help="Source content folder")
    ap.add_argument("--site", required=True, help="Fumadocs site root (contains public/)")
    ap.add_argument("--subdir", default="assets", help="Subdir under public/ (default: assets)")
    ap.add_argument("--max-width", type=int, default=1600, help="Downscale wider images (default 1600px)")
    ap.add_argument("--no-optimize", action="store_true", help="Copy verbatim, never transcode/resize")
    ap.add_argument("--out", default="", help="Write the path map JSON here (default: stdout)")
    args = ap.parse_args()

    root = Path(os.path.expanduser(args.src)).resolve()
    site = Path(os.path.expanduser(args.site)).resolve()
    if not root.is_dir():
        sys.exit(f"ERROR: --src not a directory: {root}")
    if not site.is_dir():
        sys.exit(f"ERROR: --site not a directory: {site}")

    public = site / "public" / args.subdir
    has_pillow = (not args.no_optimize) and try_pillow()

    mapping = {}
    n = 0
    for img in find_images(root):
        rel = img.relative_to(root)
        dest = public / rel
        if args.no_optimize:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img, dest)
            final = dest
        else:
            final = process(img, dest, args.max_width, has_pillow)
        web_path = "/" + str(Path(args.subdir) / final.relative_to(public)).replace(os.sep, "/")
        mapping[str(rel).replace(os.sep, "/")] = web_path
        n += 1

    text = json.dumps(mapping, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"✓ {n} images → {public}  (pillow={'yes' if has_pillow else 'no'})", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
