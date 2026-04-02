---
name: lovstudio:any2pdf
description: >
  Convert Markdown documents to professionally typeset PDF files with reportlab.
  Handles CJK/Latin mixed text, fenced code blocks, tables, blockquotes, cover pages,
  clickable TOC, PDF bookmarks, watermarks, and page numbers. Supports multiple
  color themes (Warm Academic, Nord, GitHub Light, Solarized, etc.) and is
  battle-tested for Chinese technical reports. Use this skill whenever the user
  wants to turn a .md file into a styled PDF, generate a report PDF from markdown,
  or create a print-ready document from markdown content — especially if CJK
  characters, code blocks, or tables are involved. Also trigger when the user
  mentions "markdown to PDF", "md2pdf", "any2pdf", "md转pdf", "报告生成", or asks for a "typeset" or
  "professionally formatted" PDF from markdown source.
license: MIT
compatibility: >
  Requires Python 3.8+ and reportlab (`pip install reportlab`).
  macOS: uses Palatino, Songti SC, Menlo (pre-installed).
  Linux: uses Carlito, Liberation Serif, Droid Sans Fallback, DejaVu Sans Mono.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: markdown pdf cjk reportlab typesetting
---

# any2pdf — Markdown to Professional PDF

This skill converts any Markdown file into a publication-quality PDF using Python's
reportlab library. It was developed through extensive iteration on real Chinese
technical reports and solves several hard problems that naive MD→PDF converters
get wrong.

## When to Use

- User wants to convert `.md` → `.pdf`
- User has a markdown report/document and wants professional typesetting
- Document contains CJK characters (Chinese/Japanese/Korean) mixed with Latin text
- Document has fenced code blocks, markdown tables, or nested lists
- User wants a cover page, table of contents, or watermark in their PDF

## Quick Start

```bash
python md2pdf/scripts/md2pdf.py \
  --input report.md \
  --output report.pdf \
  --title "My Report" \
  --author "Author Name" \
  --theme warm-academic
```

All parameters except `--input` are optional — sensible defaults are applied.

## Pre-Conversion Options (MANDATORY)

**IMPORTANT: You MUST use the `AskUserQuestion` tool to ask these questions BEFORE
running the conversion. Do NOT list options as plain text — use the tool so the user
gets a proper interactive prompt. Ask all options in a SINGLE `AskUserQuestion` call.**

Use `AskUserQuestion` with the following template. The tone should be friendly and
concise — like a design assistant, not a config form:

```
开始转 PDF！先帮你确认几个选项 👇

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

━━━ 🖼 扉页图片（封面之后的全页插图） ━━━
 1) 跳过
 2) 我提供本地图片路径
 3) AI 根据内容自动生成一张

━━━ 💧 水印 ━━━
 1) 不加
 2) 自定义文字（如 "DRAFT"、"内部资料"）

━━━ 📇 封底物料（名片/二维码/品牌） ━━━
 1) 跳过
 2) 我提供图片
 3) 纯文字信息

示例回复："a, 扉页跳过, 水印:仅供学习参考, 封底图片:/path/qr.png"
直接说人话就行，不用记编号 😄
```

### Mapping User Choices to CLI Args

| Choice | CLI arg |
|--------|---------|
| Design style a-j | `--theme` with value from table below |
| Frontispiece local | `--frontispiece <path>` |
| Frontispiece AI | Generate image first, then `--frontispiece /tmp/frontispiece.png` |
| Watermark text | `--watermark "文字"` |
| Back cover image | `--banner <path>` |
| Back cover text | `--disclaimer "声明"` and/or `--copyright "© 信息"` |

### Theme Name Mapping

| Choice | `--theme` value | Inspiration |
|--------|----------------|-------------|
| a) 暖学术 | `warm-academic` | Lovstudio design system |
| b) 经典论文 | `classic-thesis` | LaTeX classicthesis |
| c) Tufte | `tufte` | Edward Tufte's books |
| d) 期刊蓝 | `ieee-journal` | IEEE journal format |
| e) 精装书 | `elegant-book` | LaTeX ElegantBook |
| f) 中国红 | `chinese-red` | Chinese formal documents |
| g) 水墨 | `ink-wash` | 水墨画 / ink wash painting |
| h) GitHub | `github-light` | GitHub Markdown style |
| i) Nord | `nord-frost` | Nord color scheme |
| j) 海洋 | `ocean-breeze` | — |

