#!/usr/bin/env python3
"""Check a built card: figure text overlaps, overflow, clipping, and out-of-canvas elements.

Run it on the card HTML after the figures are injected and before delivery; the
mobile-infographic audit cannot see collisions between two SVG labels.

An inline SVG clips anything outside its own viewBox, so a label that runs past
the right edge is cut in the PNG while every element still sits inside the card.
That is checked per figure as `clipped_in_svg`.
"""

import argparse
import itertools
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--card", required=True, help="card.html with the figures injected")
    ap.add_argument("--out", default="", help="optional JSON report")
    ap.add_argument("--min-overlap", type=float, default=1.0)
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("needs playwright: python3 -m pip install playwright") from exc

    js = """
    () => {
      const card = document.querySelector('[data-card]');
      const box = card.getBoundingClientRect();
      const labels = [...card.querySelectorAll('.matrix text, svg text')].map((t) => {
        const r = t.getBoundingClientRect();
        return { text: t.textContent, x: r.x - box.x, y: r.y - box.y, w: r.width, h: r.height };
      });
      const overflow = [];
      card.querySelectorAll('*').forEach((el) => {
        if (el.scrollWidth - el.clientWidth > 2 || el.scrollHeight - el.clientHeight > 2) {
          overflow.push(el.tagName.toLowerCase() + '.' + (el.getAttribute('class') || ''));
        }
      });
      const outside = labels.filter((l) => l.x < -2 || l.y < -2 ||
        l.x + l.w > box.width + 2 || l.y + l.h > box.height + 2).map((l) => l.text);
      const clipped = [];
      card.querySelectorAll('svg').forEach((svg) => {
        const s = svg.getBoundingClientRect();
        svg.querySelectorAll('text').forEach((t) => {
          const r = t.getBoundingClientRect();
          const past = r.x < s.x - 1 || r.y < s.y - 1 ||
            r.x + r.width > s.x + s.width + 1 || r.y + r.height > s.y + s.height + 1;
          if (past) {
            clipped.push({
              figure: svg.getAttribute('aria-label') || '(unnamed)',
              text: t.textContent,
            });
          }
        });
      });
      return { canvas: { w: box.width, h: box.height }, labels, overflow, outside, clipped };
    }
    """

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1200})
        page.goto(Path(args.card).resolve().as_uri())
        page.wait_for_timeout(300)
        data = page.evaluate(js)
        browser.close()

    clashes = []
    for a, b in itertools.combinations(data["labels"], 2):
        ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
        oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
        if ox > args.min_overlap and oy > args.min_overlap:
            clashes.append({"a": a["text"][:20], "b": b["text"][:20],
                            "overlap_px": [round(ox), round(oy)]})

    report = {
        "canvas": data["canvas"],
        "labels": len(data["labels"]),
        "overlaps": clashes,
        "overflow": data["overflow"],
        "outside_canvas": data["outside"],
        "clipped_in_svg": data["clipped"],
    }
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "labels"},
                     ensure_ascii=False, indent=1))
    if clashes or data["overflow"] or data["outside"] or data["clipped"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
