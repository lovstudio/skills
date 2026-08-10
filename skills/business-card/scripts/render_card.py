#!/usr/bin/env python3
"""
render_card.py — Generate a professional editorial business card (2:1).

Fills a parameterized HTML template with the user's identity and renders it to
a high-resolution PNG via headless Chrome. The HTML itself is self-contained
(avatar embedded as base64, modern-screenshot vendored) so it also works
standalone in a browser with a click-to-download button.

Usage:
    python3 render_card.py \
        --name "手工川" --latin "Mark Shawn" \
        --brand "LOVSTUDIO.AI" --index "Nº 2026" \
        --tags "背包客,超级开发者,AI / OPC 布道师" \
        --tagline "在 **Agent 时代**，|寻找**人**的意义" \
        --pursuits "旅行,羽毛球,计算机科学,心理学,哲学" \
        --bases "上海 陆家嘴数智港,北京 搜狐大厦清智孵化器" \
        --avatar ./me.png --theme dark-terracotta \
        --out ./output --format both

Notes:
- --tagline: use ** ** to mark accent words, and | to split lines.
- --bases: comma-separated; each gets a pin marker.
- --avatar omitted → a monogram (first glyph of --name) is rendered instead.
- --format: png | html | both (default both).
"""

import argparse
import base64
import html
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE = ASSETS / "template.html"
SCREENSHOT_JS = ASSETS / "modern-screenshot.umd.js"

# ---------------------------------------------------------------- themes
THEMES = {
    "dark-terracotta": {
        "--page": "#0c0a08", "--bg": "#17120d", "--ink": "#ece4d6",
        "--ink-dim": "#b6ab98", "--muted": "#8a7d6c",
        "--terra": "#c9663e", "--terra-deep": "#a64f30",
        "--terra-line": "rgba(201,102,62,.5)", "--hair": "rgba(236,228,214,.13)",
        "--glow1": "rgba(201,102,62,.20)", "--glow2": "rgba(201,102,62,.07)",
        "--wm": "rgba(201,102,62,.045)",
        "--mono-a": "#241a12", "--mono-b": "#3a241a",
    },
    "midnight": {
        "--page": "#080b12", "--bg": "#0f1420", "--ink": "#e6ecf5",
        "--ink-dim": "#aab6c8", "--muted": "#7e8aa0",
        "--terra": "#6f9bd1", "--terra-deep": "#4f76a8",
        "--terra-line": "rgba(111,155,209,.5)", "--hair": "rgba(230,236,245,.12)",
        "--glow1": "rgba(111,155,209,.18)", "--glow2": "rgba(111,155,209,.06)",
        "--wm": "rgba(111,155,209,.05)",
        "--mono-a": "#121b2c", "--mono-b": "#1c2940",
    },
    "ivory": {
        "--page": "#eceae3", "--bg": "#f4f1ea", "--ink": "#1d1a16",
        "--ink-dim": "#4a443b", "--muted": "#6d6557",
        "--terra": "#b8563a", "--terra-deep": "#943f28",
        "--terra-line": "rgba(184,86,58,.55)", "--hair": "rgba(29,26,22,.14)",
        "--glow1": "rgba(184,86,58,.12)", "--glow2": "rgba(184,86,58,.05)",
        "--wm": "rgba(184,86,58,.05)",
        "--mono-a": "#e8e2d4", "--mono-b": "#ded5c2",
    },
}

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    return None


def slugify(s):
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"[^\w一-鿿-]", "", s)
    return s or "card"


def esc(s):
    return html.escape(s, quote=True)


def emphasize(text):
    """Convert **word** -> <em>word</em>, escaping the rest."""
    out, last = [], 0
    for m in re.finditer(r"\*\*(.+?)\*\*", text):
        out.append(esc(text[last:m.start()]))
        out.append("<em>" + esc(m.group(1)) + "</em>")
        last = m.end()
    out.append(esc(text[last:]))
    return "".join(out)


def build_tagline(raw):
    lines = [seg for seg in raw.split("|")]
    return "<br>".join(emphasize(l) for l in lines)


def build_roles(tags):
    items = [esc(t.strip()) for t in tags if t.strip()]
    sep = '<i class="sep"></i>'
    return sep.join(items)


def build_pursuits(items):
    cleaned = [esc(p.strip()) for p in items if p.strip()]
    return '<i class="mid"></i>'.join(cleaned)


def build_bases(items):
    parts = []
    for i, b in enumerate(items):
        b = b.strip()
        if not b:
            continue
        pin = '<i class="pin n"></i>' if parts else '<i class="pin"></i>'
        parts.append(pin + esc(b))
    return "".join(parts)


def build_portrait(avatar, name, caption):
    if avatar:
        p = Path(avatar).expanduser()
        if not p.exists():
            sys.exit(f"avatar not found: {p}")
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        data = base64.b64encode(p.read_bytes()).decode()
        img = f'<img src="data:{mime};base64,{data}" alt="{esc(name)}">'
        cap = f'<div class="pcaption">{esc(caption)}</div>' if caption else ""
        return img + cap
    glyph = esc(name.strip()[:1]) if name.strip() else "·"
    return f'<div class="mono">{glyph}</div>'


