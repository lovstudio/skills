# PDF大师 · PDF Master

![Version](https://img.shields.io/badge/version-1.5.2-CC785C)

Markdown to professionally typeset PDF with [reportlab](https://docs.reportlab.com/). CJK/Latin mixed text, code blocks, tables, images, Obsidian callouts, emoji fallback, formulas, cover pages, TOC, bookmarks, watermarks, and 16 themes.

Part of [skill-publisher/skills](https://example.com/skills/skills) &mdash; by [example.com](https://example.com)

## Install

```bash
npx skills add any2pdf -g -y
```

Requires: Python 3.8+ and `pip install reportlab`

Optional:

```bash
pip install matplotlib
sudo apt install fonts-dejavu-core fonts-liberation fonts-freefont-ttf fonts-noto fonts-noto-cjk fonts-noto-color-emoji
```

## Usage

```bash
python md2pdf.py --input report.md --output report.pdf
```

With no explicit theme, the CLI analyzes the title, prose, code blocks, tables,
and document structure, then selects an appropriate preset. Pass `--theme NAME`
or set `theme:` in frontmatter to override it.

For long Chinese reports and dense tables, use the publication-style reading preset:

```bash
python md2pdf.py --input report.md --output report.pdf --theme songti-reading
```

`songti-reading` pairs Songti body text with sans-serif headings/emphasis, Palatino
Latin prose, Menlo code, roomier leading, symbol fallback, and a fit-width opening view.

You can also keep options in top-of-file frontmatter:

```markdown
---
title: My Report
author: Author Name
theme: auto
watermark: DRAFT
---
```

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | (required) | Markdown file path |
| `--output` | `output.pdf` | Output PDF path |
| `--title` | From H1 | Cover page title |
| `--subtitle` | | Subtitle |
| `--author` | | Author name |
| `--theme` | content-aware `auto` | Color theme |
| `--watermark` | | Watermark text |
| `--cover` | `true` | Generate cover page |
| `--toc` | `true` | Generate table of contents |
| `--frontispiece` | | Full-page image after cover |
| `--code-max-lines` | `30` | Max lines per code block |
| `--image-cover` | `false` | Use frontispiece image as full-bleed cover |

## Themes

No single preset is the universal default. `songti-reading` is a strong choice when
sustained Chinese reading matters more than compact page count; other content types
are matched to the themes below.

| Reading and print | Technical and modern | Specialized |
|---|---|---|
| songti-reading | github-light | consulting-navy |
| warm-academic | nord-frost | ieee-journal |
| paper-classic | ocean-breeze | elegant-book |
| classic-thesis | solarized-light | chinese-red |
| tufte | monokai-warm / dracula-soft | ink-wash |

## License

MIT
