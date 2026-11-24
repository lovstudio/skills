#!/usr/bin/env python3
"""Lay out a lookalike meme (1080x1440) with HTML and render it with headless Chrome.

Background: bright color + white halftone dots + radial burst.
Cards: white-bordered tilted stickers with hard black shadow.
Title: one big SmileySans headline, yellow fill, thick black stroke, hard drop shadow.
All Chinese text is typeset here, never by an image model.
"""
import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 1080, 1440

PALETTES = {
    "pink": ("#ff5c8a", "#ffe14d"),
    "yellow": ("#ffc23d", "#ffffff"),
    "blue": ("#3d9df5", "#ffe14d"),
    "mint": ("#25c492", "#ffe14d"),
    "purple": ("#8f5cff", "#ffe14d"),
    "orange": ("#ff7a2f", "#ffe14d"),
}

# left, top, width, height, rotate(deg); approved 3-up layout first.
LAYOUTS = {
    1: [(190, 380, 700, 900, -3)],
    2: [(50, 370, 500, 560, -6), (500, 760, 500, 560, 5)],
    3: [(40, 360, 470, 470, -7), (522, 330, 500, 500, 6), (250, 870, 560, 500, -2)],
}

FONT_NAMES = ("SmileySans-Oblique.ttf", "SmileySans-Oblique.otf", "SmileySans-Oblique.ttf.woff2")
FONT_DIRS = ("~/Library/Fonts", "/Library/Fonts", "~/.local/share/fonts", "~/.fonts",
             "/usr/share/fonts", "/usr/local/share/fonts", "C:/Windows/Fonts")
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge",
)


def find_font(explicit):
    if explicit:
        p = Path(explicit).expanduser()
        if p.is_file():
            return p
        sys.exit(f"font not found: {explicit}")
    env = os.environ.get("LOOKALIKE_MEME_FONT")
    if env and Path(env).expanduser().is_file():
        return Path(env).expanduser()
    for d in FONT_DIRS:
        root = Path(d).expanduser()
        if not root.is_dir():
            continue
        for name in FONT_NAMES:
            hits = list(root.rglob(name))
            if hits:
                return hits[0]
    sys.exit("SmileySans (得意黑) not found. Install it from https://github.com/atelier-anchor/smiley-sans "
             "or pass --font / set LOOKALIKE_MEME_FONT.")


def find_chrome(explicit):
    for cand in ([explicit] if explicit else []) + [os.environ.get("CHROME_BIN", "")] + list(CHROME_CANDIDATES):
        if not cand:
            continue
        if Path(cand).is_file():
            return cand
        found = shutil.which(cand)
        if found:
            return found
    sys.exit("Chrome/Chromium not found; pass --chrome or set CHROME_BIN")


def parse_sticker(spec):
    """PATH or PATH#contain (contain keeps the whole image on a white card)."""
    fit = "cover"
    if spec.endswith("#contain"):
        spec, fit = spec[: -len("#contain")], "contain"
    p = Path(spec).expanduser()
    if not p.is_file():
        sys.exit(f"sticker not found: {spec}")
    return p, fit


def title_css(lines):
    longest = max(len(line) for line in lines)
    size = min(190, int(980 / max(longest, 1)))
    if len(lines) > 1:
        size = min(size, 130)
    return size


def build_html(title, stickers, palette, font_url, shift):
    bg, title_color = PALETTES[palette]
    lines = [s for s in title.split("|") if s] or [title]
    size = title_css(lines)
    cards = []
    for i, ((src, fit), (left, top, w, h, rot)) in enumerate(zip(stickers, LAYOUTS[len(stickers)])):
        img_style = "object-fit:contain;background:#fff;padding:6%;box-sizing:border-box" if fit == "contain" else "object-fit:cover"
        cards.append(
            f'<div class="st" style="left:{left}px;top:{top + shift}px;width:{w}px;height:{h}px;'
            f'transform:rotate({rot}deg)"><img src="{html.escape(src)}" style="{img_style}"></div>')
    title_html = "<br>".join(html.escape(line) for line in lines)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Smiley;src:url("{font_url}")}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:{bg};background-image:radial-gradient(rgba(255,255,255,.28) 3px,transparent 3.5px);background-size:26px 26px;position:relative}}
.burst{{position:absolute;left:-200px;top:-200px;width:1480px;height:1840px;
 background:repeating-conic-gradient(from 0deg at 50% 55%,rgba(255,255,255,.14) 0 6deg,transparent 6deg 14deg)}}
.t{{position:absolute;left:0;right:0;top:60px;text-align:center;font-family:Smiley;font-size:{size}px;line-height:1.02;color:{title_color};
 -webkit-text-stroke:14px #1a1a1a;paint-order:stroke fill;transform:rotate(-4deg);
 filter:drop-shadow(10px 12px 0 #1a1a1a)}}
.st{{position:absolute;background:#fff;padding:14px;border-radius:36px;box-shadow:12px 14px 0 #1a1a1a;box-sizing:content-box}}
.st img{{display:block;width:100%;height:100%;border-radius:24px}}
</style></head><body>
<div class="burst"></div>
{chr(10).join(cards)}
<div class="t">{title_html}</div>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--title", required=True, help="Headline; use | for a line break (keep it 3-8 chars)")
    ap.add_argument("--sticker", action="append", required=True,
                    help="Image path, 1-3 times, in reading order; append #contain to keep the whole image")
    ap.add_argument("--palette", choices=sorted(PALETTES), default="pink")
    ap.add_argument("--out", type=Path, required=True, help="Output PNG")
    ap.add_argument("--font", help="SmileySans font file")
    ap.add_argument("--chrome", help="Chrome/Chromium binary")
    ap.add_argument("--keep-html", action="store_true", help="Keep the editable HTML next to the PNG")
    args = ap.parse_args()

    if not 1 <= len(args.sticker) <= 3:
        ap.error("--sticker must be given 1-3 times")
    stickers = [parse_sticker(s) for s in args.sticker]
    font = find_font(args.font)
    chrome = find_chrome(args.chrome)
    lines = [s for s in args.title.split("|") if s]
    shift = 60 if len(lines) > 1 else 0

    out = args.out.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="lookalike-meme-"))
    try:
        rel = []
        for i, (src, fit) in enumerate(stickers):
            name = f"s{i + 1}{src.suffix.lower()}"
            shutil.copy2(src, work / name)
            rel.append((name, fit))
        page = work / "meme.html"
        page.write_text(build_html(args.title, rel, args.palette, font.resolve().as_uri(), shift), encoding="utf-8")
        shot = work / "shot.png"
        cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
               "--allow-file-access-from-files", "--virtual-time-budget=4000", f"--window-size={W},{H}",
               f"--screenshot={shot}", page.as_uri()]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not shot.is_file():
            sys.exit("chrome did not produce a screenshot:\n" + proc.stderr[-1500:])
        from PIL import Image
        img = Image.open(shot).convert("RGB")
        if img.size != (W, H):
            img = img.crop((0, 0, W, H)) if img.width >= W and img.height >= H else img.resize((W, H))
        img.save(out)
        if args.keep_html:
            bundle = out.with_suffix("")
            bundle = bundle.parent / (bundle.name + "_html")
            if bundle.exists():
                shutil.rmtree(bundle)
            shutil.copytree(work, bundle, ignore=shutil.ignore_patterns("shot.png"))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(json.dumps({"out": str(out), "size": [W, H], "font": font.name, "palette": args.palette}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
