#!/usr/bin/env python3
"""Render a distilled business card from a JSON layout spec.

The spec describes each card side as absolutely positioned blocks (name, text,
contacts, image, qr, rect) on a fixed canvas. The script writes one
self-contained HTML file (all assets inlined as data URIs), runs a layout check
in headless Chrome, then screenshots the front, back and stacked views.

usage:
  render_card.py SPEC.json --out-dir DIR --version v0.1
                 [--stem NAME] [--date YYYY-MM-DD] [--sides front,back,stack]
                 [--scale 3] [--chrome PATH] [--html-only] [--force]

exit codes: 0 rendered and layout clean, 1 error, 2 refused to overwrite,
3 rendered but the layout check reported issues.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import mimetypes
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

# Lucide icons (ISC license), inner SVG markup on a 24x24 stroke grid.
ICONS = {
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "smartphone": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "at-sign": '<circle cx="12" cy="12" r="4"/><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "map-pin": '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "book-open": '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
    "message-circle": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "building": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
    "briefcase": '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
}
ICON_ALIASES = {"pin": "map-pin", "book": "book-open", "web": "globe", "wechat": "message-circle",
                "email": "mail", "address": "map-pin", "company": "building", "mobile": "smartphone"}

DEFAULT_THEME = {
    "accent": "#C8553D",
    "paper": "#FCFBF8",
    "ink": "#24231F",
    "ink2": "#4F4D48",
    "ink3": "#7B7870",
    "on_accent": "#FFFFFF",
    "font_sans": '"PingFang SC", "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
    "font_serif": '"Songti SC", "Noto Serif CJK SC", "Source Han Serif SC", STSong, serif',
    "font_mono": '"SF Mono", Menlo, Consolas, monospace',
}
DEFAULT_LABELS = {"front": "正面", "back": "背面", "stack": "正反"}
BLOCK_TYPES = {"name", "text", "contacts", "image", "qr", "rect"}
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
CHROME_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"]
DIM_RE = re.compile(r"^(?:auto|-?\d+(?:\.\d+)?(?:px|%|em)?)$")
UNSAFE_CSS = re.compile(r"[;{}<>]")
LEAK_RE = re.compile(r"[/]Users[/][^/\s\"']+[/]|[A-Za-z]:\\\\Users\\\\|file://|wxid_[A-Za-z0-9]+")


class SpecError(Exception):
    pass


# ---------------------------------------------------------------- helpers

def esc(value) -> str:
    return html.escape(str(value), quote=True)


def css_value(value, field: str) -> str:
    text = str(value)
    if UNSAFE_CSS.search(text):
        raise SpecError(f"{field}: CSS value must not contain ; {{ }} < >")
    return text


def dim(value, field: str) -> str:
    if isinstance(value, bool):
        raise SpecError(f"{field}: expected a number or length string")
    if isinstance(value, (int, float)):
        return f"{value:g}px"
    text = str(value).strip()
    if not DIM_RE.fullmatch(text):
        raise SpecError(f"{field}: unsupported length {text!r} (use px number, '50%', 'auto')")
    return text


class Ctx:
    def __init__(self, spec_dir: Path, theme: dict):
        self.spec_dir = spec_dir
        self.theme = theme
        self.cache: dict[str, str] = {}

    def color(self, value, field: str) -> str:
        key = str(value)
        if key in self.theme:
            return f"var(--{key.replace('_', '-')})"
        return css_value(key, field)

    def font(self, value, field: str) -> str:
        key = str(value)
        if key in ("sans", "serif", "mono"):
            return f"var(--font-{key})"
        return css_value(key, field)

    def asset(self, src: str, field: str) -> str:
        if src.startswith("data:"):
            return src
        path = (self.spec_dir / src).expanduser().resolve()
        if not path.is_file():
            raise SpecError(f"{field}: asset not found: {src}")
        key = str(path)
        if key not in self.cache:
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if path.suffix.lower() == ".svg":
                mime = "image/svg+xml"
            self.cache[key] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
        return self.cache[key]


def box_css(b: dict, field: str) -> list[str]:
    out = []
    center = b.get("center")
    if center in ("x", "xy") and "left" not in b and "right" not in b:
        out.append("left:50%")
    if center in ("y", "xy") and "top" not in b and "bottom" not in b:
        out.append("top:50%")
    for key in ("left", "top", "right", "bottom", "width", "height"):
        if key in b:
            out.append(f"{key}:{dim(b[key], f'{field}.{key}')}")
    transform = {"x": "translateX(-50%)", "y": "translateY(-50%)", "xy": "translate(-50%,-50%)"}.get(center)
    if center and not transform:
        raise SpecError(f"{field}.center must be x, y or xy")
    if transform:
        out.append(f"transform:{transform}")
    if "opacity" in b:
        out.append(f"opacity:{float(b['opacity']):g}")
    if "z" in b:
        out.append(f"z-index:{int(b['z'])}")
    return out


def type_css(ctx: Ctx, b: dict, field: str, prefix: str = "") -> list[str]:
    def get(key):
        return b.get(prefix + key)

    out = []
    if get("size") is not None:
        out.append(f"font-size:{dim(get('size'), field + '.' + prefix + 'size')}")
    if get("weight") is not None:
        out.append(f"font-weight:{int(get('weight'))}")
    if get("color") is not None:
        out.append(f"color:{ctx.color(get('color'), field + '.' + prefix + 'color')}")
    if get("font") is not None:
        out.append(f"font-family:{ctx.font(get('font'), field + '.' + prefix + 'font')}")
    if get("tracking") is not None:
        out.append(f"letter-spacing:{float(get('tracking')):g}em")
        if get("optical_center"):  # balance the trailing letter-spacing of centered text
            out.append(f"padding-left:{float(get('tracking')):g}em")
    if get("line_height") is not None:
        out.append(f"line-height:{css_value(get('line_height'), field + '.line_height')}")
    if get("align") is not None:
        out.append(f"text-align:{css_value(get('align'), field + '.align')}")
    if get("italic"):
        out.append("font-style:italic")
    return out


def style_attr(parts: list[str]) -> str:
    return f' style="{esc(";".join(parts))}"' if parts else ""


def rich(b: dict, field: str, key: str = "text") -> str:
    if "html" in b and key == "text":
        return str(b["html"])
    if key not in b:
        raise SpecError(f"{field}: '{key}' is required")
    return esc(b[key]).replace("\n", "<br>")


def icon_svg(ctx: Ctx, item: dict, block: dict, field: str, color: str) -> str:
    if "icon_svg" in item:
        inner = str(item["icon_svg"])
    else:
        name = ICON_ALIASES.get(item.get("icon", ""), item.get("icon", ""))
        if name not in ICONS:
            raise SpecError(f"{field}.icon: unknown icon {item.get('icon')!r}; known: {', '.join(sorted(ICONS))}")
        inner = ICONS[name]
    size = dim(block.get("icon_size", 18), field + ".icon_size")
    stroke = float(block.get("stroke", 1.9))
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="{esc(color)}" stroke-width="{stroke:g}" '
            f'stroke-linecap="round" stroke-linejoin="round" style="width:{size};height:{size}">{inner}</svg>')


# ---------------------------------------------------------------- blocks

def block_attrs(b: dict, side: str, index: int) -> str:
    bid = b.get("id") or f"{side}-{index}-{b['type']}"
    attrs = f' data-id="{esc(bid)}"'
    if b.get("decor"):
        attrs += ' data-decor="1"'
    if b.get("bleed"):
        attrs += ' data-bleed="1"'
    return attrs


def r_name(ctx, b, field, attrs):
    row = box_css(b, field) + [f"gap:{dim(b.get('gap', 20), field + '.gap')}"]
    main = type_css(ctx, {"size": 54, "weight": 600, "color": "accent", "line_height": "1", **b}, field)
    out = f'<div class="blk name-row"{attrs}{style_attr(row)}><span class="nm"{style_attr(main)}>{rich(b, field)}</span>'
    if b.get("latin"):
        lat = type_css(ctx, {"latin_size": 30, "latin_weight": 400, "latin_color": "ink3",
                             "latin_line_height": "1", **b}, field, prefix="latin_")
        out += f'<span class="lt"{style_attr(lat)}>{esc(b["latin"])}</span>'
    return out + "</div>"


def r_text(ctx, b, field, attrs):
    parts = box_css(b, field) + type_css(ctx, b, field)
    cls = "blk t wrap" if b.get("wrap") else "blk t"
    return f'<div class="{cls}"{attrs}{style_attr(parts)}>{rich(b, field)}</div>'


def r_contacts(ctx, b, field, attrs):
    style = b.get("icon_style", "tile")
    if style not in ("tile", "circle", "plain"):
        raise SpecError(f"{field}.icon_style must be tile, circle or plain")
    tile = dim(b.get("tile_size", 32), field + ".tile_size")
    radius = "50%" if style == "circle" else dim(b.get("tile_radius", 4), field + ".tile_radius")
    tile_bg = "transparent" if style == "plain" else ctx.color(b.get("tile_color", "accent"), field + ".tile_color")
    default_icon = "accent" if style == "plain" else "on_accent"
    icon_color = ctx.color(b.get("icon_color", default_icon), field + ".icon_color")
    text_css = type_css(ctx, {"size": 20, "color": "ink2", "line_height": tile, **b}, field)
    label_css = [f"color:{ctx.color(b.get('label_color', 'ink3'), field + '.label_color')}",
                 f"margin-right:{dim(b.get('label_gap', 10), field + '.label_gap')}"]
    prefix_css = [f"margin-right:{dim(b.get('prefix_gap', 14), field + '.prefix_gap')}"]
    if b.get("prefix_color"):
        prefix_css.append(f"color:{ctx.color(b['prefix_color'], field + '.prefix_color')}")
    box = box_css(b, field) + [f"gap:{dim(b.get('row_gap', 26), field + '.row_gap')}"]
    rows = []
    items = b.get("items")
    if not isinstance(items, list) or not items:
        raise SpecError(f"{field}.items must be a non-empty list")
    for i, item in enumerate(items):
        f = f"{field}.items[{i}]"
        if not isinstance(item, dict):
            raise SpecError(f"{f} must be an object")
        svg = icon_svg(ctx, item, b, f, icon_color)
        if "lines" in item:
            lines = []
            for line in item["lines"]:
                if isinstance(line, list) and len(line) == 2:
                    lines.append(f'<span class="pf"{style_attr(prefix_css)}>{esc(line[0])}</span>{esc(line[1])}')
                else:
                    lines.append(esc(line))
            body = "<br>".join(lines)
        else:
            body = esc(item.get("text", ""))
        if item.get("label"):
            body = f'<span class="k"{style_attr(label_css)}>{esc(item["label"])}</span>' + body
        rows.append(
            f'<div class="row" style="gap:{dim(b.get("icon_gap", 20), field + ".icon_gap")}">'
            f'<span class="tile" style="width:{tile};height:{tile};border-radius:{radius};background:{tile_bg}">{svg}</span>'
            f'<div class="txt"{style_attr(text_css)}>{body}</div></div>'
        )
    return f'<div class="blk contacts"{attrs}{style_attr(box)}>{"".join(rows)}</div>'


def r_image(ctx, b, field, attrs):
    if "src" not in b:
        raise SpecError(f"{field}.src is required")
    parts = box_css(b, field)
    if b.get("fit"):
        parts.append(f"object-fit:{css_value(b['fit'], field + '.fit')}")
    return f'<img class="blk img"{attrs} src="{esc(ctx.asset(b["src"], field + ".src"))}" alt="{esc(b.get("alt", ""))}"{style_attr(parts)}>'


def r_qr(ctx, b, field, attrs):
    if "src" not in b:
        raise SpecError(f"{field}.src is required")
    size = dim(b.get("size", 150), field + ".size")
    pad = dim(b.get("pad", 8), field + ".pad")
    bg = ctx.color(b.get("bg", "#FFFFFF"), field + ".bg")
    box = box_css(b, field) + [f"width:{size}"]
    img = f"display:block;width:{size};height:{size};background:{bg};padding:{pad}"
    out = f'<div class="blk qr"{attrs}{style_attr(box)}><img src="{esc(ctx.asset(b["src"], field + ".src"))}" alt="{esc(b.get("alt", "QR"))}" style="{esc(img)}">'
    if b.get("caption"):
        cap = type_css(ctx, {"caption_size": 13, "caption_color": "ink3", **b}, field, prefix="caption_")
        tracking = float(b.get("caption_tracking", 0.3))
        cap += [f"letter-spacing:{tracking:g}em", f"padding-left:{tracking:g}em",
                f"margin-top:{dim(b.get('caption_gap', 8), field + '.caption_gap')}"]
        out += f'<span class="cap"{style_attr(cap)}>{esc(b["caption"])}</span>'
    return out + "</div>"


def r_rect(ctx, b, field, attrs):
    parts = box_css(b, field) + [f"background:{ctx.color(b.get('color', 'accent'), field + '.color')}"]
    if "radius" in b:
        parts.append(f"border-radius:{dim(b['radius'], field + '.radius')}")
    return f'<div class="blk rect"{attrs}{style_attr(parts)}></div>'


RENDERERS = {"name": r_name, "text": r_text, "contacts": r_contacts, "image": r_image, "qr": r_qr, "rect": r_rect}


# ---------------------------------------------------------------- page

PAGE_JS = r"""
(function () {
  const m = location.hash.slice(1);
  const root = document.documentElement;
  if (m) { root.classList.add("shoot"); if (m === "front" || m === "back") root.classList.add("only-" + m); }
  if (!m) {
    const fit = () => { const s = Math.min(1, (window.innerWidth - 32) / CARD_W);
      document.querySelectorAll(".card").forEach(c => c.style.zoom = s); };
    fit(); window.addEventListener("resize", fit);
  }
  if (m !== "check") return;
  const run = () => {
    const issues = [];
    document.querySelectorAll(".card").forEach(card => {
      const side = card.dataset.side, cr = card.getBoundingClientRect();
      const blocks = [...card.querySelectorAll(".blk")].map(el => ({
        id: el.dataset.id, decor: !!el.dataset.decor, bleed: !!el.dataset.bleed,
        r: el.getBoundingClientRect(), el }));
      blocks.forEach(b => {
        const r = b.r;
        if (!b.bleed && (r.left < cr.left - 0.5 || r.top < cr.top - 0.5 || r.right > cr.right + 0.5 || r.bottom > cr.bottom + 0.5))
          issues.push({ side, kind: "out-of-bounds", id: b.id,
            box: [r.left - cr.left, r.top - cr.top, r.width, r.height].map(v => Math.round(v)) });
        if (b.el.classList.contains("t") && b.el.style.width && b.el.scrollWidth > b.el.clientWidth + 1)
          issues.push({ side, kind: "text-overflow", id: b.id });
      });
      const solid = blocks.filter(b => !b.decor);
      for (let i = 0; i < solid.length; i++) for (let j = i + 1; j < solid.length; j++) {
        const a = solid[i].r, c = solid[j].r;
        const w = Math.min(a.right, c.right) - Math.max(a.left, c.left);
        const h = Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top);
        if (w > 1 && h > 1) issues.push({ side, kind: "overlap", ids: [solid[i].id, solid[j].id], area: Math.round(w * h) });
      }
    });
    const out = document.createElement("pre");
    out.id = "layout-report"; out.textContent = JSON.stringify({ issues });
    document.body.appendChild(out);
  };
  window.addEventListener("load", () => (document.fonts ? document.fonts.ready : Promise.resolve()).then(run));
})();
"""


def build_html(spec: dict, spec_dir: Path) -> tuple[str, int, int, list[str]]:
    canvas = spec.get("canvas") or {}
    try:
        width, height = int(canvas["width"]), int(canvas["height"])
    except (KeyError, TypeError, ValueError):
        raise SpecError("canvas.width and canvas.height are required integers (CSS px)")
    theme = {**DEFAULT_THEME, **(spec.get("theme") or {})}
    for key, value in theme.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise SpecError(f"theme key {key!r} must be lowercase snake_case")
        css_value(value, f"theme.{key}")
    ctx = Ctx(spec_dir, theme)
    sides = [s for s in ("front", "back") if spec.get(s)]
    if not sides:
        raise SpecError("spec needs at least one of 'front' or 'back'")

    sections = []
    for side in sides:
        sd = spec[side]
        bg = ctx.color(sd.get("background", "paper"), f"{side}.background")
        blocks = sd.get("blocks") or []
        if not isinstance(blocks, list):
            raise SpecError(f"{side}.blocks must be a list")
        rendered = []
        for i, b in enumerate(blocks):
            field = f"{side}.blocks[{i}]"
            if not isinstance(b, dict) or b.get("type") not in BLOCK_TYPES:
                raise SpecError(f"{field}.type must be one of {', '.join(sorted(BLOCK_TYPES))}")
            rendered.append(RENDERERS[b["type"]](ctx, b, field, block_attrs(b, side, i)))
        sections.append(f'<section class="card {side}" data-side="{side}" style="background:{bg}">\n  '
                        + "\n  ".join(rendered) + "\n</section>")

    root_vars = "\n".join(f"  --{k.replace('_', '-')}: {v};" for k, v in theme.items())
    gap = int(spec.get("stack_gap", 0))
    title = esc(spec.get("title") or "Business card")
    extra_css = str(spec.get("extra_css", ""))
    if "</style" in extra_css.lower():
        raise SpecError("extra_css must not close the style element")
    page = f"""<!doctype html>
