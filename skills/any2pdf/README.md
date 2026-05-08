# lovstudio-any2pdf

![Version](https://img.shields.io/badge/version-1.3.4-CC785C)

Markdown to professionally typeset PDF with [reportlab](https://docs.reportlab.com/). CJK/Latin mixed text, code blocks, tables, images, Obsidian callouts, emoji fallback, formulas, cover pages, TOC, bookmarks, watermarks, and 14 color themes.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx lovstudio skills add any2pdf -g -y
```

Requires: Python 3.8+ and `pip install reportlab`

Optional:

```bash
pip install matplotlib
sudo apt install fonts-dejavu-core fonts-liberation fonts-freefont-ttf fonts-noto fonts-noto-cjk fonts-noto-color-emoji
```

## Usage

```bash
python md2pdf.py --input report.md --output report.pdf --theme warm-academic
```

You can also keep options in top-of-file frontmatter:

```markdown
---
title: My Report
author: Author Name
theme: warm-academic
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
| `--theme` | `warm-academic` | Color theme |
| `--watermark` | | Watermark text |
| `--cover` | `true` | Generate cover page |
| `--toc` | `true` | Generate table of contents |
| `--frontispiece` | | Full-page image after cover |
| `--code-max-lines` | `30` | Max lines per code block |
| `--image-cover` | `false` | Use frontispiece image as full-bleed cover |

## Themes

| warm-academic | nord-frost | github-light | solarized-light |
|:---:|:---:|:---:|:---:|
| ![warm-academic](../../docs/previews/warm-academic.png) | ![nord-frost](../../docs/previews/nord-frost.png) | ![github-light](../../docs/previews/github-light.png) | ![solarized-light](../../docs/previews/solarized-light.png) |

| paper-classic | ocean-breeze | tufte | classic-thesis |
|:---:|:---:|:---:|:---:|
| ![paper-classic](../../docs/previews/paper-classic.png) | ![ocean-breeze](../../docs/previews/ocean-breeze.png) | ![tufte](../../docs/previews/tufte.png) | ![classic-thesis](../../docs/previews/classic-thesis.png) |

| ieee-journal | elegant-book | chinese-red | ink-wash |
|:---:|:---:|:---:|:---:|
| ![ieee-journal](../../docs/previews/ieee-journal.png) | ![elegant-book](../../docs/previews/elegant-book.png) | ![chinese-red](../../docs/previews/chinese-red.png) | ![ink-wash](../../docs/previews/ink-wash.png) |

| monokai-warm | dracula-soft |
|:---:|:---:|
| ![monokai-warm](../../docs/previews/monokai-warm.png) | ![dracula-soft](../../docs/previews/dracula-soft.png) |

## License

MIT
