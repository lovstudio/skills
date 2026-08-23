---
name: lov-fill-form
category: Office Automation
tagline: "Fill Word form templates (.docx). Auto-detects table fields, CJK font support."
description: >
  Fill in Word document form templates (.docx) with user-provided data.
  Reads a template containing tables with label→value cell pairs, detects
  all fillable fields, and outputs a completed document. Handles CJK/Latin
  mixed text with proper font switching. Use this skill when the user wants
  to fill in a form template, complete an application form, populate a Word
  table form, or automate document filling. Also trigger when the user
  mentions "填表", "填写表格", "fill form", "fill template", "表格填写",
  "申请表", "登记表", or has a .docx template with blank fields to fill.
license: MIT
compatibility: >
  Requires Python 3.8+ and python-docx (`pip install python-docx`).
  Cross-platform: macOS, Windows, Linux.
  Input must be .docx (recommended) or .doc (auto-converted via textutil on macOS,
  but table structure may be lost — use .docx when possible).
metadata:
  author: contributors
  version: "1.2.0"
  tags: form fill template docx word table cjk
---

# fill-form — Fill Word Form Templates

This skill fills in Word document form templates (.docx) with user-provided data.
It detects table-based form fields (label in one cell, value in the adjacent cell)
and populates them automatically.

## When to Use

- User has a `.docx` form template with blank fields to fill
- User wants to fill in an application form, registration form, etc.
- Document uses Word tables for form layout (label | value cell pairs)
- User mentions 填表, 申请表, 登记表, or wants to automate form filling

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: Scan the template

Discover all fillable fields:

```bash
python lov-fill-form/scripts/fill_form.py --template <path> --scan
```

### Step 2: Pre-fill from known context

Before asking the user, try to fill as many fields as possible from:
1. **User memory** — name, title, organization, etc.
2. **Context files** — if the user provides reference documents (e.g. STARTER-PROMPT.md,
   project docs), extract relevant info to fill content-heavy fields
3. **Conversation context** — anything already mentioned

For content-heavy fields (e.g. "主要内容/简介/摘要"), actively compose the content
by synthesizing from context files, user's known expertise, and the topic/title.

### Step 3: Ask only what you don't know

**Use `AskUserQuestion` to collect ONLY the fields you cannot fill from context.**

- Group fields into a single question
- If ALL fields are unknown, list them all
- If the user says some fields can be left blank (e.g. "其他朋友会帮我填"),
  respect that and leave those empty
- Do NOT force the user to provide every field

### Step 4: Fill and save

Write a JSON data file (avoids shell escaping issues with long text), then run:

```bash
python lov-fill-form/scripts/fill_form.py \
  --template <path> \
  --data-file /tmp/form_data.json
```

**Output path rules:**
- Default: `<template_dir>/<name>_filled.docx` (same directory as the template)
- If the template is in a temp directory or system path, save to user's document
  directory or ask the user where to save
- Use `--output` to override explicitly

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--template` | (required) | Path to template .doc/.docx file |
| `--output` | `<template_dir>/<name>_filled.docx` | Output .docx path |
| `--scan` | false | List all detected form fields |
| `--data` | `""` | JSON string with field→value mapping |
| `--data-file` | `""` | Path to JSON file with field→value mapping |
| `--font` | Platform CJK serif | Font name for filled text |
| `--font-size` | `11` | Font size in points |

## How Field Detection Works

1. **Table-based** (primary): Scans all tables for rows with label→value cell pairs.
   A label cell contains short text (CJK or Latin); the adjacent cell is the value field.
2. **Merged rows**: Detects full-width merged cells with "Label：" pattern as large text areas.
3. **Paragraph fallback**: If no tables found, detects "Label：value" patterns in paragraphs.

## Limitations

- `.doc` files are auto-converted to `.docx` via macOS `textutil`, which **loses table structure**.
  For best results, use `.docx` templates directly. If you only have `.doc`, convert with
  LibreOffice first: `libreoffice --headless --convert-to docx file.doc`
- Fields are matched by normalized label text (whitespace removed). If a label contains
  unusual formatting, the match may fail — use `--scan` to verify detection.

## Dependencies

```bash
python3 -m pip install python-docx
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
