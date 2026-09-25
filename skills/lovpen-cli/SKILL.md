---
name: lovpen-cli
description: >
  调用已验证的 lovpen-cli，把 Markdown 渲染成与 Lovpen 微信公众号复制链一致的内联 HTML，或显式生成独立 HTML，并返回资源解析、文件大小和 SHA-256 证据。Use when users say “/lovpen-cli”“排版这篇 Markdown” or “render this Markdown with Lovpen”.
license: MIT
compatibility: "Python 3.9+, Node.js 20+, Chrome/Chromium 109+, and lovpen-cli 0.2.0 or a ready Lovpen agent-harness checkout."
allowed-tools:
  - Bash
  - Read
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - lovpen
    - markdown
    - html
    - cli
    - publishing
  dependencies:
    - "lovpen-cli>=0.2.0"
---

# 公众号排版 · WeChat Typesetter

把用户的 Markdown 交给 Lovpen 已验收的真实渲染链。默认生成与
`LovpenReact → 微信公众号 → extractWechatClipboardHTML` 相同契约的内联
HTML；只有用户明确要求独立网页时才输出带 `<style>` 的完整文档。

Public identifier: `lovpen-cli` intentionally matches the Lovpen product and
installed command. Do not rewrite it as `lov-lovpen-cli`; that would break the
existing `$lovpen-cli` trigger and installation paths.

## Triggers

### Activate when

- “/lovpen-cli 把这篇 Markdown 用 Typora 套装排版成微信公众号 HTML”。
- “列出 Lovpen 可用的主题、代码高亮和模板”。
- “检查 lovpen-cli 能不能用”“用 JSON 返回 Lovpen 渲染证据”。
- “Use /lovpen-cli to render this Markdown with Lovpen.”
- “Render this Markdown with the Typora Newsprint kit for WeChat.”
- “Render this Markdown as a self-contained Lovpen HTML file.”

### Do not activate when

- 用户要创建、重构或修复 CLI 本身；交给 `lov-cli-creator` 或目标项目开发流程。
- 用户要发布、上传或上架这个 Skill；交给 `lov-skill-publisher`。
- 用户要直接发布到微信公众号、知乎、小红书或 Twitter；本 Skill 只生成 HTML，平台发布由对应产品能力负责。
- 用户只要润色 Markdown 文本而不需要 Lovpen 渲染；使用写作或编辑能力。
- “给 Lovpen 项目新增一个 React 组件”属于应用开发，不触发本 Skill。

## User Profile (cross-session)

Every invocation reads the shared `user-profile/v1` contract declared in
`skill.yaml`. Resolve the CLI path, Lovpen project root, output directory,
default template kit, theme, and highlight in this order: current request,
project context, `skills.lovpen-cli.records`, shared preferences, workspace
Profile, then safe defaults.

Persist only a directly stated durable preference. For example, when the user
explicitly says to always use one theme:

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lovpen-cli \
  --path records.default_theme \
  --value '"wabi-sabi"' \
  --confirm
```

Report the saved Profile path. Never persist inferred project paths, document
contents, credentials, or tokens. Read `references/user-profile.md` for the
complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before invoking an adjacent Skill.
`lovpen-cli` owns intent routing and verified use of the existing CLI. The CLI
is the product backend, not an embedded Skill module or copied implementation.

## Workflow (MANDATORY)

Follow these steps in order.

### Step 0: Resolve the Skill, Profile, and CLI

1. Resolve `SKILL_DIR` from the active Skill context.
2. Read `skill.yaml`, `references/skill-composition.md`, and
   `references/cli-contract.md` completely.
3. Confirm `$SKILL_DIR/scripts/run_lovpen_cli.py` exists.
4. Resolve the backend through the wrapper. It accepts an explicit CLI,
   `LOVPEN_CLI`, an installed `lovpen-cli` on `PATH`, or a ready project root
   from the request, `LOVPEN_PROJECT_ROOT`, Profile, or current directory.
5. Do not store a machine-specific resolved path in this Skill source.

Manual resolution check:

```bash
python3 "$SKILL_DIR/scripts/run_lovpen_cli.py" \
  --project-root PROJECT_ROOT \
  --resolve-only
