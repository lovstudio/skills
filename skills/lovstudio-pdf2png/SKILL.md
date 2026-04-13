---
name: lovstudio:pdf2png
description: >
  Convert PDF files to a single vertically concatenated PNG image using macOS
  native CoreGraphics. Each page is rendered at 2x scale and stitched top-to-bottom.
  ~20x faster than pdftoppm+ImageMagick, zero external dependencies on macOS.
  Trigger when the user mentions "pdf to png", "pdf转png", "PDF转图片",
  "pdf拼接", "pdf截图", "convert pdf to image", or wants to turn a multi-page
  PDF into one long PNG.
license: MIT
compatibility: >
  macOS only. Requires pyobjc-framework-Quartz (`pip install pyobjc-framework-Quartz`).
  Uses native CoreGraphics + AppKit via Python bridge.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: pdf png macos coregraphics finder-action
---

# pdf2png — PDF to Vertically Concatenated PNG

Convert multi-page PDF files into a single tall PNG image. All pages are rendered
at 2x scale (Retina quality) and stitched vertically. Uses macOS CoreGraphics
directly — no pdftoppm, no ImageMagick, no Ghostscript.

## When to Use

- User wants to convert a PDF to a single PNG image
- User needs a long screenshot-style image of a PDF
- User wants to share PDF content as an image (WeChat, social media, etc.)

## Workflow

### Step 1: Identify PDF files

Locate the PDF file(s) the user wants to convert. Confirm the path(s).

### Step 2: Execute

```bash
bash lovstudio-pdf2png/scripts/pdf2png.sh /path/to/file.pdf
```

Output: `/path/to/file.png` (same directory, same name, `.png` extension).

For multiple files:

```bash
bash lovstudio-pdf2png/scripts/pdf2png.sh file1.pdf file2.pdf file3.pdf
```

### Step 3: Verify

Check the output file exists and report its size.

## CLI Reference

| Argument | Description |
|----------|-------------|
| `file1.pdf [file2.pdf ...]` | One or more PDF files to convert |

Output is always `<input>.png` in the same directory as the input file.

## Finder Quick Action

This skill can also be installed as a macOS Finder Quick Action for right-click
conversion. See [lovstudio/mac-pdf2png](https://github.com/lovstudio/mac-pdf2png)
for the Automator workflow.

## Dependencies

```bash
pip install pyobjc-framework-Quartz --break-system-packages
```
