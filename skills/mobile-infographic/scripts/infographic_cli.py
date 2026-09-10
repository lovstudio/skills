#!/usr/bin/env python3
"""Mobile Infographic CLI: scaffold, render, audit, and brand initialization.

Deterministic work only: template assembly, exact-pixel rendering through
Playwright, and mobile-readability measurement. Copy and evidence judgement stay
with the agent.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_ROOT / "assets"
TEMPLATE_DIR = ASSETS_DIR / "templates"
PACKAGED_BRAND = ASSETS_DIR / "brand-profile.json"

TEMPLATES = (
    "single-claim",
    "step-strip",
    "metric-focus",
    "compare-pair",
    "checklist-gate",
    "quote-evidence",
    "bar-ranking",
)

# Skeleton bars used when `scaffold --row` is not supplied for bar-ranking.
# One row = two lines: (1) item + its one-line description, (2) bar + value + roster.
DEFAULT_BAR_ROWS = """        <div class="bar-row" data-source-ref="{{SOURCE_ID}}" data-encoding="长度 = 数值">
          <p class="bar-head">
            <span class="bar-label" data-role="label" data-skeleton="1">01 条目</span>
            <span class="bar-desc" data-role="note" data-source-ref="{{SOURCE_ID}}" data-skeleton="1">这一行是什么：一句设定或背景。</span>
          </p>
          <div class="bar-metric">
            <span class="bar-track"><span class="bar-fill" style="width:100%"></span></span>
            <span class="bar-value" data-role="label" data-skeleton="1">（0 人）</span>
          </div>
          <p class="bar-note" data-role="note" data-source-ref="{{SOURCE_ID}}" data-skeleton="1">人数对应的名单或依据。</p>
        </div>
        <div class="bar-row" data-source-ref="{{SOURCE_ID}}" data-encoding="长度 = 数值">
          <p class="bar-head">
            <span class="bar-label" data-role="label" data-skeleton="1">02 条目</span>
            <span class="bar-desc" data-role="note" data-source-ref="{{SOURCE_ID}}" data-skeleton="1">这一行是什么：一句设定或背景。</span>
          </p>
          <div class="bar-metric">
            <span class="bar-track"><span class="bar-fill" style="width:60%"></span></span>
            <span class="bar-value" data-role="label" data-skeleton="1">（0 人）</span>
          </div>
          <p class="bar-note" data-role="note" data-source-ref="{{SOURCE_ID}}" data-skeleton="1">人数对应的名单或依据。</p>
        </div>"""

# Canvas sizes at 1080 logical width. `long` grows with the content.
RATIOS: dict[str, tuple[int, int]] = {
    "3:4": (1080, 1440),
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
    "9:16": (1080, 1920),
    "long": (1080, 0),
}

# `long` grows with the content; three 3:4 screens is the documented ceiling.
LONG_MAX_HEIGHT = 1440 * 3

SAFE_AREA = {"x": 88, "top": 96, "bottom": 96, "gap": 40}

# Minimum computed font size in CSS pixels at the 1080 canvas width.
FONT_FLOOR = {
    "title": 72.0,
    "value": 96.0,
    "claim": 50.0,
    "body": 36.0,
    "label": 30.0,
    "note": 26.0,
    "source": 26.0,
}
DEFAULT_FONT_FLOOR = 26.0

# Maximum characters per rendered line, counted in CJK-equivalent units.
LINE_LIMIT = {
    "title": 14.0,
    "claim": 20.0,
    "body": 24.0,
    "label": 20.0,
    "note": 28.0,
    "source": 34.0,
}
DEFAULT_LINE_LIMIT = 26.0

CONTRAST_MIN_BODY = 4.5
CONTRAST_MIN_LARGE = 3.0
LARGE_TEXT_PX = 40.0

SCORE_THRESHOLD = 85
SCORE_DEDUCTION = {"critical": 12, "error": 6, "warning": 2}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_ratio(value: str) -> tuple[int, int]:
    left, _, right = value.partition(":")
    return int(left), int(right)


# --------------------------------------------------------------------------
# brand resolution
# --------------------------------------------------------------------------


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_brand(explicit: str | None) -> tuple[dict[str, Any], str]:
    """Resolve the brand profile. Returns the profile and its origin label."""
    candidates: list[tuple[str, Path]] = []
    if explicit:
        candidates.append(("flag", Path(explicit).expanduser()))
    env_path = os.environ.get("SKILL_MOBILE_INFOGRAPHIC_BRAND_PROFILE")
    if env_path:
        candidates.append(("env", Path(env_path).expanduser()))

    profile: dict[str, Any] = {}
    origin = "packaged"
    if PACKAGED_BRAND.is_file():
        profile = load_json(PACKAGED_BRAND)
    else:
        profile = {
            "schema_version": 1,
            "name": "Mobile Infographic",
            "site": "https://lovstudio.ai/skills/mobile-infographic",
            "logo": "",
            "primary": "#182033",
            "accent": "#EB6637",
            "ink": "#172033",
            "muted": "#4A5468",
            "paper": "#F7F4EF",
            "font_family": "PingFang SC, Hiragino Sans GB, Microsoft YaHei, Inter, sans-serif",
            "attribution": "Powered by",
        }

    for label, path in candidates:
        if path.is_file():
            profile.update(load_json(path))
            origin = f"{label}:{path}"
            break
    else:
        shared = os.environ.get("SKILL_PROFILE_PATH")
        if shared and Path(shared).expanduser().is_file():
            shared_data = load_json(Path(shared).expanduser())
            brand_scope = shared_data.get("brand") or {}
            mapped = {
                "name": brand_scope.get("name"),
                "site": brand_scope.get("site"),
                "logo": brand_scope.get("logo"),
                "font_family": brand_scope.get("font_family"),
            }
            applied = {k: v for k, v in mapped.items() if v}
            if applied:
                profile.update(applied)
                origin = f"shared-profile:{shared}"
    return profile, origin


def logo_data_url(profile: dict[str, Any]) -> str:
    raw = str(profile.get("logo") or "").strip()
    if not raw:
        return ""
    if raw.startswith("data:"):
        return raw
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = ASSETS_DIR / path
    if not path.is_file():
        raise SystemExit(f"logo not found: {path}")
    suffix = path.suffix.lower()
    mime = {".png": "image/png", ".svg": "image/svg+xml", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(suffix, "image/png")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


# --------------------------------------------------------------------------
# scaffold
# --------------------------------------------------------------------------


def page_mark(index: int, size: int) -> str:
    return f"{index}/{size}" if size > 1 else "1/1"


def credit_line(brand: dict[str, Any]) -> str:
    """Footer credit. `credit` is free text; the site is appended as *plain text* when
    `credit_link` is on.

    The deliverable is a PNG: a hyperlink is invisible once rasterised, so any URL has to
    be readable as text. Cards about private material can omit the credit entirely.
    """
    credit = str(brand.get("credit", "") or "").strip()
    site = str(brand.get("site", "") or "").strip()
    show_site = bool(brand.get("credit_link"))
    label = re.sub(r"^https?://", "", site).rstrip("/")
    if credit and show_site and label:
        return f"{credit} · {label}"
    if credit:
        return credit
    if show_site and label:
        return label
    return ""


def build_bar_rows(specs: list[str], source_id: str) -> list[str] | None:
    """Turn `--row "label|value|description|members|group"` specs into bar-ranking markup.

    Each row is two lines by design: the first line names the item and says what it is,
    the second line carries the bar, the count and the roster. The bar length is the
    row's share of the largest value, so the ranking is read before any number.
    """
    parsed: list[dict[str, Any]] = []
    for spec in specs:
        parts = [part.strip() for part in spec.split("|")]
        label = parts[0] if parts else ""
        try:
            value = float(parts[1]) if len(parts) > 1 and parts[1] else 0.0
        except ValueError:
            raise SystemExit(f"--row value must be numeric: {spec!r}")
        description = parts[2] if len(parts) > 2 else ""
        members = parts[3] if len(parts) > 3 else ""
        group = parts[4] if len(parts) > 4 and parts[4] else "voice"
        parsed.append({
            "label": label,
            "value": value,
            "description": description,
            "members": members,
            "group": group,
        })
    if not parsed:
        return None
    largest = max(row["value"] for row in parsed) or 1.0
    rows = []
    for row in parsed:
        width = max(2.0, round(row["value"] / largest * 100, 1))
        rows.append(
            "\n".join([
                f'        <div class="bar-row" data-group="{row["group"]}" data-source-ref="{source_id}" data-encoding="长度 = 数值">',
                '          <p class="bar-head">',
                f'            <span class="bar-label" data-role="label">{row["label"]}</span>',
                f'            <span class="bar-desc" data-role="note" data-source-ref="{source_id}">{row["description"]}</span>',
                '          </p>',
                '          <div class="bar-metric">',
                f'            <span class="bar-track"><span class="bar-fill" style="width:{width}%"></span></span>',
                f'            <span class="bar-value" data-role="label">（{row["value"]:g} 人）</span>',
                '          </div>',
                f'          <p class="bar-note" data-role="note" data-source-ref="{source_id}">{row["members"]}</p>',
                "        </div>",
            ])
        )
    return rows


def build_card_html(
    *,
    template: str,
    ratio: str,
    title: str,
    claim: str,
    eyebrow: str,
    source: str,
    source_id: str,
    brand: dict[str, Any],
    series_index: int,
    series_size: int,
    rows: list[str] | None = None,
) -> str:
    template_path = TEMPLATE_DIR / f"{template}.html"
    if not template_path.is_file():
        raise SystemExit(f"unknown template '{template}'; expected one of {', '.join(TEMPLATES)}")
    base_css = (ASSETS_DIR / "card-base.css").read_text(encoding="utf-8")
    markup = template_path.read_text(encoding="utf-8")
    width, height = RATIOS[ratio]
    replacements = {
        "{{BASE_CSS}}": base_css.rstrip(),
        "{{TEMPLATE_ID}}": template,
        "{{RATIO}}": ratio,
        "{{CANVAS_WIDTH}}": str(width),
        "{{CANVAS_HEIGHT}}": str(height if ratio != "long" else 0),
        "{{SAFE_X}}": str(SAFE_AREA["x"]),
        "{{SAFE_TOP}}": str(SAFE_AREA["top"]),
        "{{SAFE_BOTTOM}}": str(SAFE_AREA["bottom"]),
        "{{BLOCK_GAP}}": str(SAFE_AREA["gap"]),
        "{{BRAND_PRIMARY}}": str(brand.get("primary", "#182033")),
        "{{BRAND_ACCENT}}": str(brand.get("accent", "#EB6637")),
        "{{BRAND_ACCENT_INK}}": str(
            brand.get("accent_ink") or brand.get("accent", "#B0491A")
        ),
        "{{BRAND_INK}}": str(brand.get("ink", "#172033")),
        "{{BRAND_MUTED}}": str(brand.get("muted", "#4A5468")),
        "{{BRAND_PAPER}}": str(brand.get("paper", "#F7F4EF")),
        "{{FONT_FAMILY}}": str(
            brand.get(
                "font_family",
                "PingFang SC, Hiragino Sans GB, Microsoft YaHei, Inter, sans-serif",
            )
        ),
        "{{BRAND_NAME}}": str(brand.get("name", "")),
        "{{BRAND_LOGO}}": logo_data_url(brand),
        "{{BRAND_SITE}}": str(brand.get("site", "")),
        "{{BRAND_SITE_LABEL}}": re.sub(r"^https?://", "", str(brand.get("site", ""))).rstrip("/"),
        "{{ATTRIBUTION}}": str(brand.get("attribution", "Powered by")),
        "{{TITLE}}": title,
        "{{EYEBROW}}": eyebrow,
        "{{CLAIM}}": claim,
        "{{SOURCE}}": source,
        "{{SOURCE_ID}}": source_id,
        "{{ROWS}}": "\n".join(rows) if rows else DEFAULT_BAR_ROWS,
        "{{CREDIT_LINE}}": credit_line(brand),
        "{{SERIES_INDEX}}": str(series_index),
        "{{SERIES_SIZE}}": str(series_size),
        "{{PAGE_MARK}}": page_mark(series_index, series_size),
    }
    for token, value in replacements.items():
        markup = markup.replace(token, value)
    # Rows are injected as markup and may carry their own tokens.
    markup = markup.replace("{{SOURCE_ID}}", source_id).replace("{{SOURCE}}", source)
    return markup


BRIEF_TEMPLATE = """# 手机信息图 Brief