def theme_vars(theme):
    t = THEMES.get(theme)
    if not t:
        sys.exit(f"unknown theme: {theme} (choose from {', '.join(THEMES)})")
    body = ";".join(f"{k}:{v}" for k, v in t.items())
    return ".stage,.viewport,.dl-btn,body{" + body + "}"


def render_html(args):
    tpl = TEMPLATE.read_text(encoding="utf-8")
    name = args.name
    latin = f'<p class="latin">{esc(args.latin)}</p>' if args.latin else ""
    repl = {
        "__TITLE__": esc(name) + " · 名片",
        "__THEME_VARS__": theme_vars(args.theme),
        "__WM__": esc(args.watermark or (name.strip()[-1:] if name.strip() else "")),
        "__BRAND__": render_brand(args.brand),
        "__INDEX__": esc(args.index or ""),
        "__PORTRAIT__": build_portrait(args.avatar, name, args.caption),
        "__NAME__": esc(name),
        "__LATIN__": latin,
        "__ROLES__": build_roles(args.tags.split(",")) if args.tags else "",
        "__TAGLINE__": build_tagline(args.tagline) if args.tagline else "",
        "__PURSUITS__": build_pursuits(args.pursuits.split(",")) if args.pursuits else "",
        "__BASES__": build_bases(args.bases.split(",")) if args.bases else "",
        "__SLUG__": slugify(name),
    }
    for k, v in repl.items():
        tpl = tpl.replace(k, v)
    return tpl


def render_brand(brand):
    """Highlight a single dot in a brand like LOVSTUDIO.AI."""
    if not brand:
        return ""
    if "." in brand:
        head, _, tail = brand.partition(".")
        return esc(head) + '<span class="ds">.</span>' + esc(tail)
    return esc(brand)


def screenshot(html_path, png_path, chrome, scale=3):
    """Render full card to PNG by capturing a 1700x900 window then cropping."""
    with tempfile.TemporaryDirectory() as tmp:
        full = Path(tmp) / "full.png"
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--virtual-time-budget=6000", "--run-all-compositor-stages-before-draw",
            f"--force-device-scale-factor={scale}", "--window-size=1700,900",
            f"--screenshot={full}", f"file://{html_path}#shoot",
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        if not full.exists():
            sys.exit("chrome screenshot failed")
        crop(full, png_path, 1600 * scale, 800 * scale)


def crop(src, dst, w, h):
    """Center-crop src to w x h, writing dst. Uses sips (mac) or PIL."""
    if shutil.which("sips"):
        subprocess.run(["sips", "-c", str(h), str(w), str(src), "--out", str(dst)],
                       check=True, capture_output=True)
        return
    try:
        from PIL import Image
    except ImportError:
        sys.exit("need `sips` (macOS) or Pillow (`pip install pillow`) to crop")
    im = Image.open(src)
    W, H = im.size
    left, top = (W - w) // 2, (H - h) // 2
    im.crop((left, top, left + w, top + h)).save(dst)


def main():
    ap = argparse.ArgumentParser(description="Generate an editorial business card (2:1).")
    ap.add_argument("--name", required=True, help="display name (CJK ok)")
    ap.add_argument("--latin", default="", help="secondary/romanized name")
    ap.add_argument("--brand", default="", help="top-left brand text, e.g. LOVSTUDIO.AI")
    ap.add_argument("--index", default="", help="top-right line, e.g. 'STUDIO — Nº 2026'")
    ap.add_argument("--tags", default="", help="comma-separated role tags")
    ap.add_argument("--tagline", default="", help="hero line; **accent**, | splits lines")
    ap.add_argument("--pursuits", default="", help="comma-separated interests (footer left)")
    ap.add_argument("--bases", default="", help="comma-separated locations (footer right)")
    ap.add_argument("--avatar", default="", help="portrait image path (optional)")
    ap.add_argument("--caption", default="", help="portrait caption (optional)")
    ap.add_argument("--watermark", default="", help="giant background glyph (default: last char of name)")
    ap.add_argument("--theme", default="dark-terracotta",
                    help="dark-terracotta | midnight | ivory")
    ap.add_argument("--out", default="./output", help="output directory")
    ap.add_argument("--format", default="both", choices=["png", "html", "both"])
    ap.add_argument("--scale", type=int, default=3, help="PNG scale factor (default 3 -> 4800x2400)")
    args = ap.parse_args()

    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.name)

    html_doc = render_html(args)
    html_path = out / f"{slug}-名片.html"
    html_path.write_text(html_doc, encoding="utf-8")
    # vendored screenshot lib next to the html so the download button works
    shutil.copy(SCREENSHOT_JS, out / "modern-screenshot.umd.js")
    print(f"✓ HTML  {html_path}")

    if args.format in ("png", "both"):
        chrome = find_chrome()
        if not chrome:
            print("⚠ Chrome/Chromium not found — skipping PNG. Open the HTML and click 下载.")
        else:
            png_path = out / f"{slug}-名片.png"
            screenshot(str(html_path), str(png_path), chrome, args.scale)
            print(f"✓ PNG   {png_path}  ({1600*args.scale}x{800*args.scale})")


if __name__ == "__main__":
    main()
