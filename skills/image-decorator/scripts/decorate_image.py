#!/usr/bin/env python3
"""Add an editorial caption bar and brand logo beneath an existing image."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CAPTION = "Powered by lovstudio.ai/skill/image-decorator"
DEFAULT_LOGO = SKILL_DIR / "assets" / "lovstudio-logo.png"
DEFAULT_FONT = SKILL_DIR / "assets" / "NotoSansSC-VariableFont_wght.ttf"
DEFAULT_PROFILE_CANDIDATES = (
    Path.home() / ".lovstudio" / "skills" / "profile.json",
    Path.home() / ".skill-publisher" / "skills" / "profile.json",
    Path.home() / ".config" / "agent-skills" / "profile.json",
)
SUPPORTED_OUTPUTS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_STYLES = {"editorial-caption", "screenshot-caption"}


class DecoratorError(RuntimeError):
    pass


def parse_hex_color(value: str) -> tuple[int, int, int, int]:
    raw = value.strip().lstrip("#")
    if len(raw) not in (6, 8) or not re.fullmatch(r"[0-9A-Fa-f]+", raw):
        raise argparse.ArgumentTypeError("颜色必须是 6 或 8 位十六进制值")
    if len(raw) == 6:
        raw += "FF"
    return tuple(int(raw[index : index + 2], 16) for index in range(0, 8, 2))


def profile_path(explicit: Path | None) -> Path | None:
    if explicit:
        return explicit.expanduser()
    configured = os.environ.get("SKILL_PROFILE_PATH") or os.environ.get("SKILLS_PROFILE_PATH")
    if configured:
        return Path(os.path.expandvars(configured)).expanduser()
    return next((path for path in DEFAULT_PROFILE_CANDIDATES if path.is_file()), None)


def read_profile(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DecoratorError(f"无法读取 Profile：{exc}") from exc
    if not isinstance(value, dict):
        raise DecoratorError("Profile 顶层必须是 object")
    return value


def nested_mapping(root: dict[str, Any], *parts: str) -> dict[str, Any]:
    current: Any = root
    for part in parts:
        if not isinstance(current, dict):
            return {}
        current = current.get(part)
    return current if isinstance(current, dict) else {}


def resolve_caption(explicit: str | None, profile: dict[str, Any]) -> tuple[str, str]:
    if explicit is not None and explicit.strip():
        return explicit.strip(), "explicit"
    records = nested_mapping(profile, "skills", "lov-image-decorator", "records")
    recorded = records.get("default_caption")
    if isinstance(recorded, str) and recorded.strip():
        return recorded.strip(), "profile"
    return DEFAULT_CAPTION, "fallback"


def local_logo_candidate(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.startswith("file://"):
        raw = raw[7:]
    path = Path(os.path.expandvars(raw)).expanduser()
    return path if path.is_file() and path.suffix.lower() in SUPPORTED_OUTPUTS else None


def resolve_logo(explicit: Path | None, profile: dict[str, Any]) -> tuple[Path, str]:
    if explicit:
        path = explicit.expanduser()
        if not path.is_file():
            raise DecoratorError(f"Logo 不存在：{path}")
        return path, "explicit"
    records = nested_mapping(profile, "skills", "lov-image-decorator", "records")
    recorded = local_logo_candidate(records.get("logo_path"))
    if recorded:
        return recorded, "profile"
    brand = profile.get("brand") if isinstance(profile.get("brand"), dict) else {}
    profiled = local_logo_candidate(brand.get("logo"))
    if profiled:
        return profiled, "brand-profile"
    if not DEFAULT_LOGO.is_file():
        raise DecoratorError("缺少内置 Logo：assets/lovstudio-logo.png")
    return DEFAULT_LOGO, "bundled"


def load_image(path: Path, label: str) -> Image.Image:
    if not path.is_file():
        raise DecoratorError(f"{label}不存在：{path}")
    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGBA")
    except (OSError, ValueError) as exc:
        raise DecoratorError(f"无法读取{label}：{exc}") from exc
    if image.width < 64 or image.height < 64:
        raise DecoratorError(f"{label}尺寸过小：{image.width}×{image.height}")
    return image


def tokenise(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9._:/+\-]*|\s+|.", text, flags=re.DOTALL)


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in tokenise(text):
        if token.isspace() and not current:
            continue
        candidate = current + token
        if current and text_width(draw, candidate, font) > max_width:
            lines.append(current.rstrip())
            current = token.lstrip()
        else:
            current = candidate
    if current.strip():
        lines.append(current.rstrip())
    return lines or [text]


def fit_caption(
    draw: ImageDraw.ImageDraw,
    caption: str,
    font_path: Path,
    requested_size: int,
    requested_weight: int,
    max_width: int,
    max_lines: int,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    if not font_path.is_file():
        raise DecoratorError(f"字体不存在：{font_path}")
    minimum = max(12, round(requested_size * 0.68))
    for size in range(requested_size, minimum - 1, -1):
        font = ImageFont.truetype(str(font_path), size=size)
        try:
            axes = font.get_variation_axes()
            if len(axes) == 1 and axes[0].get("name") == b"Weight":
                font.set_variation_by_axes([requested_weight])
        except (AttributeError, OSError):
            pass
        lines = wrap_text(draw, caption, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    raise DecoratorError(f"caption 过长，缩小字号后仍超过 {max_lines} 行")


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def dominant_opaque_edge_color(image: Image.Image) -> tuple[int, int, int, int]:
    width, height = image.size
    samples: list[tuple[int, int, int]] = []
    step = max(1, min(width, height) // 256)
    for x in range(0, width, step):
        for y in (0, height - 1):
            red, green, blue, alpha = image.getpixel((x, y))
            if alpha >= 250:
                samples.append((red // 8 * 8, green // 8 * 8, blue // 8 * 8))
    for y in range(0, height, step):
        for x in (0, width - 1):
            red, green, blue, alpha = image.getpixel((x, y))
            if alpha >= 250:
                samples.append((red // 8 * 8, green // 8 * 8, blue // 8 * 8))
    if not samples:
        return 255, 255, 255, 255
    red, green, blue = Counter(samples).most_common(1)[0][0]
    return red, green, blue, 255


def normalize_screenshot(
    image: Image.Image,
    background: tuple[int, int, int, int] | None,
) -> tuple[Image.Image, tuple[int, int, int, int], tuple[int, int, int, int], str]:
    width, height = image.size
    alpha = image.getchannel("A")
    if alpha.getextrema() == (255, 255):
        return image, (0, 0, width, height), (0, 0, 0, 0), "none"

    opaque = alpha.point(lambda value: 255 if value >= 250 else 0)
    crop = opaque.getbbox() or (0, 0, width, height)
    normalized = image.crop(crop)
    fill = background or dominant_opaque_edge_color(normalized)
    pixels = normalized.load()
    for y in range(normalized.height):
        left = next(
            (x for x in range(normalized.width) if pixels[x, y][3] >= 250),
            None,
        )
        if left is None:
            continue
        right = next(
            (x for x in range(normalized.width - 1, -1, -1) if pixels[x, y][3] >= 250),
            left,
        )
        left_color = (*pixels[left, y][:3], 255)
        right_color = (*pixels[right, y][:3], 255)
        for x in range(left):
            pixels[x, y] = left_color
        for x in range(right + 1, normalized.width):
            pixels[x, y] = right_color
    flattened = Image.new("RGBA", normalized.size, fill)
    flattened.alpha_composite(normalized)
    return flattened, crop, fill, "opaque-bounds-flatten"


def save_atomic(image: Image.Image, output: Path, quality: int) -> None:
    suffix = output.suffix.lower()
    if suffix not in SUPPORTED_OUTPUTS:
        raise DecoratorError("输出格式只支持 PNG、JPEG 或 WebP")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=suffix, delete=False) as handle:
            temporary_name = handle.name
        temporary = Path(temporary_name)
        if suffix in {".jpg", ".jpeg"}:
            flattened = Image.new("RGB", image.size, (249, 249, 247))
            flattened.paste(image, mask=image.getchannel("A"))
            flattened.save(temporary, format="JPEG", quality=quality, optimize=True)
        elif suffix == ".webp":
            image.save(temporary, format="WEBP", quality=quality, method=6)
        else:
            image.save(temporary, format="PNG", optimize=True)
        temporary.replace(output)
    finally:
        if temporary_name:
            temporary = Path(temporary_name)
            if temporary.exists():
                temporary.unlink()


def decorate(args: argparse.Namespace) -> dict[str, Any]:
    input_path = args.input.expanduser().resolve()
    output = (args.output or input_path.with_name(f"{input_path.stem}.decorated.png")).expanduser().resolve()
    if input_path == output:
        raise DecoratorError("输出路径不能覆盖输入图片")

    profile = read_profile(profile_path(args.profile))
    caption, caption_source = resolve_caption(args.caption, profile)
    logo_path, logo_source = resolve_logo(args.logo, profile)
    source = load_image(input_path, "输入图片")
    logo = load_image(logo_path, "Logo")

    input_width, input_height = source.size
    screenshot_crop = (0, 0, input_width, input_height)
    screenshot_background = (0, 0, 0, 0)
    alpha_treatment = "none"
    if args.style == "screenshot-caption":
        source, screenshot_crop, screenshot_background, alpha_treatment = normalize_screenshot(
            source,
            args.screenshot_background,
        )

    width, image_height = source.size
    if args.style == "screenshot-caption":
        outer_padding = 0
        radius = 0
    else:
        outer_padding = args.outer_padding or max(18, min(64, round(width * 0.018)))
        radius = args.corner_radius or max(24, min(80, round(width * 0.028)))
    base_font_size = args.caption_size or max(18, min(48, round(width * 0.022)))
    bar_padding_x = max(24, round(width * 0.024))
    bar_padding_y = max(18, round(base_font_size * 0.72))
    requested_bar_height = args.bar_height or max(92, round(width * 0.095))
    logo_size = args.logo_size or max(28, round(requested_bar_height * 0.42))
    available_text_width = width - bar_padding_x * 2 - logo_size - max(24, round(width * 0.018))
    if available_text_width < width * 0.35:
        raise DecoratorError("图片过窄，无法同时容纳 caption 与 Logo")

    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    font_path = (args.font or DEFAULT_FONT).expanduser()
    font, lines = fit_caption(
        probe,
        caption,
        font_path,
        base_font_size,
        args.caption_weight,
        available_text_width,
        args.max_lines,
    )
    ascent, descent = font.getmetrics()
    line_height = max(ascent + descent, round(font.size * 1.35))
    caption_height = line_height * len(lines)
    bar_height = max(requested_bar_height, caption_height + bar_padding_y * 2)

    frame_color = args.frame_color
    bar_color = args.bar_color
    text_color = args.text_color
    card_height = image_height + bar_height
    canvas_size = (width + outer_padding * 2, card_height + outer_padding * 2)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    if args.style == "editorial-caption":
        frame = Image.new("RGBA", canvas_size, frame_color)
        canvas.paste(frame, (0, 0), rounded_mask(canvas_size, radius))
    canvas.alpha_composite(source, (outer_padding, outer_padding))

    bar = Image.new("RGBA", (width, bar_height), bar_color)
    bar_draw = ImageDraw.Draw(bar)
    text_top = (bar_height - caption_height) // 2
    for index, line in enumerate(lines):
        bar_draw.text(
            (bar_padding_x, text_top + index * line_height),
            line,
            font=font,
            fill=text_color,
            anchor="la",
        )

    logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
    logo_x = width - bar_padding_x - logo.width
    logo_y = (bar_height - logo.height) // 2
    bar.alpha_composite(logo, (logo_x, logo_y))
    canvas.alpha_composite(bar, (outer_padding, outer_padding + image_height))

    save_atomic(canvas, output, args.quality)
    data = output.read_bytes()
    return {
        "ok": True,
        "output": str(output),
        "format": output.suffix.lower().lstrip(".").replace("jpeg", "jpg"),
        "width": canvas.width,
        "height": canvas.height,
        "input_width": input_width,
        "input_height": input_height,
        "content_width": width,
        "content_height": image_height,
        "caption": caption,
        "caption_source": caption_source,
        "caption_lines": len(lines),
        "logo_source": logo_source,
        "style": args.style,
        "decoration": {
            "frame": "warm-rounded" if args.style == "editorial-caption" else "none",
            "source_crop": list(screenshot_crop),
            "alpha_treatment": alpha_treatment,
            "screenshot_background": list(screenshot_background),
            "outer_padding": outer_padding,
            "corner_radius": radius,
            "bar_height": bar_height,
            "caption_size": font.size,
            "caption_weight": args.caption_weight,
            "logo_width": logo.width,
            "logo_height": logo.height,
        },
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Existing PNG, JPEG, or WebP image")
    parser.add_argument("--output", "-o", type=Path, help="Output PNG, JPEG, or WebP path")
    parser.add_argument("--caption", help="Caption shown in the bottom decoration")
    parser.add_argument("--logo", type=Path, help="Local raster logo; defaults to Profile or bundled LovStudio logo")
    parser.add_argument("--font", type=Path, help="Local TrueType/OpenType font")
    parser.add_argument("--profile", type=Path, help="Shared user-profile JSON")
    parser.add_argument(
        "--style",
        choices=sorted(SUPPORTED_STYLES),
        default="editorial-caption",
        help="Framed artwork treatment or borderless screenshot treatment",
    )
    parser.add_argument(
        "--screenshot-background",
        type=parse_hex_color,
        default=None,
        help="Background used after trimming transparent screenshot shadows; defaults to an edge-derived color",
    )
    parser.add_argument("--outer-padding", type=int, default=None)
    parser.add_argument("--corner-radius", type=int, default=None)
    parser.add_argument("--bar-height", type=int, default=None)
    parser.add_argument("--caption-size", type=int, default=None)
    parser.add_argument("--caption-weight", type=int, default=500)
    parser.add_argument("--logo-size", type=int, default=None)
    parser.add_argument("--max-lines", type=int, default=3)
    parser.add_argument("--quality", type=int, default=92)
    parser.add_argument("--frame-color", type=parse_hex_color, default=parse_hex_color("#F9F9F7"))
    parser.add_argument("--bar-color", type=parse_hex_color, default=parse_hex_color("#181818"))
    parser.add_argument("--text-color", type=parse_hex_color, default=parse_hex_color("#F9F9F7"))
    parser.add_argument("--json", action="store_true", help="Print machine-readable result")
    return parser


def validate_numeric_args(args: argparse.Namespace) -> None:
    for name in ("outer_padding", "corner_radius", "bar_height", "caption_size", "logo_size"):
        value = getattr(args, name)
        if value is not None and value <= 0:
            raise DecoratorError(f"--{name.replace('_', '-')} 必须大于 0")
    if not 1 <= args.max_lines <= 6:
        raise DecoratorError("--max-lines 必须在 1 到 6 之间")
    if not 100 <= args.caption_weight <= 900:
        raise DecoratorError("--caption-weight 必须在 100 到 900 之间")
    if not 1 <= args.quality <= 100:
        raise DecoratorError("--quality 必须在 1 到 100 之间")
    if args.style == "screenshot-caption" and (
        args.outer_padding is not None or args.corner_radius is not None
    ):
        raise DecoratorError("screenshot-caption 不接受 --outer-padding 或 --corner-radius")
    if args.style != "screenshot-caption" and args.screenshot_background is not None:
        raise DecoratorError("--screenshot-background 仅适用于 screenshot-caption")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        validate_numeric_args(args)
        result = decorate(args)
    except DecoratorError as exc:
        context_id = f"lov-image-decorator-{uuid.uuid4().hex[:8]}"
        error = {"ok": False, "context_id": context_id, "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
