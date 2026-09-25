#!/usr/bin/env python3
"""Measure, normalize, and verify Tauri macOS app-icon evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:
    print(
        json.dumps(
            {
                "ok": False,
                "context_id": "tauri-app-icon/missing-pillow",
                "field": "dependency",
                "message": "Pillow is required. Install it with: python3 -m pip install 'Pillow>=9.0'",
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    raise SystemExit(2)


class IconInputError(Exception):
    """A user-actionable input error with a stable diagnostic identifier."""

    def __init__(self, code: str, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message


def emit(payload: Dict[str, Any], stream: Any = sys.stdout) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), file=stream)


def fail(error: IconInputError) -> int:
    emit(
        {
            "ok": False,
            "context_id": "tauri-app-icon/{0}".format(error.code),
            "field": error.field,
            "message": error.message,
        },
        sys.stderr,
    )
    return 2


def alpha_threshold(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer from 1 to 255") from exc
    if not 1 <= parsed <= 255:
        raise argparse.ArgumentTypeError("must be an integer from 1 to 255")
    return parsed


def positive_size(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def visible_ratio(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number greater than 0 and at most 1") from exc
    if not 0 < parsed <= 1:
        raise argparse.ArgumentTypeError("must be a number greater than 0 and at most 1")
    return parsed


def open_square_rgba(path: Path) -> Image.Image:
    if not path.is_file():
        raise IconInputError("missing-input", "input", "image does not exist: {0}".format(path))
    try:
        with Image.open(path) as source:
            source.load()
            image = source.convert("RGBA")
    except (OSError, ValueError) as exc:
        raise IconInputError("unreadable-image", "input", "could not decode image: {0}".format(path)) from exc
    if image.width != image.height:
        raise IconInputError(
            "non-square-canvas",
            "input",
            "Tauri app icon input must be square; got {0}x{1}".format(image.width, image.height),
        )
    return image


def alpha_bbox(image: Image.Image, threshold: int) -> Tuple[int, int, int, int]:
    alpha = image.getchannel("A")
    if threshold > 1:
        alpha = alpha.point(lambda value: 255 if value >= threshold else 0)
    bbox = alpha.getbbox()
    if bbox is None:
        raise IconInputError("empty-alpha", "input", "image has no pixels at or above the alpha threshold")
    return bbox


def metrics_from_image(image: Image.Image, threshold: int) -> Dict[str, Any]:
    bbox = alpha_bbox(image, threshold)
    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    side = max(width, height)
    canvas = image.width
    corners = {
        "top_left": image.getpixel((0, 0))[3],
        "top_right": image.getpixel((canvas - 1, 0))[3],
        "bottom_left": image.getpixel((0, canvas - 1))[3],
        "bottom_right": image.getpixel((canvas - 1, canvas - 1))[3],
    }
    return {
        "canvas": {"width": canvas, "height": canvas},
        "alpha_threshold": threshold,
        "visible_bbox": {"left": left, "top": top, "width": width, "height": height},
        "visible_side": side,
        "visible_ratio": round(float(side) / float(canvas), 6),
        "corner_alpha": corners,
        "has_transparent_corners": any(value < threshold for value in corners.values()),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def command_measure(args: argparse.Namespace) -> int:
    path = Path(args.input)
    metrics = metrics_from_image(open_square_rgba(path), args.alpha_threshold)
    emit(
        {
            "ok": True,
            "context_id": "tauri-app-icon/measure",
            "input": str(path),
            "metrics": metrics,
        }
    )
    return 0


def command_normalize(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    source = open_square_rgba(input_path)
    source_metrics = metrics_from_image(source, args.alpha_threshold)
    reference_metrics: Optional[Dict[str, Any]] = None

    if args.reference:
        reference_path = Path(args.reference)
        reference_metrics = metrics_from_image(open_square_rgba(reference_path), args.alpha_threshold)
        target_ratio = float(reference_metrics["visible_ratio"])
        target_source = "reference"
    else:
        target_ratio = float(args.target_visible_ratio)
        target_source = "explicit_ratio"

    output_size = args.size or source.width
    bbox = source_metrics["visible_bbox"]
    crop_box = (
        int(bbox["left"]),
        int(bbox["top"]),
        int(bbox["left"] + bbox["width"]),
        int(bbox["top"] + bbox["height"]),
    )
    cropped = source.crop(crop_box)
    source_visible_side = int(source_metrics["visible_side"])
    target_visible_side = max(1, min(output_size, int(round(output_size * target_ratio))))
    scale = float(target_visible_side) / float(source_visible_side)
    resized_width = max(1, int(round(cropped.width * scale)))
    resized_height = max(1, int(round(cropped.height * scale)))
    resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    resized = cropped.resize((resized_width, resized_height), resampling)
    canvas = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    offset = ((output_size - resized_width) // 2, (output_size - resized_height) // 2)
    canvas.alpha_composite(resized, offset)

    if output_path.exists() and not args.force:
        raise IconInputError(
            "output-exists",
            "output",
            "output already exists; choose a new path or pass --force: {0}".format(output_path),
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)
    output_metrics = metrics_from_image(canvas, args.alpha_threshold)
    emit(
        {
            "ok": True,
            "context_id": "tauri-app-icon/normalize",
            "input": str(input_path),
            "output": str(output_path),
            "target": {
                "source": target_source,
                "visible_ratio": round(target_ratio, 6),
                "visible_side": target_visible_side,
            },
            "source_metrics": source_metrics,
            "reference_metrics": reference_metrics,
            "output_metrics": output_metrics,
        }
    )
    return 0


def command_verify_build_watch(args: argparse.Namespace) -> int:
    build_rs = Path(args.build_rs)
    if not build_rs.is_file():
        raise IconInputError("missing-build-rs", "build_rs", "build.rs does not exist: {0}".format(build_rs))
    contents = build_rs.read_text(encoding="utf-8")
    checks: List[Dict[str, Any]] = []
    for watch_path in args.watch:
        declaration = "cargo:rerun-if-changed={0}".format(watch_path)
        checks.append({"watch": watch_path, "declaration": declaration, "present": declaration in contents})
    ok = all(bool(check["present"]) for check in checks)
    emit(
        {
            "ok": ok,
            "context_id": "tauri-app-icon/verify-build-watch",
            "build_rs": str(build_rs),
            "checks": checks,
        }
    )
    return 0 if ok else 1


def matching_embeddings(source: Path, build_out: Path) -> Iterable[Path]:
    source_size = source.stat().st_size
    source_digest = sha256(source)
    for candidate in build_out.rglob("*"):
        if not candidate.is_file() or candidate.stat().st_size != source_size:
            continue
        if sha256(candidate) == source_digest:
            yield candidate


def command_verify_embed(args: argparse.Namespace) -> int:
    source = Path(args.source_icns)
    build_out = Path(args.build_out)
    if not source.is_file():
        raise IconInputError("missing-source-icns", "source_icns", "source ICNS does not exist: {0}".format(source))
    if not build_out.is_dir():
        raise IconInputError("missing-build-output", "build_out", "build output directory does not exist: {0}".format(build_out))
    matches = list(matching_embeddings(source, build_out))
    source_digest = sha256(source)
    emit(
        {
            "ok": bool(matches),
            "context_id": "tauri-app-icon/verify-embed",
            "source_icns": str(source),
            "sha256": source_digest,
            "matches": [str(path) for path in matches],
            "status": "runtime_embedded" if matches else "resource_only_or_stale_build",
        }
    )
    return 0 if matches else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure, normalize, and verify Tauri macOS app-icon evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    measure = subparsers.add_parser("measure", help="measure a square image alpha envelope")
    measure.add_argument("--input", required=True, help="source PNG or other Pillow-readable image")
    measure.add_argument("--alpha-threshold", type=alpha_threshold, default=1)
    measure.set_defaults(handler=command_measure)

    normalize = subparsers.add_parser("normalize", help="normalize an image to a reference alpha envelope")
    normalize.add_argument("--input", required=True, help="source square image")
    normalize.add_argument("--output", required=True, help="new PNG output path")
    target = normalize.add_mutually_exclusive_group(required=True)
    target.add_argument("--reference", help="square reference image used to derive visible ratio")
    target.add_argument("--target-visible-ratio", type=visible_ratio)
    normalize.add_argument("--size", type=positive_size, help="square PNG output size; defaults to input size")
    normalize.add_argument("--alpha-threshold", type=alpha_threshold, default=1)
    normalize.add_argument("--force", action="store_true", help="allow overwriting an existing output")
    normalize.set_defaults(handler=command_normalize)

    verify_watch = subparsers.add_parser("verify-build-watch", help="check explicit Cargo icon inputs")
    verify_watch.add_argument("--build-rs", required=True, help="target project build.rs")
    verify_watch.add_argument("--watch", action="append", required=True, help="relative icon path expected in a rerun declaration")
    verify_watch.set_defaults(handler=command_verify_build_watch)

    verify_embed = subparsers.add_parser("verify-embed", help="match source ICNS bytes in Cargo build output")
    verify_embed.add_argument("--source-icns", required=True, help="generated source ICNS")
    verify_embed.add_argument("--build-out", required=True, help="target/debug/build directory")
    verify_embed.set_defaults(handler=command_verify_embed)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except IconInputError as error:
        return fail(error)
    except OSError as error:
        return fail(IconInputError("filesystem", "filesystem", str(error)))


if __name__ == "__main__":
    raise SystemExit(main())
