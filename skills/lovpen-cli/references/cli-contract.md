# lovpen-cli Contract

## Backend identity

The supported backend is `lovpen-cli` version 0.2.0 with a `lov-cli/v1`
contract. It calls Lovpen's maintained standalone renderer and, for WeChat
format, the same shared browser clipboard extractor used by the UI.

The Skill may use either:

1. an installed `lovpen-cli` executable; or
2. a Lovpen source checkout whose `agent-harness/lov-cli.json` has status
   `ready` and whose `agent-harness/src/lovpen_cli` module is present.

The supplied resolver never evaluates a shell command string.

## Global contract

- `--help` and `--version` expose usage and version.
- Put global `--json` before the subcommand.
- `--project-root PATH` selects a specific Lovpen source checkout.
- Success exits 0 with one JSON object containing `ok`, `command`, `data`, and
  `meta.duration_ms`.
- Failure exits nonzero with `error.code`, `error.message`, `context_id`, and
  an actionable `hint`.

Exit meanings are stable:

- 0: success and verified postconditions;
- 2: usage or input error;
- 3: missing runtime or project dependency;
- 4: backend or postcondition failure;
- 5: unsafe or conflicting state.

## Commands

### doctor

Checks Node.js, Chrome/Chromium 109+, the Lovpen project, Vite, standalone
renderer, shared clipboard/preview transforms, themes, highlights, and
templates. Continue only when `data.ready` is true.

### info

Returns command, version, status, project root, and backend identity. A complete
local CLI reports status `ready`.

### capabilities

Returns built-in and domain command schemas for agent discovery.

### resources

Returns real `themes`, `highlights`, `templates`, and `template_kits` catalogs.
Theme selection accepts a listed display name or `class_name`; other resource
names match exactly. Template-kit entries include their resolved theme,
highlight, HTML layout, and theme color.

### render

Required inputs:

- positional UTF-8 Markdown input;
- `--output` or `-o` HTML path.

Optional inputs:

- `--theme`, default `wabi-sabi`;
- `--highlight`, default `default`;
- `--template`;
- `--template-kit`, exact kit id or name;
- `--format standalone|wechat`, default `standalone` at the CLI layer;
- `--title`;
- `--author`;
- `--dry-run`.

A template kit cannot be combined with individual theme, highlight, or template
flags. A successful material render reports `written`, absolute `output`,
positive `bytes`, SHA-256, format, theme, highlight, template kit/template,
`renderer_source`, `renderer_mode`, `clipboard_source`, browser, and
`disabled_preview_plugins`. It writes atomically and reads the file back before
success.

## Render-mode boundary

`wechat` runs `applyPreviewRenderPlugins` and
`extractWechatClipboardHTML` from `packages/shared/src` inside Chromium. It
emits the inline-styled `<section>` produced by the UI's 微信公众号 copy contract
and removes `<style>`, script, link stylesheet, and Lovpen action elements.

`standalone` covers Markdown parsing, syntax highlighting, Handlebars templates,
theme CSS, front matter, and final render CSS without a browser. Browser-only
preview/export plugins are disabled and named in each standalone response:

- code block image scaling;
- cover injection;
- image management;
- first-heading removal;
- heading numbering;
- generated table of contents;
- link footnotes.

WeChat parity assumes the same Markdown, resolved built-in resource kit, Lovpen
default settings, and compatible Chromium rendering engine. Additional UI
settings not supplied to the CLI remain outside that claim.