```

### Step 1: Map the user task to the narrowest command

- Runtime health and dependencies: `doctor`.
- CLI identity and readiness: `info`.
- Machine-readable command discovery: `capabilities`.
- Available themes, highlights, templates, and template kits: `resources`.
- Markdown to WeChat-copy HTML or a self-contained HTML artifact: `render`.

For `render`, resolve the input Markdown, output HTML, format, template kit or
individual resources, title, and author. The safe format default is `wechat`.
If the output is omitted, use `INPUT_STEM.lovpen.wechat.html`; use
`INPUT_STEM.lovpen.html` only for explicitly requested `standalone` output.
Without a named kit, safe resource defaults are theme `wabi-sabi`, highlight
`default`, and no HTML template.

### Step 2: Run doctor before a material render

Use global `--json` before the subcommand:

```bash
python3 "$SKILL_DIR/scripts/run_lovpen_cli.py" \
  --project-root PROJECT_ROOT \
  -- --json doctor
```

Continue only when the JSON envelope has `ok: true` and `data.ready: true`.
For WeChat format, confirm the `browser`, `clipboard_renderer`, and
`article_transforms` checks are also true. On failure, return the CLI or wrapper
`context_id`, failed check, and hint.

### Step 3: Inspect resources when selection is unresolved

Run `resources` before choosing an unverified theme, highlight, or template:

```bash
python3 "$SKILL_DIR/scripts/run_lovpen_cli.py" \
  --project-root PROJECT_ROOT \
  -- --json resources
```

Match theme names or `class_name` exactly. Match highlight and HTML template
names exactly. Match a template kit by its exact `id` or `name`; for example,
the UI's “Typora Newsprint” selection is `--template-kit typora-newsprint`, not
`--template typora`. A kit atomically resolves its theme, highlight, optional
HTML layout, and theme color. Do not combine `--template-kit` with `--theme`,
`--highlight`, or `--template`.

### Step 4: Render through the real Lovpen backend

```bash
python3 "$SKILL_DIR/scripts/run_lovpen_cli.py" \
  --project-root PROJECT_ROOT \
  -- --json render INPUT.md \
  --output OUTPUT.html \
  --format wechat \
  --template-kit typora-newsprint
```

For an explicitly requested independent document, pass `--format standalone`
and select `--theme`, `--highlight`, and optionally `--template`. Add `--title`
or `--author` only when requested or resolved from the current document
context. Use `--dry-run` when the user asks to preview the planned write. Never
reconstruct a shell command from untrusted input; pass arguments as an array
through the supplied wrapper.

### Step 5: Validate and report the artifact

For a successful render, verify all of the following from the JSON response and
filesystem:

1. `ok` and `data.written` are true, unless this was a dry run.
2. `data.renderer_source` identifies Lovpen's standalone renderer.
3. The absolute output path exists as a regular file.
4. `data.bytes` is positive and `data.sha256` is a 64-character digest.
5. `data.format`, `renderer_mode`, theme, highlight, template kit/template, and
   `disabled_preview_plugins` are reported without hiding limitations.
6. For `wechat`, `renderer_mode` is `wechat-browser-copy`, `clipboard_source`
   identifies `extractWechatClipboardHTML`, the output root is
   `<section class="lovpen-renderer">`, inline styles are present, and no
   `<style>` tag remains.
7. For `standalone`, `renderer_mode` is `standalone-headless-core`, the document
   contains its embedded `<style>`, and browser-only disabled plugins remain
   explicit.

Lead with the output file, then report resource choices and verification. Do
not blur the two contracts. WeChat format runs Lovpen's shared preview-plugin
and clipboard extractors in Chromium using the same built-in defaults and
resolved kit as the UI; standalone format intentionally remains the DOM-free
document path. If the UI has additional persisted per-document settings that
were not provided to the CLI, report that scope instead of claiming those
settings were reproduced.

## Dependencies

- Python 3.9+
- Node.js 20+
- Chrome or Chromium 109+ for WeChat format
- `lovpen-cli` 0.2.0 on `PATH`, or a Lovpen source checkout whose
  `agent-harness/lov-cli.json` status is `ready`
- Installed Lovpen workspace dependencies, including Vite, for source-checkout mode

No credentials are required for local rendering.

## Validation

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/run_lovpen_cli.py" \
  --project-root PROJECT_ROOT \
  -- --json doctor
```
