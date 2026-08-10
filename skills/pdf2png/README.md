# lov-pdf2png

![Version](https://img.shields.io/badge/version-0.1.2-CC785C)

Convert PDF files to a single vertically concatenated PNG image using macOS native CoreGraphics.

Part of [skill-publisher/skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add pdf2png -g -y
```

Requires: macOS, `pip install pyobjc-framework-Quartz`

## Usage

```bash
bash pdf2png.sh input.pdf           # → input.png
bash pdf2png.sh a.pdf b.pdf c.pdf   # batch mode
```

## How It Works

```
┌─────────┐     CoreGraphics      ┌─────────┐
│  PDF     │  ──── render ────►   │  Page 1  │
│ (N pages)│     2x scale         │  Page 2  │
│          │                      │  ...     │
│          │                      │  Page N  │
└─────────┘                       └────┬─────┘
                                       │ vertical append
                                       ▼
                                  ┌─────────┐
                                  │ one.png  │
                                  └─────────┘
```

## Why Not pdftoppm + ImageMagick?

| | pdftoppm + magick | CoreGraphics |
|---|---|---|
| 27MB / 20 pages | ~3 minutes | ~3 seconds |
| Dependencies | Homebrew (poppler, imagemagick) | None (macOS built-in) |
| Retina quality | Manual DPI flag | Native 2x scale |

## Also Available As

- **Finder Quick Action**: Right-click any PDF → "PDF to PNG". See [skill-publisher/mac-pdf2png](https://example.com/skills/mac-pdf2png).

## License

MIT