- 模板：{template}
- 比例：{ratio}（{width}×{height_css}）
- 系列：第 {series_index} / {series_size} 张
- 生成时间：{generated_at}

## 唯一结论

{claim}

## 证据表

| ID | 论点 / 判据 | 精确证据 | 编码方式 | 直接标注 |
| --- | --- | --- | --- | --- |
| S1 | {claim} | 待补充来源、口径与数字 | 位置 / 长度 / 颜色 | 待补充 |

## 口径与限定

- 单位、周期、样本与分母：
- 事实 / 估计 / 假设 / 解读：
- 已知缺口：
"""


def cmd_scaffold(args: argparse.Namespace) -> int:
    brand, brand_origin = resolve_brand(args.brand_profile)
    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / args.filename
    if target.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite existing card: {target}")

    html = build_card_html(
        template=args.template,
        ratio=args.ratio,
        title=args.title,
        claim=args.claim or args.title,
        eyebrow=args.eyebrow,
        source=args.source,
        source_id=args.source_id,
        brand=brand,
        series_index=args.series_index,
        series_size=args.series_size,
        rows=build_bar_rows(args.row or [], args.source_id),
    )
    target.write_text(html, encoding="utf-8")

    brief_path = out_dir / (target.stem + ".brief.md")
    width, height = RATIOS[args.ratio]
    brief_path.write_text(
        BRIEF_TEMPLATE.format(
            template=args.template,
            ratio=args.ratio,
            width=width,
            height_css="自动高度" if args.ratio == "long" else height,
            series_index=args.series_index,
            series_size=args.series_size,
            generated_at=now_iso(),
            claim=args.claim or args.title,
        ),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "scaffolded",
        "card": str(target),
        "brief": str(brief_path),
        "template": args.template,
        "ratio": args.ratio,
        "series": f"{args.series_index}/{args.series_size}",
        "brand_origin": brand_origin,
        "next": "替换 data-skeleton 文案，补证据与来源，然后 render 与 audit",
    }, ensure_ascii=False, indent=1))
    return 0


# --------------------------------------------------------------------------
# browser plumbing
# --------------------------------------------------------------------------


def require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(
            "Playwright is required: python3 -m pip install 'playwright>=1.45,<2' "
            "&& python3 -m playwright install chromium"
        ) from exc
    return sync_playwright


MEASURE_JS = r"""
() => {
  const CJK = /[\u1100-\u11FF\u2E80-\uA4CF\uA960-\uA97F\uAC00-\uD7FF\uF900-\uFAFF\uFE10-\uFE6F\uFF00-\uFFEF]/;
  const card = document.querySelector('[data-card]');
  if (!card) { return { error: 'no [data-card] element found' }; }
  const cardRect = card.getBoundingClientRect();

  const parseColor = (value) => {
    const m = String(value || '').match(/rgba?\(([^)]+)\)/);
    if (!m) { return null; }
    const parts = m[1].split(',').map((p) => parseFloat(p.trim()));
    return { r: parts[0], g: parts[1], b: parts[2], a: parts.length > 3 ? parts[3] : 1 };
  };
  const blend = (fg, bg) => {
    const a = fg.a + bg.a * (1 - fg.a);
    if (a === 0) { return { r: 255, g: 255, b: 255, a: 0 }; }
    return {
      r: (fg.r * fg.a + bg.r * bg.a * (1 - fg.a)) / a,
      g: (fg.g * fg.a + bg.g * bg.a * (1 - fg.a)) / a,
      b: (fg.b * fg.a + bg.b * bg.a * (1 - fg.a)) / a,
      a,
    };
  };
  const effectiveBackground = (element) => {
    const stack = [];
    let node = element;
    while (node && node !== document.documentElement.parentNode) {
      const bg = parseColor(getComputedStyle(node).backgroundColor);
      if (bg && bg.a > 0) { stack.push(bg); }
      if (bg && bg.a >= 0.999) { break; }
      node = node.parentElement;
    }
    let base = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = stack.length - 1; i >= 0; i -= 1) { base = blend(stack[i], base); }
    return base;
  };
  const luminance = (c) => {
    const channel = (v) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * channel(c.r) + 0.7152 * channel(c.g) + 0.0722 * channel(c.b);
  };
  const contrast = (a, b) => {
    const la = luminance(a);
    const lb = luminance(b);
    const hi = Math.max(la, lb);
    const lo = Math.min(la, lb);
    return (hi + 0.05) / (lo + 0.05);
  };

  const lineUnits = (node) => {
    const text = node.textContent || '';
    const range = document.createRange();
    const tops = [];
    const units = [];
    for (let i = 0; i < text.length; i += 1) {
      range.setStart(node, i);
      range.setEnd(node, i + 1);
      const rects = range.getClientRects();
      if (!rects.length) { continue; }
      const top = Math.round(rects[0].top);
      const ch = text[i];
      let unit = 0.55;
      if (CJK.test(ch)) { unit = 1; } else if (!ch.trim()) { unit = 0.5; }
      if (!tops.length || Math.abs(tops[tops.length - 1] - top) > 2) {
        tops.push(top);
        units.push(0);
      }
      units[units.length - 1] += unit;
    }
    return units.map((u) => Math.round(u * 10) / 10);
  };

  const roleOf = (element) => {
    const holder = element.closest('[data-role]');
    return holder ? holder.getAttribute('data-role') : null;
  };

  const textEntries = [];
  card.querySelectorAll('*').forEach((element) => {
    const own = Array.from(element.childNodes).filter(
      (n) => n.nodeType === 3 && n.textContent.trim().length > 0
    );
    if (!own.length) { return; }
    const style = getComputedStyle(element);
    if (style.visibility === 'hidden' || style.display === 'none') { return; }
    const rect = element.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) { return; }
    let units = [];
    own.forEach((node) => { units = units.concat(lineUnits(node)); });
    const background = effectiveBackground(element);
    const color = parseColor(style.color) || { r: 0, g: 0, b: 0, a: 1 };
    const opaque = blend(color, background);
    textEntries.push({
      role: roleOf(element),
      text: own.map((n) => n.textContent.trim()).join(' ').slice(0, 120),
      font_size: parseFloat(style.fontSize),
      font_weight: style.fontWeight,
      contrast: Math.round(contrast(opaque, background) * 100) / 100,
      lines: units,
      max_units: units.length ? Math.max.apply(null, units) : 0,
      rect: { x: rect.x - cardRect.x, y: rect.y - cardRect.y, w: rect.width, h: rect.height },
    });
  });

  const overflow = [];
  const bars = [];
  card.querySelectorAll('.bar-row').forEach((row) => {
    const value = row.querySelector('.bar-value');
    const label = row.querySelector('.bar-label');
    const parsed = value ? parseFloat(value.textContent) : NaN;
    bars.push({
      label: label ? label.textContent.trim().slice(0, 40) : '',
      value: Number.isFinite(parsed) ? parsed : null,
    });
  });

  card.querySelectorAll('*').forEach((element) => {
    const style = getComputedStyle(element);
    if (style.display === 'none' || style.visibility === 'hidden') { return; }
    const dy = element.scrollHeight - element.clientHeight;
    const dx = element.scrollWidth - element.clientWidth;
    if (dy > 2 || dx > 2) {
      overflow.push({
        tag: element.tagName.toLowerCase(),
        cls: element.className && element.className.toString().slice(0, 60),
        ellipsis: style.textOverflow === 'ellipsis',
        clips: style.overflowX !== 'visible' || style.overflowY !== 'visible',
        dy, dx,
      });
    }
  });

  const cardBox = {
    x: 0, y: 0,
    w: cardRect.width,
    h: cardRect.height,
  };
  const outOfBounds = [];
  card.querySelectorAll('*').forEach((element) => {
    const style = getComputedStyle(element);
    if (style.display === 'none' || style.visibility === 'hidden') { return; }
    const r = element.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) { return; }
    const x = r.x - cardRect.x;
    const y = r.y - cardRect.y;
    if (x < -2 || y < -2 || x + r.width > cardBox.w + 2 || y + r.height > cardBox.h + 2) {
      outOfBounds.push({
        tag: element.tagName.toLowerCase(),
        cls: element.className && element.className.toString().slice(0, 60),
        dx: Math.round(x), dy: Math.round(y),
        dw: Math.round(x + r.width - cardBox.w), dh: Math.round(y + r.height - cardBox.h),
      });
    }
  });

  const logged = [];
  const style = getComputedStyle(card);
  const padX = parseFloat(style.paddingLeft);
  const padTop = parseFloat(style.paddingTop);
  const padBottom = parseFloat(style.paddingBottom);
  card.querySelectorAll(':scope > *').forEach((element) => {
    const r = element.getBoundingClientRect();
    if (r.width < 1) { return; }
    const left = r.x - cardRect.x;
    const right = left + r.width;
    const top = r.y - cardRect.y;
    const bottom = top + r.height;
    if (left < padX - 1 || right > cardBox.w - padX + 1 || top < padTop - 1 || bottom > cardBox.h - padBottom + 1) {
      logged.push({
        tag: element.tagName.toLowerCase(),
        cls: element.className && element.className.toString().slice(0, 60),
        left: Math.round(left), right: Math.round(right),
        top: Math.round(top), bottom: Math.round(bottom),
      });
    }
  });

  const logo = card.querySelector('[data-brand-logo]');
  const attribution = card.querySelector('[data-attribution]');
  const pageMark = card.querySelector('[data-page]');
  const linked = (element) => Boolean(element.closest('[data-source-ref]'));
  const encodings = Array.from(card.querySelectorAll('[data-encoding]'));
  const skeletons = Array.from(card.querySelectorAll('[data-skeleton]'));

  return {
    canvas: {
      w: cardBox.w,
      h: cardBox.h,
      ratio: card.getAttribute('data-ratio'),
      template: card.getAttribute('data-template'),
      series_index: card.getAttribute('data-series-index'),
      series_size: card.getAttribute('data-series-size'),
      background: style.backgroundColor,
    },
    text_entries: textEntries,
    bars,
    overflow,
    out_of_bounds: outOfBounds,
    safe_violations: logged,
    counts: {
      claims: card.querySelectorAll('[data-claim]').length,
      sources: card.querySelectorAll('[data-source-ref]').length,
      encodings: encodings.length,
      encodings_linked: encodings.filter(linked).length,
      annotations: card.querySelectorAll('[data-annotation]').length,
      skeletons: skeletons.length,
      blocks: card.querySelectorAll('.block, .step, .check, .compare-side, .metric').length,
    },
    logo: logo ? {
      present: Boolean(logo.getAttribute('src')),
      natural_w: logo.naturalWidth,
      natural_h: logo.naturalHeight,
    } : null,
    attribution: attribution ? attribution.textContent.trim() : '',
    page_mark: pageMark ? pageMark.textContent.trim() : '',
    visible_text_length: card.innerText.replace(/\s+/g, '').length,
    title: (card.querySelector('[data-claim]') || {}).innerText || '',
  };
}
"""


def open_card_page(page, html_path: Path, width: int, height: int, scale: int) -> None:
    page.set_viewport_size({"width": width, "height": max(height, 400)})
    page.goto(html_path.resolve().as_uri())
    page.wait_for_timeout(120)
    page.evaluate("() => document.fonts && document.fonts.ready")
    page.wait_for_timeout(60)


def cmd_render(args: argparse.Namespace) -> int:
    sync_playwright = require_playwright()
    html_path = Path(args.input).expanduser()
    if not html_path.is_file():
        raise SystemExit(f"card html not found: {html_path}")
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport={"width": args.width, "height": 1600},
            device_scale_factor=args.scale,
        )
        page = context.new_page()
        page.goto(html_path.resolve().as_uri())
        page.wait_for_timeout(150)
        page.evaluate("() => document.fonts && document.fonts.ready")
        page.wait_for_timeout(80)
        box = page.locator("[data-card]").bounding_box()
        if not box:
            browser.close()
            raise SystemExit("no [data-card] element to capture")
        page.set_viewport_size({"width": args.width, "height": int(box["height"]) + 40})
        page.wait_for_timeout(60)
        page.locator("[data-card]").screenshot(path=str(output))
        browser.close()

    width_px, height_px = png_size(output)
    expected = (int(round(box["width"] * args.scale)), int(round(box["height"] * args.scale)))
    # A `long` card has a fractional height: the element box and the captured bitmap can
    # differ by one device pixel, so allow 1px and flag anything larger.
    ok = all(abs(actual - want) <= 1 for actual, want in zip((width_px, height_px), expected))
    report = {
        "status": "rendered" if ok else "size_mismatch",
        "image": str(output),
        "bytes": output.stat().st_size,
        "px": {"width": width_px, "height": height_px},
        "expected_px": {"width": expected[0], "height": expected[1]},
        "scale": args.scale,
        "elapsed_seconds": round(time.time() - started, 2),
        "html": str(html_path),
    }
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if ok else 1


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:33]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"not a PNG file: {path}")
    return struct.unpack(">II", data[16:24])


# --------------------------------------------------------------------------
# audit
# --------------------------------------------------------------------------


def add_issue(checks: list[dict[str, Any]], check_id: str, level: str,
              ok: bool, detail: str) -> None:
    checks.append({
        "id": check_id,
        "level": level,
        "status": "pass" if ok else "fail",
        "detail": detail,
    })


def audit_measurements(m: dict[str, Any], ratio_expected: tuple[int, int] | None,
                       image_px: tuple[int, int] | None, scale: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    canvas = m["canvas"]
    counts = m["counts"]

    add_issue(checks, "canvas", "critical", canvas["w"] > 0 and canvas["h"] > 0,
              f"画布 {round(canvas['w'])}×{round(canvas['h'])}，模板 {canvas['template']}，比例 {canvas['ratio']}")

    if ratio_expected:
        add_issue(checks, "ratio", "error", ratio_expected[0] == ratio_expected[0] and
                  abs(canvas["w"] - ratio_expected[0]) <= 1,
                  f"期望宽度 {ratio_expected[0]}px，实际 {round(canvas['w'])}px")

    if image_px:
        expected = (round(canvas["w"] * scale), round(canvas["h"] * scale))
        # A `long` card has a fractional content height, so the browser's element box and
        # the captured bitmap can differ by one device pixel; anything larger is a real bug.
        within_one_px = all(abs(actual - want) <= 1 for actual, want in zip(image_px, expected))
        add_issue(checks, "image_size", "error", within_one_px,
                  f"PNG {image_px[0]}×{image_px[1]}，期望 {expected[0]}×{expected[1]}（scale {scale}，容差 1px）")

    if canvas["ratio"] == "long":
        add_issue(checks, "long_height", "warning", canvas["h"] <= LONG_MAX_HEIGHT,
                  f"长卡高度 {round(canvas['h'])}px（上限 {LONG_MAX_HEIGHT}px，即三个 3:4 屏；"
                  "超出应先拆卡或删减）")

    bars = [bar for bar in m.get("bars", []) if bar.get("value") is not None]
    if len(bars) > 1:
        ordered = all(
            bars[index]["value"] >= bars[index + 1]["value"]
            for index in range(len(bars) - 1)
        )
        add_issue(checks, "bar_order", "error", ordered,
                  "条形按数值倒序排列" if ordered else
                  "条形未按数值倒序："
                  + " → ".join(f"{bar['label']} {bar['value']:g}" for bar in bars[:6])
                  + "（排位图必须从大到小，读者靠长度和顺序同时读）")

    tiny = [
        entry for entry in m["text_entries"]
        if entry["font_size"] < FONT_FLOOR.get(entry["role"] or "", DEFAULT_FONT_FLOOR) - 0.5
    ]
    add_issue(checks, "font_floor", "critical", not tiny,
              "全部文本达到字号下限" if not tiny else
              "低于下限：" + "; ".join(
                  f"{entry['role'] or '未标注'} {entry['font_size']}px < "
                  f"{FONT_FLOOR.get(entry['role'] or '', DEFAULT_FONT_FLOOR)}px 「{entry['text'][:18]}」"
                  for entry in tiny[:4]
              ))

    too_long = [
        entry for entry in m["text_entries"]
        if entry["max_units"] > LINE_LIMIT.get(entry["role"] or "", DEFAULT_LINE_LIMIT) + 0.5
    ]
    add_issue(checks, "line_length", "error", not too_long,
              "每行字数在手机可读范围内" if not too_long else
              "行宽超限：" + "; ".join(
                  f"{entry['role'] or '未标注'} 最长 {entry['max_units']} 字 > "
                  f"{LINE_LIMIT.get(entry['role'] or '', DEFAULT_LINE_LIMIT)} 字 「{entry['text'][:18]}」"
                  for entry in too_long[:4]
              ))

    low_contrast = []
    for entry in m["text_entries"]:
        limit = CONTRAST_MIN_LARGE if entry["font_size"] >= LARGE_TEXT_PX else CONTRAST_MIN_BODY
        if entry["contrast"] < limit:
            low_contrast.append((entry, limit))
    add_issue(checks, "contrast", "error", not low_contrast,
              "所有文本对比度达标" if not low_contrast else
              "对比度不足：" + "; ".join(
                  f"{entry['role'] or '未标注'} {entry['contrast']}:1 < {limit}:1 "
                  f"「{entry['text'][:18]}」"
                  for entry, limit in low_contrast[:4]
              ))

    truncated = [item for item in m["overflow"] if item.get("ellipsis")]
    other = [item for item in m["overflow"] if not item.get("ellipsis")]
    overflowing = [item for item in other if item.get("clips", True)]
    glyphs = [item for item in other if not item.get("clips", True)]
    add_issue(checks, "overflow", "critical", not overflowing,
              "无裁切与溢出" if not overflowing else
              "溢出元素：" + "; ".join(
                  f"{item['tag']}.{item['cls']} 纵向 +{item['dy']}px 横向 +{item['dx']}px"
                  for item in overflowing[:4]
              ))
    add_issue(checks, "truncation", "warning", not truncated,
              "无省缺号截断文本" if not truncated else
              "被省略号截断：" + "; ".join(
                  f"{item['tag']}.{item['cls']} 横向 +{item['dx']}px" for item in truncated[:3]
              ))
    add_issue(checks, "glyph_overflow", "warning", not glyphs,
              "文本未溢出自身盒模型" if not glyphs else
              "内容超出自身盒模型（未裁切，但已被压紧）：" + "; ".join(
                  f"{item['tag']}.{item['cls']} 纵向 +{item['dy']}px 横向 +{item['dx']}px"
                  for item in glyphs[:3]
              ))

    add_issue(checks, "out_of_bounds", "critical", not m["out_of_bounds"],
              "所有元素在画布内" if not m["out_of_bounds"] else
              "越界元素：" + "; ".join(
                  f"{item['tag']}.{item['cls']} 偏出 {item['dw']}/{item['dh']}px"
                  for item in m["out_of_bounds"][:4]
              ))

    add_issue(checks, "safe_area", "critical", not m["safe_violations"],
              "内容位于安全区内" if not m["safe_violations"] else
              "越出安全区（左/右/上/下边界）：" + "; ".join(
                  f"{item['tag']}.{item['cls']} [{item['left']},{item['top']}-{item['right']},{item['bottom']}]"
                  for item in m["safe_violations"][:4]
              ))

    add_issue(checks, "single_claim", "critical", counts["claims"] == 1,
              f"data-claim 数量 {counts['claims']}（必须为 1）")

    add_issue(checks, "evidence_linkage", "error",
              counts["sources"] >= 1 and counts["encodings"] == counts["encodings_linked"],
              f"来源引用 {counts['sources']} 处，编码元素 {counts['encodings']} 个，"
              f"其中已挂来源 {counts['encodings_linked']} 个")

    logo = m["logo"]
    # The logotype is required; the credit line is optional (a card about private
    # material may omit it, and the implementation tooling is never mandatory).
    footer_ok = bool(logo and logo["present"] and logo["natural_w"] > 0)
    add_issue(checks, "brand_footer", "critical", footer_ok,
              f"品牌页脚 Logo 完整，署名「{m['attribution'] or '（未署名）'}」"
              if footer_ok else f"Logo={logo}")

    title_text = (m.get("title") or "").strip()
    has_number = bool(re.search(r"\d", title_text))
    judgment_cues = ("应该", "必须", "值得", "才是", "不是", "而是", "其实", "真正",
                     "反而", "意味着", "只能", "更", "最", "成了", "正在", "决定")
    add_issue(checks, "title_is_thesis", "warning",
              not has_number or any(cue in title_text for cue in judgment_cues),
              "标题是判断句" if not has_number or any(cue in title_text for cue in judgment_cues)
              else f"标题像事实陈述「{title_text[:24]}」：信息图标题应给出观点或主题，数字留给图表")

    sensitive = ("db_storage", "sqlcipher", ".db", "wxid_", "/Users/", "~/Library", "Msg_")
    leaked = [entry for entry in m["text_entries"]
              if any(pattern.lower() in (entry["text"] or "").lower() for pattern in sensitive)]
    add_issue(checks, "source_hygiene", "error", not leaked,
              "来源行只含对外可披露的来源"
              if not leaked else
              "文本疑似泄漏内部数据来源：" + "; ".join(
                  f"「{(entry['text'] or '')[:24]}」" for entry in leaked[:3]
              ) + "（内部数据库路径、表名与工具名不要出现在卡片上）")

    size = int(canvas["series_size"] or 1)
    index = int(canvas["series_index"] or 1)
    # A single card is not a series: no page mark is the correct state there.
    if size <= 1:
        page_ok = True
        page_detail = "单卡不需要页码标记"
    else:
        page_ok = bool(re.fullmatch(rf"{index}/{size}", m["page_mark"]))
        page_detail = f"页码标记「{m['page_mark']}」，系列 {index}/{size}"
    add_issue(checks, "series_page", "warning", page_ok, page_detail)

    add_issue(checks, "skeleton_replaced", "critical", counts["skeletons"] == 0,
              "骨架文案已全部替换" if counts["skeletons"] == 0 else
              f"仍有 {counts['skeletons']} 处 data-skeleton 未替换")

    add_issue(checks, "copy_volume", "warning", m["visible_text_length"] >= 60,
              f"可见文字 {m['visible_text_length']} 字（建议 ≥ 60，过少说明卡片信息量不足）")

    context = {
        "template": canvas["template"],
        "ratio": canvas["ratio"],
        "canvas_px": {"width": round(canvas["w"]), "height": round(canvas["h"])},
        "text_entries": len(m["text_entries"]),
        "counts": counts,
        "page_mark": m["page_mark"],
    }
    return checks, context


def cmd_audit(args: argparse.Namespace) -> int:
    sync_playwright = require_playwright()
    html_path = Path(args.input).expanduser()
    if not html_path.is_file():
        raise SystemExit(f"card html not found: {html_path}")
    image_path = Path(args.image).expanduser() if args.image else None
    if image_path and not image_path.is_file():
        raise SystemExit(f"image not found: {image_path}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": args.width, "height": 1600})
        page = context.new_page()
        page.goto(html_path.resolve().as_uri())
        page.wait_for_timeout(150)
        page.evaluate("() => document.fonts && document.fonts.ready")
        page.wait_for_timeout(80)
        # `long` cards grow with their content: size the viewport to the card first so
        # the measurement and the captured bitmap agree on the same layout pass.
        box = page.locator("[data-card]").bounding_box()
        if box:
            page.set_viewport_size({"width": args.width, "height": int(box["height"]) + 40})
            page.wait_for_timeout(60)
        measured = page.evaluate(MEASURE_JS)
        browser.close()

    if "error" in measured:
        raise SystemExit(measured["error"])

    ratio_expected = RATIOS.get(args.ratio) if args.ratio else None
    image_px = png_size(image_path) if image_path else None
    checks, context = audit_measurements(measured, ratio_expected, image_px, args.scale)

    score = 100
    for check in checks:
        if check["status"] == "fail":
            score -= SCORE_DEDUCTION.get(check["level"], 2)
    score = max(0, score)

    failures = [check for check in checks if check["status"] == "fail"]
    critical_failures = [check for check in failures if check["level"] == "critical"]
    machine_pass = not critical_failures and score >= SCORE_THRESHOLD

    human_status = args.human_review or "pending"
    if human_status == "passed" and not (image_path and args.review_note):
        human_status = "invalid"
    if human_status == "invalid":
        raise SystemExit("--human-review passed requires both --image and a specific --review-note")
    if args.strict and human_status != "passed":
        machine_pass = False

    report = {
        "schema": "lov-mobile-infographic/audit/v1",
        "generated_at": now_iso(),
        "input": str(html_path),
        "image": str(image_path) if image_path else None,
        "scale": args.scale,
        "context": context,
        "score": score,
        "threshold": SCORE_THRESHOLD,
        "machine_pass": machine_pass,
        "strict": bool(args.strict),
        "human_review": {"status": human_status, "note": args.review_note or ""},
        "checks": checks,
        "failures": [check["id"] for check in failures],
        "status": "pass" if machine_pass else "fail",
    }
    report_path = Path(args.report).expanduser() if args.report else html_path.with_suffix(".audit.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    summary = {
        "status": report["status"],
        "score": score,
        "failures": report["failures"],
        "human_review": human_status,
        "report": str(report_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if report["status"] == "pass" else 1


# --------------------------------------------------------------------------
# brand initialization
# --------------------------------------------------------------------------


def cmd_init_brand(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser()
    if target.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite existing brand profile: {target}")
    logo = Path(args.logo).expanduser()
    if args.logo and not logo.is_file():
        raise SystemExit(f"logo not found: {logo}")
    profile = {
        "schema_version": 1,
        "name": args.name,
        "site": args.site,
        "logo": args.logo,
        "primary": args.primary,
        "accent": args.accent,
        "accent_ink": args.accent_ink,
        "ink": args.ink,
        "muted": args.muted,
        "paper": args.paper,
        "font_family": args.font_family,
        "attribution": args.attribution,
        "output_dir": args.output_dir,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "brand_initialized",
        "path": str(target),
        "name": profile["name"],
        "logo": bool(profile["logo"]),
        "next": "scaffold 时用 --brand-profile 指向该文件，或设置 SKILL_MOBILE_INFOGRAPHIC_BRAND_PROFILE",
    }, ensure_ascii=False, indent=1))
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def default_brand_path() -> str:
    return str(Path.home() / ".config" / "lov-mobile-infographic" / "brand-profile.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-brand", help="write a brand profile JSON")
    init.add_argument("--name", required=True)
    init.add_argument("--logo", default="", help="absolute path to a logo image")
    init.add_argument("--site", default="")
    init.add_argument("--attribution", default="Powered by")
    init.add_argument("--primary", default="#182033")
    init.add_argument("--accent", default="#EB6637")
    init.add_argument(
        "--accent-ink",
        default="#B0491A",
        help="emphasis color used for text on paper; must reach 4.5:1 contrast",
    )
    init.add_argument("--ink", default="#172033")
    init.add_argument("--muted", default="#4A5468")
    init.add_argument("--paper", default="#F7F4EF")
    init.add_argument(
        "--font-family",
        default="PingFang SC, Hiragino Sans GB, Microsoft YaHei, Inter, sans-serif",
    )
    init.add_argument("--output-dir", default="$HOME/Documents/mobile-infographic")
    init.add_argument("--path", default=default_brand_path())
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init_brand)

    scaffold = sub.add_parser("scaffold", help="assemble an editable card.html")
    scaffold.add_argument("--template", default="single-claim", choices=TEMPLATES)
    scaffold.add_argument(
        "--ratio",
        default="long",
        choices=tuple(RATIOS),
        help="default 'long': one card whose height follows the content",
    )
    scaffold.add_argument("--title", required=True)
    scaffold.add_argument("--claim", default="")
    scaffold.add_argument("--eyebrow", default="")
    scaffold.add_argument("--source", default="待补充来源")
    scaffold.add_argument(
        "--row",
        action="append",
        metavar="LABEL|VALUE|DESCRIPTION|MEMBERS|GROUP",
        help="bar-ranking row (repeatable): line 1 = item + description, line 2 = bar + count + roster",
    )
    scaffold.add_argument("--source-id", default="S1")
    scaffold.add_argument("--series-index", type=int, default=1)
    scaffold.add_argument("--series-size", type=int, default=1)
    scaffold.add_argument("--output-dir", required=True)
    scaffold.add_argument("--filename", default="card.html")
    scaffold.add_argument("--brand-profile", default=None)
    scaffold.add_argument("--force", action="store_true")
    scaffold.set_defaults(func=cmd_scaffold)

    render = sub.add_parser("render", help="render card.html to an exact-pixel PNG")
    render.add_argument("--input", required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--width", type=int, default=1080)
    render.add_argument("--scale", type=int, default=2)
    render.set_defaults(func=cmd_render)

    audit = sub.add_parser("audit", help="measure mobile readability and the visual contract")
    audit.add_argument("--input", required=True)
    audit.add_argument("--image", default=None)
    audit.add_argument("--report", default=None)
    audit.add_argument("--ratio", default=None, choices=tuple(RATIOS))
    audit.add_argument("--width", type=int, default=1080)
    audit.add_argument("--scale", type=int, default=2)
    audit.add_argument("--human-review", choices=("passed", "failed", "pending"), default=None)
    audit.add_argument("--review-note", default=None)
    audit.add_argument("--strict", action="store_true")
    audit.set_defaults(func=cmd_audit)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
