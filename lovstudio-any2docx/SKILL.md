---
name: lovstudio:any2docx
description: >
  Convert Markdown documents to professionally styled DOCX (Word) files with python-docx.
  Handles CJK/Latin mixed text, fenced code blocks, tables, blockquotes, cover pages,
  TOC field, watermarks, and page numbers. Supports multiple color themes matching
  any2pdf (Warm Academic, Nord, GitHub Light, etc.) and is battle-tested for Chinese
  technical reports. Use this skill whenever the user wants to turn a .md file into a
  styled Word document, generate an editable report from markdown, or create a DOCX
  from markdown content — especially if CJK characters, code blocks, or tables are
  involved. Also trigger when the user mentions "markdown to docx", "md2docx",
  "any2docx", "md转word", "md转docx", "生成word", or asks for an "editable document"
  from markdown source.
license: MIT
compatibility: >
  Requires Python 3.8+ and python-docx (`pip install python-docx`).
  Cross-platform: macOS, Windows, Linux.
  CJK fonts: macOS uses Songti SC, Windows uses SimSun, Linux uses Noto Serif CJK SC.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: markdown docx word cjk python-docx typesetting
---

# any2docx — Markdown to Professional DOCX

This skill converts any Markdown file into a professionally styled Word document using
Python's python-docx library. It shares the same theme palette as any2pdf and handles
all CJK/Latin edge cases correctly.

## When to Use

- User wants to convert `.md` → `.docx` (Word)
- User needs an **editable** document (not PDF)
- Document contains CJK characters mixed with Latin text
- Document has fenced code blocks, markdown tables, or lists
- User wants a cover page, table of contents, or watermark in their DOCX

## Quick Start

```bash
python lovstudio-any2docx/scripts/md2docx.py \
  --input report.md \
  --output report.docx \
  --title "My Report" \
  --author "Author Name" \
  --theme warm-academic
```

All parameters except `--input` are optional — sensible defaults are applied.

## Pre-Conversion Options (MANDATORY)

**IMPORTANT: You MUST use the `AskUserQuestion` tool to ask these questions BEFORE
running the conversion. Do NOT list options as plain text — use the tool so the user
gets a proper interactive prompt. Ask all options in a SINGLE `AskUserQuestion` call.**

Use `AskUserQuestion` with the following template:

```
开始转 Word！先帮你确认几个选项 👇

━━━ 📐 设计风格 ━━━
 a) 暖学术    — 陶土色调，温润典雅，适合人文/社科报告
 b) 经典论文  — 棕色调，灵感源自 LaTeX classicthesis，适合学术论文
 c) Tufte     — 极简留白，深红点缀，适合数据叙事/技术写作
 d) 期刊蓝    — 藏蓝严谨，灵感源自 IEEE，适合正式发表风格
 e) 精装书    — 咖啡色调，书卷气，适合长篇专著/技术书
 f) 中国红    — 朱红配暖纸，适合中文正式报告/白皮书
 g) 水墨      — 纯灰黑，素雅克制，适合文学/设计类内容
 h) GitHub    — 蓝白极简，程序员熟悉的风格
 i) Nord 冰霜 — 蓝灰北欧风，清爽现代
 j) 海洋      — 青绿色调，清新自然
 k) 投资报告  — 楷体+深红，专业严谨，适合投资/尽调报告

━━━ 💧 水印 ━━━
 1) 不加
 2) 自定义文字（如 "DRAFT"、"内部资料"）

示例回复："a, 水印:仅供内部参考"
直接说人话就行，不用记编号 😄
```

### Mapping User Choices to CLI Args

| Choice | CLI arg |
|--------|---------|
| Design style a-k | `--theme` with value from table below |
| Watermark text | `--watermark "文字"` |

### Theme Name Mapping

| Choice | `--theme` value |
|--------|----------------|
| a) 暖学术 | `warm-academic` |
| b) 经典论文 | `classic-thesis` |
| c) Tufte | `tufte` |
| d) 期刊蓝 | `ieee-journal` |
| e) 精装书 | `elegant-book` |
| f) 中国红 | `chinese-red` |
| g) 水墨 | `ink-wash` |
| h) GitHub | `github-light` |
| i) Nord | `nord-frost` |
| j) 海洋 | `ocean-breeze` |
| k) 投资报告 | `invest-report` |

## Architecture

```
Markdown → Preprocess (split merged headings) → Parse (code-fence-aware) → python-docx Document → .docx
```

Key components:
1. **CJK font switching**: `_split_mixed()` detects CJK runs and assigns Songti SC / SimSun / Noto CJK
2. **Inline markdown**: `_parse_inline()` handles **bold**, *italic*, `code`, [links](url)
3. **Code blocks**: Shaded paragraph with monospace font and border
4. **Tables**: Header row with accent background, alternating row shading
5. **Watermark**: VML-based diagonal watermark in header (Word-native)
6. **TOC**: Field code that Word/WPS updates on open

## Configuration Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | Path to markdown file |
| `--output` | `output.docx` | Output DOCX path |
| `--title` | From first H1 | Document title for cover page |
| `--subtitle` | `""` | Subtitle text |
| `--author` | `""` | Author name |
| `--date` | Today | Date string |
| `--version` | `""` | Version string for cover |
| `--watermark` | `""` | Watermark text (empty = none) |
| `--theme` | `warm-academic` | Color theme name |
| `--cover` | `true` | Generate cover page |
| `--toc` | `true` | Generate table of contents |
| `--header-title` | `""` | Report title in page header |
| `--footer-left` | author | Brand/author in footer |
| `--stats-line` | `""` | Stats on cover |
| `--stats-line2` | `""` | Second stats line |
| `--edition-line` | `""` | Edition line on cover |
| `--code-max-lines` | `30` | Max lines per code block |

## Dependencies

```bash
pip install python-docx --break-system-packages
```