<html lang="{esc(spec.get('lang', 'zh-CN'))}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root {{
{root_vars}
  --stack-gap: {gap}px;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ background: #E9E7E1; }}
body {{ font-family: var(--font-sans); -webkit-font-smoothing: antialiased; display: flex; flex-direction: column;
        align-items: center; gap: 28px; padding: 40px 16px; }}
.card {{ width: {width}px; height: {height}px; position: relative; overflow: hidden; flex: none;
         box-shadow: 0 1px 2px rgba(0,0,0,.06), 0 8px 28px rgba(0,0,0,.08); }}
.blk {{ position: absolute; }}
.name-row {{ display: flex; align-items: baseline; white-space: nowrap; }}
.t {{ white-space: nowrap; }}
.t.wrap {{ white-space: normal; }}
.contacts {{ display: flex; flex-direction: column; }}
.contacts .row {{ display: flex; align-items: flex-start; }}
.tile {{ flex: none; display: flex; align-items: center; justify-content: center; }}
.qr {{ text-align: center; }}
.qr .cap {{ display: block; }}
#layout-report {{ display: none; }}
html.shoot, html.shoot body {{ background: transparent; padding: 0; gap: var(--stack-gap); }}
html.shoot .card {{ box-shadow: none; }}
html.only-front .back, html.only-back .front {{ display: none; }}
{extra_css}
</style></head>
<body>
{chr(10).join(sections)}
<script>const CARD_W = {width};{PAGE_JS}</script>
</body></html>
"""
    return page, width, height, sides


# ---------------------------------------------------------------- chrome

def find_chrome(explicit: str | None) -> str:
    for candidate in (explicit, os.environ.get("CHROME_PATH"), os.environ.get("CHROME_BIN")):
        if candidate:
            if Path(candidate).exists():
                return candidate
            raise SpecError(f"Chrome not found at {candidate}")
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    for name in CHROME_NAMES:
        found = shutil.which(name)
        if found:
            return found
    raise SpecError("No Chrome/Chromium/Edge found; pass --chrome or set CHROME_PATH")


def chrome(binary: str, profile: str, args: list[str]) -> subprocess.CompletedProcess:
    base = [binary, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", f"--user-data-dir={profile}", "--virtual-time-budget=4000"]
    return subprocess.run(base + args, capture_output=True, text=True, timeout=180)


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SpecError(f"{path.name} is not a PNG")
    return struct.unpack(">II", head[16:24])


def layout_check(binary: str, profile: str, url: str, width: int, height: int) -> list[dict]:
    proc = chrome(binary, profile, [f"--window-size={width + 40},{height * 2 + 40}", "--dump-dom", url + "#check"])
    match = re.search(r'<pre id="layout-report">(.*?)</pre>', proc.stdout, re.S)
    if not match:
        raise SpecError("layout check produced no report; Chrome stderr: " + proc.stderr.strip()[-400:])
    return json.loads(html.unescape(match.group(1)))["issues"]


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Render a distilled business card from a JSON layout spec.")
    ap.add_argument("spec", help="card spec JSON; asset paths resolve relative to it")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--version", required=True, help="output version label, e.g. v0.1")
    ap.add_argument("--stem", help="file stem; defaults to spec.output.stem or 'card'")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--sides", default="front,back,stack", help="comma list of front, back, stack")
    ap.add_argument("--scale", type=float, default=None, help="device scale factor (default spec.canvas.scale or 3)")
    ap.add_argument("--chrome")
    ap.add_argument("--html-only", action="store_true", help="write HTML and skip Chrome")
    ap.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = ap.parse_args()

    try:
        spec_path = Path(args.spec).expanduser().resolve()
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        page, width, height, sides = build_html(spec, spec_path.parent)
        scrubbed = re.sub(r'data:[^"\')\s]+', "", page)
        leak = LEAK_RE.search(scrubbed)
        if leak:
            raise SpecError(f"output would contain a private path or account id near {leak.group(0)[:12]!r}")

        output = spec.get("output") or {}
        stem = args.stem or output.get("stem") or "card"
        labels = {**DEFAULT_LABELS, **(output.get("labels") or {})}
        if not re.fullmatch(r"v?\d+(?:\.\d+){0,2}", args.version):
            raise SpecError("--version must look like v0.1 or 0.1.0")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
            raise SpecError("--date must be YYYY-MM-DD")
        wanted = [s.strip() for s in args.sides.split(",") if s.strip()]
        for s in wanted:
            if s not in ("front", "back", "stack"):
                raise SpecError(f"--sides: unknown side {s!r}")
        wanted = [s for s in wanted if s in sides or (s == "stack" and len(sides) == 2)]
        scale = args.scale or float((spec.get("canvas") or {}).get("scale", 3))

        out_dir = Path(args.out_dir).expanduser().resolve()
        html_path = out_dir / f"{stem}-{args.date}-{args.version}.html"
        pngs = {s: out_dir / f"{stem}-{labels[s]}-{args.date}-{args.version}.png" for s in wanted}
        targets = [html_path] + ([] if args.html_only else list(pngs.values()))
        existing = [p.name for p in targets if p.exists()]
        if existing and not args.force:
            print(json.dumps({"status": "refused", "reason": "outputs exist; pass --force", "files": existing},
                             ensure_ascii=False))
            return 2
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path.write_text(page, encoding="utf-8")
        result = {"status": "html-only" if args.html_only else "rendered", "html": str(html_path),
                  "html_bytes": html_path.stat().st_size, "canvas": [width, height], "scale": scale,
                  "sides": sides, "pngs": {}, "issues": []}
        if args.html_only:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        binary = find_chrome(args.chrome)
        url = html_path.as_uri()
        with tempfile.TemporaryDirectory(prefix="jessy-card-chrome-") as profile:
            result["issues"] = layout_check(binary, profile, url, width, height)
            gap = int(spec.get("stack_gap", 0))
            for side, png in pngs.items():
                h = height * 2 + gap if side == "stack" else height
                proc = chrome(binary, profile, [f"--force-device-scale-factor={scale:g}", f"--window-size={width},{h}",
                                                f"--screenshot={png}", f"{url}#{side}"])
                if not png.is_file():
                    raise SpecError(f"Chrome did not write {png.name}: {proc.stderr.strip()[-400:]}")
                w_px, h_px = png_size(png)
                result["pngs"][side] = {"path": str(png), "pixels": [w_px, h_px], "bytes": png.stat().st_size}
        if result["issues"]:
            result["status"] = "rendered-with-issues"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 3 if result["issues"] else 0
    except SpecError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1
    except (OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
