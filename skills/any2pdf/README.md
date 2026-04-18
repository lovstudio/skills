# lovstudio:any2pdf

![Version](https://img.shields.io/badge/version-1.2.0-CC785C)

Markdown to professionally typeset PDF with [reportlab](https://docs.reportlab.com/). CJK/Latin mixed text, code blocks, tables, cover pages, TOC, bookmarks, watermarks, and 14 color themes.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:any2pdf
```

Requires: Python 3.8+ and `pip install reportlab`

## Usage

```bash
python md2pdf.py --input report.md --output report.pdf --theme warm-academic
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