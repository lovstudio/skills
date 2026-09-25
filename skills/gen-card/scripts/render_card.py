#!/usr/bin/env python3
"""Render a structured editorial card to self-contained HTML and high-resolution PNG."""

from __future__ import annotations

import argparse
import base64
import binascii
import functools
import html
import http.server
import json
import mimetypes
import os
import re
import struct
import subprocess
import tempfile
import threading
import urllib.parse
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets" / "art-system-card.template.html"
MODERN_SCREENSHOT = SKILL_ROOT / "assets" / "modern-screenshot.js"
DEFAULT_PROFILE = Path.home() / ".lovstudio" / "skills" / "profile.json"
CHROME_CANDIDATES = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/chromium-browser"),
)


class CardError(RuntimeError):
    """A user-correctable card input or rendering error."""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CardError(f"Cannot read JSON input {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CardError("Card input must be a JSON object")
    return value


def load_profile(explicit: str | None) -> dict[str, Any]:
    raw = explicit or os.environ.get("SKILL_PROFILE_PATH")
    path = Path(os.path.expandvars(raw)).expanduser() if raw else DEFAULT_PROFILE
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CardError(f"Cannot read shared profile {path}: {exc}") from exc
    return value if isinstance(value, dict) else {}


def nested(mapping: dict[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def resolve_path(raw: str, base: Path) -> Path:
    expanded = Path(os.path.expandvars(raw)).expanduser()
    return expanded.resolve() if expanded.is_absolute() else (base / expanded).resolve()


def data_url(path: Path) -> str:
    if not path.is_file():
        raise CardError(f"Asset does not exist: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def require_text(card: dict[str, Any], field: str) -> str:
    value = card.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CardError(f"Missing required text field: {field}")
    return value.strip()


def validate(card: dict[str, Any], source: Path) -> None:
    template = card.get("template", "art-system-card")
    if template != "art-system-card":
        raise CardError("Supported template is currently: art-system-card")
    for field in ("title", "subtitle", "background", "prompt"):
        require_text(card, field)
    visual = card.get("visual")
    if not isinstance(visual, dict) or not isinstance(visual.get("path"), str):
        raise CardError("visual.path is required")
    visual_path = resolve_path(visual["path"], source.parent)
    if not visual_path.is_file():
        raise CardError(f"Visual asset does not exist: {visual_path}")
    scenarios = card.get("scenarios")
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 6:
        raise CardError("scenarios must contain 1-6 items")
    if not all(isinstance(item, str) and item.strip() for item in scenarios):
        raise CardError("every scenario must be non-empty text")
    ratings = card.get("ratings")
    if not isinstance(ratings, list) or not 1 <= len(ratings) <= 5:
        raise CardError("ratings must contain 1-5 items")
    for index, rating in enumerate(ratings):
        if not isinstance(rating, dict):
            raise CardError(f"ratings[{index}] must be an object")
        if not isinstance(rating.get("label"), str) or not rating["label"].strip():
            raise CardError(f"ratings[{index}].label is required")
        score = rating.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
            raise CardError(f"ratings[{index}].score must be an integer from 1 to 5")


def stars(score: int) -> str:
    return "★" * score + "☆" * (5 - score)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "card"


def public_site(value: str) -> str:
    return re.sub(r"^https?://", "", value.strip()).rstrip("/")


def prompt_markup(value: str) -> str:
    escaped = html.escape(value)
    return escaped.replace("[SUBJECT]", "<strong>[SUBJECT]</strong>", 1)


def rating_markup(ratings: list[dict[str, Any]]) -> str:
    blocks = []
    for rating in ratings:
        score = int(rating["score"])
        note = str(rating.get("note", "")).strip()
        note_markup = f'<span class="rating-note">{html.escape(note)}</span>' if note else ""
        blocks.append(
            '<div class="info-item rating">'
            f'<span class="info-key">{html.escape(rating["label"])}</span>'
            f'<span class="stars" role="img" aria-label="{score} 星，满分 5 星">{stars(score)}</span>'
            f'{note_markup}'
            "</div>"
        )
    return "".join(blocks)


def render_html(card: dict[str, Any], source: Path, profile: dict[str, Any], scale: int) -> str:
    if not TEMPLATE.is_file() or not MODERN_SCREENSHOT.is_file():
        raise CardError("Required assets are missing under assets/")
    template = TEMPLATE.read_text(encoding="utf-8")
    visual = card["visual"]
    visual_path = resolve_path(visual["path"], source.parent)
    visual_url = data_url(visual_path)

    profile_brand = profile.get("brand") if isinstance(profile.get("brand"), dict) else {}
    skill_records = nested(profile, "skills", "lov-gen-card", "records")
    skill_records = skill_records if isinstance(skill_records, dict) else {}
    supplied_brand = card.get("brand") if isinstance(card.get("brand"), dict) else {}
    brand_enabled = supplied_brand.get("enabled", True) is not False
    brand_name = str(
        supplied_brand.get("name")
        or skill_records.get("brand_name")
        or profile_brand.get("name")
        or ""
    ).strip()
    brand_site = str(
        supplied_brand.get("site")
        or skill_records.get("brand_site")
        or profile_brand.get("site")
        or ""
    ).strip()
    logo_raw = supplied_brand.get("logo") or profile_brand.get("logo")
    logo_markup = ""
    if brand_enabled and isinstance(logo_raw, str) and logo_raw.strip():
        logo_path = resolve_path(logo_raw, source.parent)
        logo_markup = (
            f'<img class="brand-logo" src="{data_url(logo_path)}" '
            f'alt="{html.escape(brand_name or "品牌 Logo")}">'
        )
    elif brand_enabled and brand_name:
        logo_markup = f'<span class="brand-wordmark">{html.escape(brand_name)}</span>'

    series = card.get("series") if isinstance(card.get("series"), dict) else {}
    series_name = str(series.get("name") or skill_records.get("series_name") or "Art System Card")
    series_subtitle = str(series.get("subtitle") or skill_records.get("series_subtitle") or "艺术风格图鉴")
    number = str(card.get("number", "01")).strip()
    category = str(card.get("category", "Visual reference")).strip()
    scenarios = [str(item).strip() for item in card["scenarios"]]
    scenarios_markup = " · ".join(html.escape(item) for item in scenarios)
    site_mark = public_site(brand_site) if brand_site else html.escape(brand_name)
    if site_mark:
        site_mark = f"{html.escape(site_mark)} · editor rating / 5"
    else:
        site_mark = "editor rating / 5"

    theme = card.get("theme") if isinstance(card.get("theme"), dict) else {}
    colors = {
        "accent": theme.get("accent", "#d84b35"),
        "accent_2": theme.get("accent_2", "#15569a"),
        "accent_3": theme.get("accent_3", "#eabf20"),
    }
    for key, value in colors.items():
        if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise CardError(f"theme.{key} must use a six-digit hex color")

    title = require_text(card, "title")
    subtitle = require_text(card, "subtitle")
    long_title = len(title) > 20 or len(subtitle) > 12
    replacements = {
        "@@LANG@@": html.escape(str(card.get("language", "zh-CN"))),
        "@@PAGE_TITLE@@": html.escape(f"{series_name} {number} · {title}"),
        "@@DESCRIPTION@@": html.escape(str(card.get("description", f"{title} 卡片"))),
        "@@ACCENT@@": colors["accent"],
        "@@ACCENT_2@@": colors["accent_2"],
        "@@ACCENT_3@@": colors["accent_3"],
        "@@SERIES_NAME@@": html.escape(series_name),
        "@@SERIES_SUBTITLE@@": html.escape(series_subtitle),
        "@@NUMBER@@": html.escape(number),
        "@@CARD_CLASS@@": " is-multi-rating" if len(card["ratings"]) > 2 else "",
        "@@TITLE_CLASS@@": " is-long" if long_title else "",
        "@@TITLE@@": html.escape(title),
        "@@SUBTITLE@@": html.escape(subtitle),
        "@@VISUAL_URL@@": visual_url,
        "@@VISUAL_ALT@@": html.escape(str(visual.get("alt", f"{subtitle}视觉语言示意"))),
        "@@CAPTION_LEFT@@": html.escape(str(visual.get("caption_left", "AI-generated visual study"))),
        "@@CAPTION_RIGHT@@": html.escape(str(visual.get("caption_right", "形态示意，并非历史作品"))),
        "@@BACKGROUND_LABEL@@": html.escape(str(card.get("background_label", "Background"))),
        "@@BACKGROUND_LABEL_SECONDARY@@": html.escape(str(card.get("background_label_secondary", "背景"))),
        "@@BACKGROUND@@": html.escape(require_text(card, "background")),
        "@@PROMPT_LABEL@@": html.escape(str(card.get("prompt_label", "Prompt"))),
        "@@PROMPT_LABEL_SECONDARY@@": html.escape(str(card.get("prompt_label_secondary", "Midjourney"))),
        "@@PROMPT@@": prompt_markup(require_text(card, "prompt")),
        "@@PROFILE_LABEL@@": html.escape(str(card.get("profile_label", "Profile"))),
        "@@PROFILE_LABEL_SECONDARY@@": html.escape(str(card.get("profile_label_secondary", "基本信息"))),
        "@@SCENARIO_LABEL@@": html.escape(str(card.get("scenario_label", "适用场景"))),
        "@@SCENARIOS@@": scenarios_markup,
        "@@BASIC_INFO_CLASS@@": " is-multi-rating" if len(card["ratings"]) > 2 else "",
        "@@RATINGS@@": rating_markup(card["ratings"]),
        "@@CATEGORY@@": html.escape(category),
        "@@SITE_MARK@@": site_mark,
        "@@LOGO@@": logo_markup,
        "@@PROMPT_JSON@@": json.dumps(require_text(card, "prompt"), ensure_ascii=False).replace("</", "<\/"),
        "@@DOWNLOAD_NAME_JSON@@": json.dumps(f"{slugify(title)}-card.png"),
        "@@EXPORT_SCALE@@": str(scale),
        "@@MODERN_SCREENSHOT@@": MODERN_SCREENSHOT.read_text(encoding="utf-8"),
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    unresolved = sorted(set(re.findall(r"@@[A-Z0-9_]+@@", template)))
    if unresolved:
        raise CardError("Unresolved template tokens: " + ", ".join(unresolved))
    return template


def find_chrome(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return path
        raise CardError(f"Chrome executable does not exist: {path}")
    env_path = os.environ.get("CHROME_PATH")
    if env_path and Path(env_path).expanduser().is_file():
        return Path(env_path).expanduser()
    for candidate in CHROME_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise CardError("PNG export requires Chrome/Chromium; set CHROME_PATH or use --chrome")


def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise CardError("Browser export did not return a PNG")
    return struct.unpack(">II", data[16:24])


def export_png(source: Path, output: Path, chrome: Path, scale: int) -> dict[str, Any]:
    page = source.read_text(encoding="utf-8")
    exporter = f"""
<pre id="png-data">pending</pre>
<script>
window.addEventListener('load', function exportForAudit() {{
  Promise.resolve(window.__CARD_READY_PROMISE__).then(function () {{
    var node = document.getElementById('capture');
    modernScreenshot.domToPng(node, {{
      width: 900,
      height: 1350,
      scale: {scale},
      backgroundColor: '#fffdf8'
    }}).then(function (url) {{
      document.getElementById('png-data').textContent = url.split(',')[1];
    }}).catch(function (error) {{
      document.getElementById('png-data').textContent = 'FAIL:' + (error && error.message ? error.message : error);
    }});
  }});
}});
</script>
"""
    page = page.replace("</body>", exporter + "</body>", 1)
    temporary = tempfile.NamedTemporaryFile(
        "w", suffix=".html", dir=source.parent, delete=False, encoding="utf-8"
    )
    result: subprocess.CompletedProcess[str] | None = None
    try:
        temporary.write(page)
        temporary.close()
        handler = functools.partial(QuietHandler, directory=str(source.parent))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            relative = Path(temporary.name).relative_to(source.parent)
            url = f"http://127.0.0.1:{server.server_port}/" + urllib.parse.quote(str(relative))
            command = [
                str(chrome), "--headless=new", "--disable-gpu", "--no-sandbox",
                "--window-size=1280,1600", "--virtual-time-budget=15000", "--dump-dom", url,
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=True)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise CardError(f"Headless browser export failed: {exc}") from exc
    finally:
        Path(temporary.name).unlink(missing_ok=True)
    if result is None:
        raise CardError("Headless browser did not return a result")
    match = re.search(r'<pre id="png-data">([^<]+)</pre>', result.stdout)
    if not match:
        raise CardError("Browser output did not contain exported image data")
    encoded = html.unescape(match.group(1)).strip()
    if encoded.startswith("FAIL:"):
        raise CardError(encoded)
    if encoded == "pending":
        raise CardError("Browser export did not finish before DOM capture")
    try:
        data = base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise CardError(
            f"Browser returned invalid PNG data: length={len(encoded)} prefix={encoded[:24]!r}"
        ) from exc
    width, height = png_size(data)
    expected = (900 * scale, 1350 * scale)
    if (width, height) != expected:
        raise CardError(f"PNG size mismatch: got {width}x{height}, expected {expected[0]}x{expected[1]}")
    audit_match = re.search(r'<output id="card-audit">([^<]+)</output>', result.stdout)
    if not audit_match:
        raise CardError("Browser output did not contain card layout audit")
    try:
        audit = json.loads(html.unescape(audit_match.group(1)))
    except json.JSONDecodeError as exc:
        raise CardError(f"Invalid card layout audit: {exc}") from exc
    if (
        audit.get("overflowX", 1) > 0
        or audit.get("overflowY", 1) > 0
        or audit.get("internalOverflowY", 1) > 0
        or audit.get("internalClipY", 1) > 0
    ):
        raise CardError(f"Card content overflows after fitting: {audit}")
    if not audit.get("visualReady"):
        raise CardError("The visual asset did not finish loading")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return {"width": width, "height": height, "bytes": len(data), "layout": audit}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Structured card JSON")
    parser.add_argument("--out", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--name", help="Output basename; defaults to a title-derived slug")
    parser.add_argument("--format", choices=("html", "png", "both"), default="both")
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--profile", help="Shared user-profile/v1 JSON path")
    parser.add_argument("--chrome", help="Chrome/Chromium executable")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        source = args.input.expanduser().resolve()
        card = load_json(source)
        validate(card, source)
        if args.scale not in (1, 2, 3, 4):
            raise CardError("--scale must be 1, 2, 3, or 4")
        if args.validate_only:
            print(f"valid={source}")
            return 0
        profile = load_profile(args.profile)
        output_dir = args.out.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        basename = args.name or slugify(require_text(card, "title"))
        html_path = output_dir / f"{basename}.html"
        html_path.write_text(render_html(card, source, profile, args.scale), encoding="utf-8")
        print(f"html={html_path}")
        if args.format in ("png", "both"):
            png_path = output_dir / f"{basename}.png"
            audit = export_png(html_path, png_path, find_chrome(args.chrome), args.scale)
            print(f"png={png_path}")
            print(f"size={audit['width']}x{audit['height']} bytes={audit['bytes']}")
            print("layout=" + json.dumps(audit["layout"], ensure_ascii=False, sort_keys=True))
        if args.format == "png":
            html_path.unlink(missing_ok=True)
        return 0
    except CardError as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
