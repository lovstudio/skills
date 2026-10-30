#!/usr/bin/env python3
"""Capture on-screen evidence (web pages, docs, local HTML) as PNG b-roll with Playwright.

usage:
  capture.py url URL --out broll/x.png [--width 1080] [--height 1350] [--scale 2] [--selector CSS]
                 [--full-page] [--wait-ms 1500] [--color-scheme light|dark] [--hide CSS ...]
  capture.py script work/script.json [--root EPISODE_DIR] [--force]
  capture.py term OUTPUT.txt --out broll/x.png [--title "check_script.py"] [--highlight ERROR WARN]

`script` mode captures every b-roll whose `capture.url` is set and whose `src` is missing (or all with --force),
using the same options from the b-roll's `capture` object (width, height, selector, full_page, wait_ms,
color_scheme, hide). Default viewport 1080×1350 at 2× matches the split layout's top panel after a
gentle push-in. Uses bundled Chromium when installed, otherwise the system Chrome channel.
`term` renders the REAL text output of a command (saved to a file) as a terminal window, with lines that
contain a --highlight word tinted, for evidence such as a gate report; never type output by hand.
Only capture public pages or the author's own screens; never pages behind someone else's login.
"""
import html
import tempfile

TERM = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#000;display:flex;justify-content:center;align-items:flex-start;padding:60px 40px;box-sizing:border-box}
.win{width:100%%;border-radius:22px;background:#1b1b1d;box-shadow:0 30px 80px rgba(0,0,0,.6);overflow:hidden;border:1px solid #333}
.bar{height:58px;background:#2a2a2d;display:flex;align-items:center;gap:14px;padding:0 24px;color:#aaa;font:600 24px -apple-system,sans-serif}
.dot{width:18px;height:18px;border-radius:50%%}
pre{margin:0;padding:28px 30px;color:#e8e8e8;font:500 27px/1.55 "SF Mono",Menlo,"PingFang SC",monospace;white-space:pre-wrap;overflow-wrap:break-word}
.hi{color:#ff6b5e;font-weight:700}.wa{color:#ffc21a}
</style></head><body><div class="win"><div class="bar"><span class="dot" style="background:#ff5f57"></span>
<span class="dot" style="background:#febc2e"></span><span class="dot" style="background:#28c840"></span>
<span style="margin-left:14px">%s</span></div><pre>%s</pre></div></body></html>"""


def term_html(text, title, highlights):
    rows = []
    for line in text.splitlines():
        cls = "hi" if highlights and any(h in line for h in highlights[:1]) else \
              "wa" if any(h in line for h in highlights[1:]) else ""
        esc = html.escape(line)
        rows.append(f'<span class="{cls}">{esc}</span>' if cls else esc)
    return TERM % (html.escape(title), "\n".join(rows))

import argparse
import json
import sys
from pathlib import Path


def shoot(pw, url, out, width=1080, height=1350, scale=2, selector=None, full_page=False, wait_ms=1500,
          color_scheme="light", hide=None, press=None):
    try:
        browser = pw.chromium.launch()
    except Exception:
        browser = pw.chromium.launch(channel="chrome")
    try:
        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale,
                                  color_scheme=color_scheme, locale="zh-CN")
        page = ctx.new_page()
        if "://" not in url:
            url = Path(url).resolve().as_uri()
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(wait_ms)
        for key in press or []:  # e.g. start a teleprompter or open a menu before the shot
            page.keyboard.press(key)
            page.wait_for_timeout(500)
        for css in hide or []:
            page.add_style_tag(content=f"{css}{{visibility:hidden !important}}")
        out.parent.mkdir(parents=True, exist_ok=True)
        if selector:
            page.locator(selector).first.screenshot(path=str(out))
        else:
            page.screenshot(path=str(out), full_page=full_page)
    finally:
        browser.close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    u = sub.add_parser("url")
    u.add_argument("url")
    u.add_argument("--out", required=True)
    u.add_argument("--width", type=int, default=1080)
    u.add_argument("--height", type=int, default=1350)
    u.add_argument("--scale", type=float, default=2)
    u.add_argument("--selector")
    u.add_argument("--full-page", action="store_true")
    u.add_argument("--wait-ms", type=int, default=1500)
    u.add_argument("--color-scheme", default="light", choices=["light", "dark"])
    u.add_argument("--hide", nargs="*", help="CSS selectors to hide (cookie banners, chat bubbles)")
    u.add_argument("--press", nargs="*", help="keys to press before the shot (Playwright names, e.g. Space ArrowRight)")
    tm = sub.add_parser("term")
    tm.add_argument("text")
    tm.add_argument("--out", required=True)
    tm.add_argument("--title", default="Terminal")
    tm.add_argument("--highlight", nargs="*", default=["ERROR", "WARN"], help="first word red, the rest yellow")
    tm.add_argument("--width", type=int, default=1080)
    tm.add_argument("--height", type=int, default=1350)
    s = sub.add_parser("script")
    s.add_argument("script")
    s.add_argument("--root")
    s.add_argument("--force", action="store_true")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        if a.mode == "term":
            with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
                f.write(term_html(Path(a.text).read_text(), a.title, a.highlight))
            out = shoot(pw, f.name, Path(a.out), a.width, a.height, 2, ".win", False, 300)
            Path(f.name).unlink()
            print(json.dumps({"captured": str(out)}, ensure_ascii=False))
            return
        if a.mode == "url":
            out = shoot(pw, a.url, Path(a.out), a.width, a.height, a.scale, a.selector, a.full_page, a.wait_ms,
                        a.color_scheme, a.hide, a.press)
            print(json.dumps({"captured": str(out)}, ensure_ascii=False))
            return
        sp = Path(a.script)
        root = Path(a.root) if a.root else sp.resolve().parent.parent
        done, failed = [], []
        for ln in json.loads(sp.read_text())["lines"]:
            for b in ln.get("broll") or []:
                cap = b.get("capture") or {}
                if not cap.get("url"):
                    continue
                dst = root / b["src"]
                if dst.exists() and not a.force:
                    continue
                try:
                    shoot(pw, cap["url"], dst, cap.get("width", 1080), cap.get("height", 1350), cap.get("scale", 2),
                          cap.get("selector"), cap.get("full_page", False), cap.get("wait_ms", 1500),
                          cap.get("color_scheme", "light"), cap.get("hide"), cap.get("press"))
                    done.append(b["src"])
                except Exception as e:  # keep going; report every failure at the end
                    failed.append({"src": b["src"], "url": cap["url"], "error": str(e)[:200]})
        print(json.dumps({"captured": done, "failed": failed}, ensure_ascii=False, indent=1))
        if failed:
            sys.exit(1)


if __name__ == "__main__":
    main()
