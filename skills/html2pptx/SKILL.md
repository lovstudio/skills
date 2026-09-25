---
name: lov-html2pptx
description: >
  Convert HTML into a high-fidelity PPTX deck using a real browser engine
  (Playwright/Chromium). Each `.slide` element in the HTML becomes one
  pptx page (rendered as a 16:9 1920×1080 retina image), so any CSS layout —
  flex/grid, webfonts, gradients, SVG — survives intact. Also ships a local
  live editor (`edit_html.py`) so the user can tweak HTML in the browser
  and one-click export PPTX.
  Trigger when the user asks to "用 HTML 做 PPT", "html 转 pptx", "html2pptx",
  "html slides", "html 幻灯片", "把这个 html 导出成 ppt", "edit html and
  export ppt", "build a deck from html", or hands you an HTML file with
  `.slide` sections.
license: MIT
compatibility: >
  Requires Python 3.9+, `playwright` (with chromium installed) and
  `python-pptx`. Cross-platform: macOS, Windows, Linux.
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.1.2"
  tags: html pptx slides presentation playwright deck
---

# 网页转幻灯 · HTML to Slides

Render any HTML file into a polished `.pptx` deck. One `.slide` element →
one pptx page. Each page is screenshotted at 1920×1080 @ 2× by Chromium
and embedded as a full-bleed image, so CSS-grid layouts, webfonts and SVG
all reproduce pixel-perfect.

Two modes:

- **Direct**: HTML in, PPTX out (`html2pptx.py`).
- **Interactive**: live editor in the browser with a Save / Export PPTX
  toolbar (`edit_html.py`).

## When to Use

- User has a polished HTML mockup and wants it as PPTX.
- User wants pixel-perfect control over slide design via CSS — going beyond
  what `python-pptx` template hacks allow.
- User wants to iterate on slides interactively in the browser.
- User says: "用 html 做 ppt", "html 转 pptx", "把这个 html 导出成幻灯片",
  "build a deck from this html", "edit html ppt", "html2pptx".

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1 — Confirm dependencies

If this is the first run on the machine, install:

```bash
pip install playwright python-pptx --break-system-packages
python3 -m playwright install chromium
```

The skill won't work without Chromium downloaded by Playwright.

### Step 2 — Ask the user (use `AskUserQuestion`)

Collect these BEFORE running the script:

| Question | Header | Options |
|---|---|---|
| One-shot conversion or live editor? | Mode | `Direct convert` / `Live editor` |
| Slide size? | Size | `1920×1080 (16:9, default)` / `1280×720` / `1024×768 (4:3)` / `Custom` |
| How are slides separated in the HTML? | Split mode | `Auto-detect (default)` / `By selector (.slide)` / `Single page` |

Skip questions whose answer is obvious from context (e.g. user already
provided a path AND said "convert it" → mode = direct).

### Step 3 — Run

**Direct mode:**

```bash
python3 scripts/html2pptx.py \
  --input path/to/deck.html \
  --output ./output/deck.pptx \
  --size 1920x1080 \
  --scale 2
```

**Live editor mode:**

```bash
python3 scripts/edit_html.py \
  --input path/to/deck.html
```

The editor opens at http://127.0.0.1:5757 with two panes (HTML on the
left, live preview on the right) and an `Export PPTX` button. If
`--input` doesn't exist, a starter template is created.

### Step 4 — Output location

Per the user's global convention, write deliverables to
`./output/articles/` or `./output/data/`. PPTX files default to
`./output/品牌方-{topic}-{YYYY-MM-DD}-v0.1.pptx`.

## Slide Splitting Rules

| `--split` | Behavior |
|---|---|
| `auto` (default) | If `.slide`, `section.slide`, or `[data-slide]` matches → use `selector`. Otherwise `single`. |
| `selector` | Each element matching `--selector` becomes one pptx page (its width/height are forced to the slide size before screenshot). |
| `single` | Render the whole HTML as ONE pptx page. |

## CLI Reference — `html2pptx.py`

| Argument | Default | Description |
|----------|---------|-------------|
| `--input`, `-i` | (required) | Source `.html` path |
| `--output`, `-o` | (required) | Destination `.pptx` path |
| `--size` | `1920x1080` | Slide pixel dimensions `WxH` |
| `--scale` | `2.0` | Device pixel ratio (2.0 = retina) |
| `--split` | `auto` | `auto` / `selector` / `single` |
| `--selector` | `.slide, section.slide, [data-slide]` | CSS selector for slide elements |

## CLI Reference — `edit_html.py`

| Argument | Default | Description |
|----------|---------|-------------|
| `--input`, `-i` | (required) | `.html` to edit (created if missing) |
| `--port` | `5757` | Server port |
| `--host` | `127.0.0.1` | Bind host |
| `--size` | `1920x1080` | Forwarded to `html2pptx.py` on export |
| `--scale` | `2.0` | Forwarded |
| `--split` | `auto` | Forwarded |
| `--selector` | `.slide, section.slide, [data-slide]` | Forwarded |
| `--no-open` | off | Don't auto-open browser |

## HTML Template Pattern

Recommended pattern — full example at `references/example.html`:

```html
<style>
  .slide {
    width: 1920px; height: 1080px;
    padding: 80px;
    page-break-after: always;
  }
</style>
<section class="slide cover">…</section>
<section class="slide body">…</section>
```

The renderer **forces** each slide's width/height to match `--size` before
screenshot, so out-of-flow children (absolutely positioned, transforms,
etc.) are still cropped correctly.

## Dependencies

```bash
pip install playwright python-pptx --break-system-packages
python3 -m playwright install chromium
```

## Troubleshooting

- **"selector matched 0 elements"** — your HTML doesn't use `.slide`. Pass
  `--split single` or supply a custom `--selector ".your-class"`.
- **Webfont didn't load** — make sure your `@import`/`<link>` is reachable.
  The renderer waits for `networkidle` and `document.fonts.ready`, but
  external fonts still need network access.
- **Chinese characters render as boxes** — install a CJK system font or
  embed one via `@font-face`. PingFang SC / Noto Sans CJK work well.
- **Output pptx looks blurry on a 4K monitor** — bump `--scale 3`.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
