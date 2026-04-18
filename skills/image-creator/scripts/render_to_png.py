#!/usr/bin/env python3
"""Render an HTML file to PNG using Playwright.

Usage:
    python3 render_to_png.py input.html -o output.png [-w 1200] [-h 630] [--scale 2] [--wait 2000]
"""
import argparse
import sys
from playwright.sync_api import sync_playwright


def render(html_path: str, output: str, width: int, height: int, scale: float, wait_ms: int):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page.goto(f"file://{html_path}", wait_until="networkidle")
        if wait_ms > 0:
            page.wait_for_timeout(wait_ms)
        page.screenshot(path=output, full_page=False)
        browser.close()
    print(f"Saved: {output} ({width}x{height} @{scale}x)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTML → PNG renderer")
    parser.add_argument("input", help="Path to HTML file")
    parser.add_argument("-o", "--output", default="output.png", help="Output PNG path")
    parser.add_argument("-W", "--width", type=int, default=1200, help="Viewport width (default: 1200)")
    parser.add_argument("-H", "--height", type=int, default=630, help="Viewport height (default: 630)")
    parser.add_argument("--scale", type=float, default=2, help="Device scale factor (default: 2)")
    parser.add_argument("--wait", type=int, default=1000, help="Extra wait in ms after networkidle (default: 1000)")
    args = parser.parse_args()

    import os
    abs_input = os.path.abspath(args.input)
    if not os.path.exists(abs_input):
        print(f"Error: {abs_input} not found")
        sys.exit(1)

    render(abs_input, args.output, args.width, args.height, args.scale, args.wait)