### Handling AI-Generated Frontispiece

If user chose AI generation: read the document title + first paragraphs, use an
image generation tool to create a themed illustration matching the chosen design
style, show for approval, then pass via `--frontispiece /path/to/image.png`

## Architecture

```
Markdown → Preprocess (split merged headings) → Parse (code-fence-aware) → Story (reportlab flowables) → PDF build
```

Key components:
1. **Font system**: Palatino (Latin body), Songti SC (CJK body), Menlo (code) on macOS; auto-fallback on Linux
2. **CJK wrapper**: `_font_wrap()` wraps CJK character runs in `<font>` tags for automatic font switching
3. **Mixed text renderer**: `_draw_mixed()` handles CJK/Latin mixed text on canvas (cover, headers, footers)
4. **Code block handler**: `esc_code()` preserves indentation and line breaks in reportlab Paragraphs
5. **Smart table widths**: Proportional column widths based on content length, with 18mm minimum
6. **Bookmark system**: `ChapterMark` flowable creates PDF sidebar bookmarks + named anchors
7. **Heading preprocessor**: `_preprocess_md()` splits merged headings like `# Part## Chapter` into separate lines

## Hard-Won Lessons

### CJK Characters Rendering as □

reportlab's `Paragraph` only uses the font in ParagraphStyle. If `fontName="Mono"` but
text contains Chinese, they render as □. **Fix**: Always apply `_font_wrap()` to ALL text
that might contain CJK, including code blocks.

### Code Blocks Losing Line Breaks

reportlab treats `\n` as whitespace. **Fix**: `esc_code()` converts `\n` → `<br/>` and
leading spaces → `&nbsp;`, applied BEFORE `_font_wrap()`.

### CJK/Latin Word Wrapping

Default reportlab breaks lines only at spaces, causing ugly splits like "Claude\nCode".
**Fix**: Set `wordWrap='CJK'` on body/bullet styles to allow breaks at CJK character boundaries.

### Canvas Text with CJK (Cover/Footer)

`drawString()` / `drawCentredString()` with a Latin font can't render 年/月/日 etc.
**Fix**: Use `_draw_mixed()` for ALL user-content canvas text (dates, stats, disclaimers).

## Configuration Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | Path to markdown file |
| `--output` | `output.pdf` | Output PDF path |
| `--title` | From first H1 | Document title for cover page |
| `--subtitle` | `""` | Subtitle text |
| `--author` | `""` | Author name |
| `--date` | Today | Date string |
| `--version` | `""` | Version string for cover |
| `--watermark` | `""` | Watermark text (empty = none) |
| `--theme` | `warm-academic` | Color theme name |
| `--theme-file` | `""` | Custom theme JSON file path |
| `--cover` | `true` | Generate cover page |
| `--toc` | `true` | Generate table of contents |
| `--page-size` | `A4` | Page size (A4 or Letter) |
| `--frontispiece` | `""` | Full-page image after cover |
| `--banner` | `""` | Back cover banner image |
| `--header-title` | `""` | Report title in page header |
| `--footer-left` | author | Brand/author in footer |
| `--stats-line` | `""` | Stats on cover |
| `--stats-line2` | `""` | Second stats line |
| `--edition-line` | `""` | Edition line at cover bottom |
| `--disclaimer` | `""` | Back cover disclaimer |
| `--copyright` | `""` | Back cover copyright |
| `--code-max-lines` | `30` | Max lines per code block |

## Themes

Available: `warm-academic`, `nord-frost`, `github-light`, `solarized-light`,
`paper-classic`, `ocean-breeze`.

Each theme defines: page background, ink color, accent color, faded text, border, code background, watermark tint.

## Dependencies

```bash
pip install reportlab --break-system-packages
```
