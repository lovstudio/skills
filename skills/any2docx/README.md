# lovstudio:any2docx

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

Markdown to professionally styled DOCX (Word) with [python-docx](https://python-docx.readthedocs.io/). CJK/Latin mixed text, code blocks, tables, **images** (local + remote), cover pages, auto-refresh TOC, watermarks, and 11 color themes. Same theme palette as any2pdf, editable output.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:any2docx
```

Requires: Python 3.8+ and `pip install python-docx`

## Usage

```bash
python md2docx.py --input report.md --output report.docx --theme warm-academic
```

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | (required) | Markdown file path |
| `--output` | `output.docx` | Output DOCX path |
| `--title` | From H1 | Cover page title |
| `--subtitle` | | Subtitle |
| `--author` | | Author name |
| `--theme` | `warm-academic` | Color theme |
| `--watermark` | | Watermark text |
| `--cover` | `true` | Generate cover page |
| `--toc` | `true` | Generate table of contents |

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
