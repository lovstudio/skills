---
name: lov-pdf2png
category: Document Conversion
tagline: "PDF → single vertically concatenated PNG. Uses macOS CoreGraphics, ~20x faster than pdftoppm."
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
  author: contributors
  version: "0.2.0"
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

Locate the PDF file(s) the user wants to convert. If multiple PDFs or output
location choices are ambiguous, use `AskUserQuestion` to confirm the path(s)
before running conversion.

### Step 2: Execute

```bash
bash lov-pdf2png/scripts/pdf2png.sh /path/to/file.pdf
```

Output: `/path/to/file.png` (same directory, same name, `.png` extension).

For multiple files:

```bash
bash lov-pdf2png/scripts/pdf2png.sh file1.pdf file2.pdf file3.pdf
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
conversion. See [skill-publisher/mac-pdf2png](https://example.com/skills/mac-pdf2png)
for the Automator workflow.

## Dependencies

```bash
pip install pyobjc-framework-Quartz --break-system-packages
```

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
