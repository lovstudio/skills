---
name: lovstudio:md2pdf
description: >
  Convert Markdown files to PDF using pandoc + xelatex with CJK support
  (PingFang SC). Simple, fast, no Python dependencies — just pandoc and
  a TeX distribution. Trigger when the user mentions "md to pdf",
  "markdown转pdf", "md转pdf", "markdown to pdf", or wants a quick PDF
  from a markdown file. Note: for professionally typeset PDFs with cover
  pages, TOC, themes, use lovstudio:any2pdf instead.
license: MIT
compatibility: >
  macOS (uses PingFang SC font). Requires pandoc and a TeX distribution
  with xelatex (`brew install pandoc basictex`).
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: markdown pdf pandoc xelatex cjk finder-action
---

# md2pdf — Markdown to PDF (pandoc)

Quick conversion from Markdown to PDF using pandoc + xelatex. Supports CJK text
out of the box with PingFang SC. For simple documents where you just need a clean
PDF — no cover page, no TOC, no themes.

For feature-rich PDF generation, use `lovstudio:any2pdf` instead.

## When to Use

- User wants a quick PDF from a markdown file
- Document is simple (no need for cover page, TOC, watermarks)
- User explicitly asks for pandoc-based conversion

## Workflow

### Step 1: Identify markdown files

Locate the `.md` file(s) the user wants to convert.

### Step 2: Execute

```bash
bash lovstudio-md2pdf/scripts/md2pdf.sh /path/to/file.md
```

Output: `/path/to/file.pdf` (same directory, same name, `.pdf` extension).

For multiple files:

```bash
bash lovstudio-md2pdf/scripts/md2pdf.sh file1.md file2.md file3.md
```

### Step 3: Verify

Check the output file exists and report its size.

## CLI Reference

| Argument | Description |
|----------|-------------|
| `file1.md [file2.md ...]` | One or more Markdown files to convert |

Output is always `<input>.pdf` in the same directory as the input file.

## Finder Quick Action

This skill can also be installed as a macOS Finder Quick Action for right-click
conversion. See [lovstudio/mac-md2pdf](https://github.com/lovstudio/mac-md2pdf)
for the Automator workflow.

## Dependencies

```bash
brew install pandoc basictex
```
