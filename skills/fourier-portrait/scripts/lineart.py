"""Photo -> binary line art (ink = 255) suited to a single Fourier path.

The look is an engraving-like stencil: locally dark detail (eyes, glasses, mouth, hair folds,
silhouette) becomes ink, flat regions stay empty, so the boundaries of the ink blobs read as a
portrait when traced as one continuous line.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

SWIFT_HELPER = Path(__file__).with_name("subject_mask.swift")


def segment(photo: Path, workdir: Path):
    """Return (bgr, mask or None, faces list). Uses Apple Vision when available."""
    img_png, mask_png = workdir / "input.png", workdir / "mask.png"
    if sys.platform == "darwin" and shutil.which("swift"):
        proc = subprocess.run(["swift", str(SWIFT_HELPER), str(photo), str(img_png), str(mask_png)],
                              capture_output=True, text=True)
        if proc.returncode == 0:
            info = json.loads(proc.stdout.strip().splitlines()[-1])
            return cv2.imread(str(img_png)), cv2.imread(str(mask_png), cv2.IMREAD_GRAYSCALE), info["faces"]
        print(f"[lineart] Vision segmentation unavailable ({proc.stderr.strip()}); using full frame",
              file=sys.stderr)
    bgr = cv2.imread(str(photo))
    if bgr is None:
        raise SystemExit(f"cannot read photo: {photo} (HEIC needs macOS Vision path)")
    return bgr, None, []


def bust_crop(shape, faces, crop):
    """Crop box (x0, y0, x1, y1). `crop` is 'auto', 'full', or 'x0,y0,x1,y1' in 0..1 fractions."""
    H, W = shape[:2]
    if crop == "full" or (crop == "auto" and not faces):
        return 0, 0, W, H
    if crop != "auto":
        f = [float(v) for v in crop.split(",")]
        return int(f[0] * W), int(f[1] * H), int(f[2] * W), int(f[3] * H)
    fx, fy, fw, fh = faces[0]
    cx = fx + fw / 2
    return (int(max(0, cx - 1.6 * fw)), int(max(0, fy - 0.9 * fh)),
            int(min(W, cx + 1.6 * fw)), int(min(H, fy + 1.8 * fh)))


def make_lineart(photo: Path, workdir: Path, *, crop="auto", work_size=900, block=35, offset=8,
                 blur=2.0, min_area=60):
    workdir.mkdir(parents=True, exist_ok=True)
    bgr, mask, faces = segment(photo, workdir)
    x0, y0, x1, y1 = bust_crop(bgr.shape, faces, crop)
    bgr = bgr[y0:y1, x0:x1]
    mask = mask[y0:y1, x0:x1] if mask is not None else np.full(bgr.shape[:2], 255, np.uint8)

    s = work_size / max(bgr.shape[:2])
    bgr = cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    mask = cv2.resize(mask, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_AREA)

    # Equalise lightness so dim or tinted selfies still separate features from skin.
    L = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[..., 0]
    L = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(L)
    g = L.astype(np.float32) / 255
    # Repeated bilateral passes flatten print halftone and skin noise but keep feature edges.
    for _ in range(3):
        g = cv2.bilateralFilter(g, 9, 0.10, 6)
    m = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 1.5)
    g8 = ((g * m + (1 - m)) * 255).astype(np.uint8)

    ink = cv2.adaptiveThreshold(cv2.GaussianBlur(g8, (0, 0), blur), 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                cv2.THRESH_BINARY_INV, block, offset)
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(ink, 8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    ink = np.where(keep[labels], 255, 0).astype(np.uint8)

    cv2.imwrite(str(workdir / "lineart.png"), ink)
    cv2.imwrite(str(workdir / "photo_cutout.png"), np.dstack([bgr, mask]))
    meta = {"crop": [x0, y0, x1, y1], "faces": faces, "size": list(ink.shape[::-1]),
            "segmented": bool(mask.min() < 255)}
    (workdir / "lineart.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return ink, np.dstack([bgr, mask]), meta
