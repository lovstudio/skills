#!/usr/bin/env python3
"""Create a styled QR PNG with Profile-backed preferences and verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

try:
    import qrcode
    from qrcode.constants import (
        ERROR_CORRECT_H,
        ERROR_CORRECT_L,
        ERROR_CORRECT_M,
        ERROR_CORRECT_Q,
    )
    from qrcode.exceptions import DataOverflowError
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.colormasks import SolidFillColorMask
    from qrcode.image.styles.moduledrawers.pil import (
        CircleModuleDrawer,
        GappedSquareModuleDrawer,
        HorizontalBarsDrawer,
        RoundedModuleDrawer,
        SquareModuleDrawer,
        VerticalBarsDrawer,
    )
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    print(
        json.dumps(
            {
                "status": "error",
                "error": "missing dependency",
                "detail": "Install qrcode and Pillow before running this command.",
            }
        ),
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


SKILL_ID = "lov-create-qrcode"
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
PALETTES = {
    "classic": ("#181818", "#F9F9F7"),
    "clay": ("#CC785C", "#F9F9F7"),
    "ink": ("#181818", "#F0EEE6"),
    "olive": ("#5B6A3B", "#F9F9F7"),
}
SHAPES = {
    "square",
    "dots",
    "rounded",
    "extra-rounded",
    "gapped-square",
    "vertical-bars",
    "horizontal-bars",
}
ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}
SAFE_DEFAULTS = {
    "palette": "classic",
    "shape": "rounded",
    "size": 768,
    "error_correction": "M",
    "border": 4,
    "poster": False,
    "show_data": False,
    "title": None,
}


class QrCodeError(Exception):
    """A user-facing QR generation error."""


def default_profile_path() -> Path | None:
    configured = os.environ.get("SKILL_PROFILE_PATH") or os.environ.get(
        "SKILLS_PROFILE_PATH"
    )
    if configured:
        return Path(os.path.expandvars(configured)).expanduser()
    candidates = (
        Path.home() / ".lovstudio" / "skills" / "profile.json",
        Path.home() / ".skill-publisher" / "skills" / "profile.json",
        Path.home() / ".config" / "agent-skills" / "profile.json",
    )
    return next((path for path in candidates if path.exists()), None)


def read_profile(path: Path | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if path is None or not path.exists():
        return {}, {}, {}
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QrCodeError("shared Profile could not be read") from exc
    if not isinstance(profile, dict):
        raise QrCodeError("shared Profile root must be an object")
    skills = profile.get("skills", {})
    skill = skills.get(SKILL_ID, {}) if isinstance(skills, dict) else {}
    records = skill.get("records", {}) if isinstance(skill, dict) else {}
    preferences = profile.get("preferences", {})
    brand = profile.get("brand", {})
    return (
        records if isinstance(records, dict) else {},
        preferences if isinstance(preferences, dict) else {},
        brand if isinstance(brand, dict) else {},
    )


def nested_preferences(preferences: dict[str, Any]) -> dict[str, Any]:
    nested = preferences.get("lov_create_qrcode")
    return nested if isinstance(nested, dict) else preferences


def resolve_value(
    explicit: Any,
    record_key: str,
    shared_key: str,
    fallback_key: str,
    records: dict[str, Any],
    preferences: dict[str, Any],
    cast: Callable[[Any], Any],
) -> tuple[Any, str]:
    if explicit is not None:
        return cast(explicit), "request"
    if record_key in records:
        return cast(records[record_key]), "skill-record"
    shared = nested_preferences(preferences)
    if shared_key in shared:
        return cast(shared[shared_key]), "shared-preferences"
    return cast(SAFE_DEFAULTS[fallback_key]), "safe-default"


def as_text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QrCodeError("a saved text preference is invalid")
    return value.strip()


def as_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return as_text(value)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.casefold() in {"true", "false"}:
        return value.casefold() == "true"
    raise QrCodeError("a saved boolean preference is invalid")


def as_int(value: Any) -> int:
    if isinstance(value, bool):
        raise QrCodeError("a saved numeric preference is invalid")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise QrCodeError("a saved numeric preference is invalid") from exc


def parse_hex(value: str) -> tuple[int, int, int]:
    if not HEX_COLOR_RE.fullmatch(value):
        raise QrCodeError("colors must use six-digit hexadecimal notation")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    values = []
    for component in rgb:
        channel = component / 255
        values.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def contrast_ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def resolve_payload(args: argparse.Namespace) -> str:
    provided = int(args.data is not None) + int(args.stdin) + int(args.input_file is not None)
    if provided != 1:
        raise QrCodeError("provide exactly one payload source: argument, --stdin, or --input-file")
    if args.stdin:
        payload = sys.stdin.read()
    elif args.input_file is not None:
        try:
            payload = args.input_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise QrCodeError("the input file must be readable UTF-8 text") from exc
    else:
        payload = args.data
    if payload is None or not payload:
        raise QrCodeError("the QR payload must not be empty")
    return payload


def module_drawers(shape: str) -> tuple[Any, Any]:
    safe_eye = SquareModuleDrawer()
    if shape == "square":
        return SquareModuleDrawer(), safe_eye
    if shape == "dots":
        return CircleModuleDrawer(), safe_eye
    if shape == "rounded":
        return RoundedModuleDrawer(radius_ratio=0.75), safe_eye
    if shape == "extra-rounded":
        return RoundedModuleDrawer(radius_ratio=1.0), safe_eye
    if shape == "gapped-square":
        return GappedSquareModuleDrawer(size_ratio=0.86), safe_eye
    if shape == "vertical-bars":
        return VerticalBarsDrawer(horizontal_shrink=0.82), safe_eye
    if shape == "horizontal-bars":
        return HorizontalBarsDrawer(vertical_shrink=0.82), safe_eye
    raise QrCodeError("unsupported QR shape")


def build_qr_image(
    payload: str,
    size: int,
    level: str,
    border: int,
    shape: str,
    foreground: tuple[int, int, int],
    background: tuple[int, int, int],
    logo: Path | None,
) -> tuple[Image.Image, int, int]:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_LEVELS[level],
        box_size=10,
        border=border,
    )
    qr.add_data(payload, optimize=20)
    try:
        qr.make(fit=True)
    except DataOverflowError as exc:
        raise QrCodeError("payload exceeds QR capacity for the selected correction level") from exc
    total_modules = qr.modules_count + border * 2
    box_size = size // total_modules
    if box_size < 2:
        raise QrCodeError("requested size is too small for this payload and correction level")
    qr.box_size = box_size
    module_drawer, eye_drawer = module_drawers(shape)
    options: dict[str, Any] = {
        "image_factory": StyledPilImage,
        "module_drawer": module_drawer,
        "eye_drawer": eye_drawer,
        "color_mask": SolidFillColorMask(
            back_color=background,
            front_color=foreground,
        ),
    }
    if logo is not None:
        options["embedded_image_path"] = str(logo)
        options["embedded_image_ratio"] = 0.20
    rendered = qr.make_image(**options).convert("RGB")
    canvas = Image.new("RGB", (size, size), background)
    offset = ((size - rendered.width) // 2, (size - rendered.height) // 2)
    canvas.paste(rendered, offset)
    return canvas, qr.version, box_size


def font_candidates(explicit: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser())
    configured = os.environ.get("QR_FONT_PATH")
    if configured:
        candidates.append(Path(os.path.expandvars(configured)).expanduser())
    candidates.extend(
        [
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ]
    )
    return candidates


def load_font(size: int, explicit: Path | None, text: str) -> ImageFont.ImageFont:
    for path in font_candidates(explicit):
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    if any(ord(character) > 127 for character in text):
        raise QrCodeError("no CJK-capable font was found; provide --font")
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if current and width > max_width:
            lines.append(current)
            current = character
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:4]


def build_poster(
    qr_image: Image.Image,
    title: str | None,
    visible_data: str | None,
    font_path: Path | None,
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    qr_size = qr_image.width
    outer_padding = max(48, qr_size // 12)
    card_padding = max(18, qr_size // 32)
    combined_text = (title or "") + (visible_data or "")
    title_font = load_font(max(24, qr_size // 24), font_path, combined_text)
    caption_font = load_font(max(14, qr_size // 44), font_path, combined_text)
    probe = Image.new("RGB", (16, 16), "#F9F9F7")
    probe_draw = ImageDraw.Draw(probe)
    caption_lines = wrap_text(probe_draw, visible_data or "", caption_font, qr_size)
    title_height = max(68, qr_size // 10) if title else 0
    caption_line_height = max(24, qr_size // 32)
    caption_height = len(caption_lines) * caption_line_height + (28 if caption_lines else 0)
    width = qr_size + outer_padding * 2
    height = outer_padding * 2 + title_height + qr_size + card_padding * 2 + caption_height
    poster = Image.new("RGB", (width, height), "#F9F9F7")
    draw = ImageDraw.Draw(poster)
    draw.rounded_rectangle(
        (1, 1, width - 2, height - 2),
        radius=max(22, width // 36),
        outline="#E8E6DC",
        width=2,
    )
    cursor_y = outer_padding
    if title:
        title_box = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_box[2] - title_box[0]
        draw.text(((width - title_width) // 2, cursor_y), title, fill="#181818", font=title_font)
        line_y = cursor_y + max(42, qr_size // 18)
        draw.rounded_rectangle(
            (width // 2 - 28, line_y, width // 2 + 28, line_y + 3),
            radius=2,
            fill="#CC785C",
        )
        cursor_y += title_height
    card_left = outer_padding - card_padding
    card_top = cursor_y
    card_right = width - outer_padding + card_padding
    card_bottom = card_top + qr_size + card_padding * 2
    draw.rounded_rectangle(
        (card_left, card_top, card_right, card_bottom),
        radius=max(16, qr_size // 32),
        fill="#FFFFFF",
        outline="#E8E6DC",
        width=2,
    )
    qr_left = outer_padding
    qr_top = card_top + card_padding
    poster.paste(qr_image, (qr_left, qr_top))
    cursor_y = card_bottom + 20
    for line in caption_lines:
        line_box = draw.textbbox((0, 0), line, font=caption_font)
        line_width = line_box[2] - line_box[0]
        draw.text(((width - line_width) // 2, cursor_y), line, fill="#6F6E68", font=caption_font)
        cursor_y += caption_line_height
    return poster, (qr_left, qr_top, qr_left + qr_size, qr_top + qr_size)


def structural_verify(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG":
                raise QrCodeError("generated file is not a PNG")
            extrema = image.convert("L").getextrema()
            if extrema[0] == extrema[1]:
                raise QrCodeError("generated PNG has no visible QR contrast")
            return image.size
    except OSError as exc:
        raise QrCodeError("generated PNG could not be read back") from exc


def scan_verify(
    path: Path,
    payload: str,
    qr_crop_box: tuple[int, int, int, int] | None = None,
) -> None:
    try:
        import cv2
    except ImportError as exc:
        raise QrCodeError("scan verification requires OpenCV Python") from exc
    image = cv2.imread(str(path))
    if image is None:
        raise QrCodeError("OpenCV could not open the generated PNG")
    candidates = [image]
    if qr_crop_box is not None:
        left, top, right, bottom = qr_crop_box
        candidates.append(image[top:bottom, left:right])
    saw_different_payload = False
    for candidate in candidates:
        decoded, points, _ = cv2.QRCodeDetector().detectAndDecode(candidate)
        if points is not None and decoded == payload:
            return
        if decoded:
            saw_different_payload = True
    if saw_different_payload:
        raise QrCodeError("decoded QR content does not exactly match the input")
    raise QrCodeError("OpenCV could not decode the generated QR image")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("data", nargs="?", help="UTF-8 payload; prefer --stdin for private values")
    result.add_argument("--stdin", action="store_true", help="Read the exact payload from stdin")
    result.add_argument("--input-file", type=Path, help="Read the exact payload from a UTF-8 file")
    result.add_argument("--output", type=Path, required=True, help="Output PNG path")
    result.add_argument("--profile", type=Path, help="Shared user Profile JSON path")
    result.add_argument("--no-profile", action="store_true", help="Ignore shared Profile values")
    result.add_argument("--palette", choices=sorted(PALETTES))
    result.add_argument("--shape", choices=sorted(SHAPES))
    result.add_argument("--foreground", help="Custom foreground as six-digit hex")
    result.add_argument("--background", help="Custom background as six-digit hex")
    result.add_argument("--size", type=int, help="QR canvas width in pixels, 128 to 4096")
    result.add_argument("--error-correction", choices=sorted(ERROR_LEVELS))
    result.add_argument("--border", type=int, help="Quiet zone in modules, 4 to 16")
    result.add_argument("--poster", action=argparse.BooleanOptionalAction, default=None)
    result.add_argument("--title", help="Optional poster title")
    result.add_argument("--show-data", action=argparse.BooleanOptionalAction, default=None)
    result.add_argument("--font", type=Path, help="Optional title and caption font")
    result.add_argument("--logo", type=Path, help="Optional local Logo; requires H correction")
    result.add_argument("--allow-low-contrast", action="store_true")
    result.add_argument("--verify", choices=("auto", "scan", "structure", "off"), default="auto")
    result.add_argument("--force", action="store_true", help="Replace the exact output target")
    result.add_argument("--json", action="store_true", help="Print a machine-readable receipt")
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    payload = resolve_payload(args)
    profile_path = None if args.no_profile else (args.profile or default_profile_path())
    records, preferences, brand = ({}, {}, {}) if args.no_profile else read_profile(profile_path)
    palette, palette_source = resolve_value(
        args.palette,
        "default_palette",
        "default_palette",
        "palette",
        records,
        preferences,
        as_text,
    )
    if palette not in PALETTES:
        raise QrCodeError("saved palette preference is unsupported")
    shape, shape_source = resolve_value(
        args.shape,
        "default_shape",
        "default_shape",
        "shape",
        records,
        preferences,
        as_text,
    )
    if shape not in SHAPES:
        raise QrCodeError("saved shape preference is unsupported")
    size, size_source = resolve_value(
        args.size,
        "default_size",
        "default_size",
        "size",
        records,
        preferences,
        as_int,
    )
    level, level_source = resolve_value(
        args.error_correction,
        "default_error_correction",
        "default_error_correction",
        "error_correction",
        records,
        preferences,
        as_text,
    )
    border, border_source = resolve_value(
        args.border,
        "default_border",
        "default_border",
        "border",
        records,
        preferences,
        as_int,
    )
    poster, poster_source = resolve_value(
        args.poster,
        "default_poster",
        "default_poster",
        "poster",
        records,
        preferences,
        as_bool,
    )
    show_data, show_data_source = resolve_value(
        args.show_data,
        "default_show_data",
        "default_show_data",
        "show_data",
        records,
        preferences,
        as_bool,
    )
    title_explicit = args.title
    if title_explicit is not None:
        title, title_source = as_text(title_explicit), "request"
    elif "default_title" in records:
        title, title_source = as_optional_text(records["default_title"]), "skill-record"
    elif poster and isinstance(brand.get("name"), str) and brand["name"].strip():
        title, title_source = brand["name"].strip(), "brand-profile"
    else:
        title, title_source = None, "safe-default"

    if not 128 <= size <= 4096:
        raise QrCodeError("size must be between 128 and 4096 pixels")
    if not 4 <= border <= 16:
        raise QrCodeError("border must be between 4 and 16 modules")
    if level not in ERROR_LEVELS:
        raise QrCodeError("saved error-correction preference is unsupported")
    foreground_hex = args.foreground or records.get("default_foreground") or PALETTES[palette][0]
    background_hex = args.background or records.get("default_background") or PALETTES[palette][1]
    foreground = parse_hex(foreground_hex)
    background = parse_hex(background_hex)
    ratio = contrast_ratio(foreground, background)
    if relative_luminance(foreground) >= relative_luminance(background):
        raise QrCodeError("QR foreground must be darker than its background")
    if ratio < 3.0 and not args.allow_low_contrast:
        raise QrCodeError("QR contrast is below 3.0; choose safer colors or explicitly allow it")
    if show_data and not poster:
        raise QrCodeError("--show-data requires poster mode")
    logo = args.logo.expanduser().resolve() if args.logo else None
    if logo is not None:
        if not logo.is_file():
            raise QrCodeError("the Logo file does not exist")
        if level != "H":
            raise QrCodeError("Logo embedding requires H error correction")

    output = args.output.expanduser().resolve()
    if output.suffix.casefold() != ".png":
        raise QrCodeError("output must use a .png extension")
    if output.exists() and not args.force:
        raise QrCodeError("output already exists; choose another path or use --force")
    output.parent.mkdir(parents=True, exist_ok=True)

    qr_image, qr_version, box_size = build_qr_image(
        payload,
        size,
        level,
        border,
        shape,
        foreground,
        background,
        logo,
    )
    qr_crop_box: tuple[int, int, int, int] | None = None
    if poster:
        final_image, qr_crop_box = build_poster(
            qr_image,
            title,
            payload if show_data else None,
            args.font,
        )
    else:
        final_image = qr_image

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent,
            prefix=f".{output.stem}.",
            suffix=".png",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
        final_image.save(temporary_path, format="PNG", optimize=True)
        width, height = structural_verify(temporary_path)
        verification = "off"
        if args.verify == "structure":
            verification = "structure"
        elif args.verify == "scan":
            scan_verify(temporary_path, payload, qr_crop_box)
            verification = "scan"
        elif args.verify == "auto":
            try:
                scan_verify(temporary_path, payload, qr_crop_box)
                verification = "scan"
            except QrCodeError as exc:
                if "requires OpenCV" not in str(exc):
                    raise
                verification = "structure"
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    payload_bytes = payload.encode("utf-8")
    return {
        "status": "created",
        "output": str(output),
        "format": "PNG",
        "width": width,
        "height": height,
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "payload_bytes": len(payload_bytes),
        "payload_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "payload_disclosed": bool(show_data),
        "palette": palette,
        "foreground": foreground_hex.upper(),
        "background": background_hex.upper(),
        "contrast_ratio": round(ratio, 3),
        "shape": shape,
        "size": size,
        "error_correction": level,
        "border_modules": border,
        "qr_version": qr_version,
        "module_pixels": box_size,
        "poster": poster,
        "logo_embedded": logo is not None,
        "verification": verification,
        "profile_used": bool(profile_path and profile_path.exists()),
        "sources": {
            "palette": palette_source,
            "shape": shape_source,
            "size": size_source,
            "error_correction": level_source,
            "border": border_source,
            "poster": poster_source,
            "show_data": show_data_source,
            "title": title_source,
        },
    }


def main() -> int:
    args = parser().parse_args()
    try:
        result = run(args)
    except (OSError, QrCodeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": str(exc),
                    "context_id": "lov-create-qrcode/generate",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(result["output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
