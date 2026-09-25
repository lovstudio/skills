# 网页转幻灯 · HTML to Slides

![Version](https://img.shields.io/badge/version-0.1.2-CC785C)

Convert HTML to a high-fidelity PPTX deck via Playwright/Chromium.
Each `.slide` element becomes one pptx page (rendered as a 1920×1080 retina
image), so any CSS layout — flex, grid, webfonts, gradients, SVG — survives
intact. Includes a local live editor for browser-based editing with one-click
PPTX export.

Part of [skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add html2pptx -g -y
pip install playwright python-pptx --break-system-packages
python3 -m playwright install chromium
```

Requires Python 3.9+.

## Usage

### Direct: HTML → PPTX

```bash
python3 scripts/html2pptx.py \
  --input deck.html \
  --output deck.pptx
```

### Live editor

```bash
python3 scripts/edit_html.py \
  --input deck.html
```

Opens `http://127.0.0.1:5757` with HTML on the left, live preview on the
right, and an **Export PPTX** button on the toolbar. If `deck.html` doesn't
exist, a starter template is created.

## How splitting works

```
┌─ deck.html ────────────────────┐
│  <section class="slide">…</…>   │ ──┐
│  <section class="slide">…</…>   │ ──┼──► one pptx page per match
│  <section class="slide">…</…>   │ ──┘
└────────────────────────────────┘
        Playwright screenshots ↓
        python-pptx packs ↓
        deck.pptx (3 pages, 1920×1080)
```

Splitting is auto-detected:

- `.slide`, `section.slide`, or `[data-slide]` present → element-by-element
- Otherwise → render the whole page as one slide

Override with `--split single` or `--selector ".your-class"`.

## Options

### `html2pptx.py`

| Option | Default | Description |
|--------|---------|-------------|
| `--input`, `-i` | (required) | Source HTML path |
| `--output`, `-o` | (required) | Output `.pptx` path |
| `--size` | `1920x1080` | Slide pixel dimensions |
| `--scale` | `2.0` | Device pixel ratio (2.0 = retina) |
| `--split` | `auto` | `auto` / `selector` / `single` |
| `--selector` | `.slide, section.slide, [data-slide]` | CSS selector for slide elements |

### `edit_html.py`

| Option | Default | Description |
|--------|---------|-------------|
| `--input`, `-i` | (required) | HTML file to edit (created if missing) |
| `--port` | `5757` | Server port |
| `--host` | `127.0.0.1` | Bind host |
| `--size` | `1920x1080` | Forwarded on export |
| `--scale` | `2.0` | Forwarded on export |
| `--split` | `auto` | Forwarded on export |
| `--selector` | `.slide, section.slide, [data-slide]` | Forwarded on export |
| `--no-open` | off | Don't auto-open browser |

## Template

A ready-to-copy reference deck lives at
[`references/example.html`](references/example.html). Open it in a browser to
see the recommended `.slide` pattern and the Skill Publisher Configurable Academic palette
(`#181818`, `#F9F9F7`, `#4F46E5`).

## License

MIT
