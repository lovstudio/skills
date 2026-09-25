---
name: lov-integrate-modern-screenshot
description: >
  给任意 HTML/网页集成 modern-screenshot，一键导出主体内容为 PNG，截图与屏幕渲染一致（文字不换行）、2x 适合网络传播；触发语包括“给网页加截图导出”“网页一键导出图片”“导出长图”与 "integrate screenshot export button"。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - screenshot
    - export
    - html
    - modern-screenshot
    - image
  compatibility: "Portable Agent Skills format. Python 3.8+; 端到端验证需 headless Chrome/Chromium。"
  dependencies: []
---

# 网页截图导出 · Web Capture Export

给一个静态 HTML 页面（或任意网页源文件）加一个右下角「导出图片」按钮，点击即用
modern-screenshot 把主体内容导出为 PNG。核心保证：截图与浏览器实际渲染一致
（文字不会因为容器宽度测量错误而换行），输出 2x 分辨率适合网络传播。

## Triggers

### Activate when

- 用户说“给这个网页加一个截图/导出图片按钮”。
- 用户说“网页一键导出 PNG / 长图 / 分享图”。
- 用户想把一个 HTML 报表、数据看板、落地页变成可分享的图片。
- The user asks to "add a screenshot export button" or "export this page as PNG".

### Do not activate when

- 要把内容导出为 HTML/MD/DOCX/PDF 交付包；使用 `lov-rich-export`。
- 要把 HTML 转成 PPTX；使用 `lov-html2pptx`。
- 要把 PNG 转 SVG / PDF 转 PNG；使用 `lov-png2svg` / `lov-pdf2png`。
- 只是截图当前浏览器视口（无需修改页面源码）；这不是本 Skill 的确定性集成任务。

## User Profile (cross-session)

Read `skill.yaml` on every invocation. Resolve user, brand, workspace, shared
preferences, and `skills.lov-integrate-modern-screenshot` records without copying
personal values into this portable source. Persist only direct durable user
statements through `scripts/profile_store.py`, then report the saved Profile path.
See `references/user-profile.md`.

## Skill Group Composition

Read `references/skill-composition.md` before composing adjacent capabilities.
Sibling Skills are optional artifact handoffs and never hidden dependencies.

## Required resources

Resolve `SKILL_DIR` from the active Skill context, then verify:

- `$SKILL_DIR/scripts/integrate_screenshot.py`
- `$SKILL_DIR/assets/modern-screenshot.js`
- `$SKILL_DIR/references/integration-contract.md`
- `$SKILL_DIR/references/acceptance-checklist.md`

## Workflow (MANDATORY)

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if provided; otherwise infer the installed skill directory.
- Confirm `scripts/integrate_screenshot.py` and `assets/modern-screenshot.js` exist.
- Read the shared Profile via `scripts/profile_store.py read --skill-id
  lov-integrate-modern-screenshot --pretty` when a Profile is configured.
- Do not overwrite an existing target without explicit authorization.

### Step 1: Inspect the target HTML

Read the target file and identify:

- the主体内容边界 (default: `<main>` plus its preceding top-level
  `<header>`; otherwise `<article>`; otherwise `<body>` contents);
- any CSS design tokens (`--surface`, `--ink`, `--line`, `--accent`) so the
  injected button adapts to light/dark theme; the snippet already falls back to
  neutral colors when tokens are absent;
- the download filename (from `<title>` when present).

If the intended capture region differs from the default, tell the user the exact
`--selector` (tag / `#id` / `.class`) to use.

### Step 2: Integrate the export button

```bash
python3 "$SKILL_DIR/scripts/integrate_screenshot.py" integrate <html> \
  --selector <css> --width 760 --scale 2 --title "<下载文件名>"
```

- `--width` sets the fixed capture width (default 760px; `0` follows content).
- `--scale` sets output resolution (default 2, suitable for sharing).
- Without `--out`, the source file is rewritten in place. Prefer a copy or `--out`
  when the user wants to keep the original.

The script embeds `modern-screenshot` inline (self-contained, offline), wraps the
capture region in `<div id="capture">`, and injects the floating button plus a
copyable error hint.

### Step 3: Verify end-to-end

```bash
python3 "$SKILL_DIR/scripts/integrate_screenshot.py" verify <html> \
  --scale 2 --chrome "/path/to/chrome"
```

The verifier renders the page in headless Chrome and asserts that the exported
PNG size equals `node.scrollWidth/Height × scale` exactly. A size mismatch is the
signal that the container width was measured wrong and text may reflow — fix the
`--width` or `--selector` and re-run.

Apply every item in `references/acceptance-checklist.md`. Report the real input,
the exact command, the `OK out=WxH …` result, and the output path. Do not invent
a passing verification or a score.

### Step 4: Report and record

Report the output path, selector, width, scale, and verification result. Record a
real case in `cases/cases.json` only when a genuine integration occurred; do not
manufacture one.

## Output contract

Return:

- the target HTML path and whether it was rewritten in place or to a new file;
- the capture selector, fixed width, and scale used;
- the headless-Chrome verification result (`OK out=… node=… expect=…`);
- any remaining gaps (e.g. web-font embedding, animated content, cross-origin media).

## Dependencies

- Runtime: Python 3.8+ (stdlib only — no PyYAML needed for the CLI itself).
- Verification: headless Chrome/Chromium (`--headless=new --dump-dom`).
- The target page needs no build step; `modern-screenshot` is embedded inline.
