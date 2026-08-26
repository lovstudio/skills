---
name: lov-app-generator
description: >
  Use when the user asks for "App生成器", "生成 Web App", "生成 Tauri App",
  "生成原生 macOS App", "Finder Quick Action", "只创建 web", or to standardize
  an existing app with branding, CI/CD, native integration, and Lovinsp where applicable.
license: MIT
compatibility: >
  Requires Python 3.8+ for the project audit helper. Designed for React,
  TypeScript, Vite, Next.js, optional Tauri, native macOS apps and Action Extensions,
  shadcn/ui, TanStack Query, GitHub Actions, web deploys, and Skill Publisher
  Configurable Academic branded apps. Every generated or standardized frontend app
  must run `lov-integrate-lovinsp`. New apps must generate a target-specific logo
  through `lov-gen-logo`; Tauri apps must run the Tauri icon pipeline from that logo.
metadata:
  author: contributors
  version: "0.5.0"
  tags:
    - skill-publisher
    - app-generator
    - web
    - vite
    - nextjs
    - tauri
    - react
    - shadcn
    - tanstack-query
    - cicd
    - updater
    - lovinsp
---

# app-generator — Skill Publisher App 生成器

Use this skill to create or upgrade a Skill Publisher-grade app. Choose the app type
from the brief instead of forcing desktop packaging: use web-only when the
workflow is browser-native, use Tauri for a web-rendered desktop product, and use a
native macOS host when an App Extension is the product's primary capability. Common
stacks are React + TypeScript + Vite, Next.js, Tauri + React, or Swift/SwiftUI +
AppKit extensions, with Skill Publisher brand assets, CI/CD or deploy wiring, and
lovinsp click-to-code support for browser-rendered UI.

## Default Integration Invariant

Run the `lov-integrate-lovinsp` skill for every app handled by this workflow. Treat
Lovinsp as a default development capability, not an optional feature selected
from the brief.

- Invoke `lov-integrate-lovinsp` after the frontend scaffold and build config exist.
- Re-run it for existing apps to update Lovinsp or migrate `code-inspector`.
- Preserve its idempotent behavior; repeated app-generator runs must stay safe.
- Require the project audit to pass dependency, configuration, migration, and
  plugin-order checks before completion.
- Verify the served Vite module contains `lovinsp-component` or `[lovinsp v...]`.

Skip this invariant only when the requested deliverable has no browser-rendered UI
and therefore falls outside the app-generation paths described below.

## Triggers

### Activate when

- The user asks to generate a new Skill Publisher app, web app, PWA, desktop app, or
  cross-platform app.
- The user asks for a native macOS app, Finder right-click action, Finder Quick
  Action, Action Extension, or another packaged macOS integration.
- The user has an existing frontend/Tauri project and wants it brought up to
  Skill Publisher app standards.
- The user mentions web-only, Vite, Next.js, PWA, Tauri, shadcn, React Query /
  TanStack Query, deploy, auto update, CI/CD, app logo, Skill Publisher logo, Warm
  Academic UI, or lovinsp as part of app setup.
- The project is a Skill Publisher, Lovpen, Lovcode, Lovmind, Lovshot, Lovsider,
  Lovsigil, or Lovtarot app.

### Do not activate when

- The user asks only for a standalone logo, document, presentation, or static media
  asset without an application shell.
- The request is limited to diagnosing an existing app and does not include creating
  or standardizing its app architecture.
- The deliverable is a backend-only service, CLI, library, or Skill package with no
  browser-rendered application UI.

## Workflow (MANDATORY)

Resolve `SKILL_DIR` from the installed skill context before running helpers.
For manual execution, set it to the directory containing this `SKILL.md`.

**You MUST follow these steps in order:**

### Step 1: Clarify the App Brief

Collect only the missing fields. Use conversation context first. Prefer
`AskUserQuestion` for interactive choices; if that tool is unavailable, ask
short direct questions and continue once the answer is clear.

Required fields:

| Field | Default | Notes |
|---|---|---|
| App name | Ask user | Product/display name, e.g. `Lovshot` |
| Project slug | Derived from app name | Lowercase kebab-case |
| Brand scope | `Skill Publisher` | Ask if ambiguous between Skill Publisher / brand-logo / personal brand |
| Target mode | `new app` | `new app` or `upgrade existing app` |
| App type | Case-by-case | `web-only`, `PWA`, `Tauri desktop`, or another fit from the brief |
| Platforms | Case-by-case | Web browser/mobile responsive unless native desktop is justified |
| Native integration | `none` | Record the exact surface: `Finder Quick Action`, `Services`, `Share Extension`, etc. |
| Core screens | Ask user | 2-5 concrete screens or workflows |
| Backend/API | Ask user if needed | REST, Supabase, local files, Tauri commands, static data, etc. |
| Distribution | Case-by-case | Web deploy for web-only; GitHub Releases + updater for Tauri |

If the user asks for a real implementation and enough information is present,
make conservative assumptions and proceed.

Suggested options to collect interactively:

| Question | Recommended choice |
|---|---|
| Target mode | `New app` |
| App type | `Decide from requirements` |
| Brand scope | `Skill Publisher` |
| UI baseline | `Configurable Academic + shadcn/ui` |
| Data layer | `TanStack Query when server state exists` |
| Release channel | `Web deploy or GitHub Releases based on app type` |

### Step 2: Read Local Context

Before changing files, inspect the target project:

```bash
pwd
find .. -name AGENTS.md -print
find .. -name CLAUDE.md -print
ls
find . -maxdepth 2 -type f \( -name package.json -o -name vite.config.ts -o -name next.config.ts -o -name next.config.js -o -name tauri.conf.json -o -name tauri.conf.json5 -o -name Cargo.toml \) -print
```

Honor any project-level instructions. If the target lives under a symlinked
workspace, follow that project's own AGENTS.md / CLAUDE.md.

### Step 3: Run the Skill Publisher App Audit

Run the helper from the target project root:

```bash
python3 "$SKILL_DIR/scripts/audit_app_project.py" --root . --app-type auto --format markdown
```

Use the output as the implementation checklist. For new projects, decide the
app type first and pass `--app-type web` or `--app-type tauri`; the audit will
mostly report missing pieces, which is expected.

### Step 4: Choose the Implementation Path

#### App Type Decision

Pick the smallest app type that genuinely fits the brief:

- **Web-only app**: default when the product is a browser workflow, SaaS/admin
  surface, content or media tool, public site with logged-in tools, or anything
  that can deploy cleanly to Vercel/Netlify/Cloudflare/GitHub Pages.
- **PWA**: use when the app is still web-first but benefits from installability,
  offline shell, push notifications, or mobile home-screen usage.
- **Tauri desktop app**: use when native desktop value is explicit: local file
  access beyond browser capabilities, tray/menu/global shortcuts, long-running
  background tasks, native OS integration, offline-first packaged use, or
  GitHub Releases distribution with auto update.
- **Native macOS app**: use when a macOS App Extension is the primary deliverable,
  including Finder Quick Actions that must be embedded, signed, enabled, and verified
  as part of the containing app. Do not force a browser-rendered shell onto an
  extension-first utility.
- **Framework choice**: prefer Vite React for app-like single-page workflows,
  Next.js for SEO/SSR/content routing/API routes, and static HTML only for very
  small one-off deliverables.

Do not add Tauri simply because this skill historically defaulted to Tauri.
If the user says "只创建 web" or the requirements do not need native desktop
capabilities, create a web app.

#### Native Surface Decision

Treat the requested macOS surface as an acceptance criterion, not an implementation
detail:

- "Finder 右键菜单" or "Finder context menu" defaults to the **Quick Actions**
  submenu when the command processes selected files or folders.
- Services are only for explicit cross-app selection processing or Services shortcuts;
  `NSServices` and Service-only workflows never satisfy a Quick Action request.
- Classify the surface by the Finder preview flag and runtime placement, not the
  `com.apple.services` identifier or `Library/Services` directory name.
- Finder Sync is only for synchronization/status behavior in monitored directories.

When the brief includes a Finder Quick Action, read
`references/macos-finder-quick-actions.md` completely before scaffolding or editing.

#### New Web App

For an app-like browser workflow, default to Vite + React + TypeScript:

```bash
pnpm create vite@latest <project-slug> -- --template react-ts
cd <project-slug>
pnpm add @tanstack/react-query lucide-react
pnpm add -D typescript
```

For SEO-heavy, public, content-routed, or SSR/API-route requirements, use
Next.js instead and keep the same Skill Publisher layers:

```bash
pnpm create next-app@latest <project-slug> --ts --tailwind --eslint --app --src-dir
cd <project-slug>
pnpm add @tanstack/react-query lucide-react
```

Then apply the Skill Publisher layers in this order:

1. Project identity: package name, app title, README, and app-specific
   CLAUDE.md / AGENTS.md.
2. Configurable Academic UI: shadcn/ui, semantic tokens, typography, and layout.
3. Server state: TanStack Query provider and query/mutation helpers when the
   app has server state; avoid unnecessary TanStack Query for purely local
   static tools.
4. Brand assets: generate a target-specific app logo with
   `lov-gen-logo`, publish the chosen version into `assets/` and
   `public/`, and generate favicons / PWA icons if needed.
5. Lovinsp: invoke `lov-integrate-lovinsp` and verify click-to-code integration.
6. CI/CD and deploy: typecheck, lint/build where available, plus the selected
   web deploy target or documented manual deploy path.
7. Verification: typecheck, build, dev server, and browser screenshot or
   interaction check where practical.

#### New Tauri App

Use this path only when the app type decision requires native desktop
capabilities or desktop distribution. Default stack:

```bash
pnpm create vite@latest <project-slug> -- --template react-ts
cd <project-slug>
pnpm add @tauri-apps/api @tanstack/react-query lucide-react
pnpm add -D @tauri-apps/cli typescript
pnpm tauri init
```

Then apply the Skill Publisher layers in this order:

1. Project identity: package name, app title, bundle identifier, README, and
   app-specific CLAUDE.md.
2. Configurable Academic UI: shadcn/ui, semantic tokens, typography, and layout.
3. Server state: TanStack Query provider, query keys, and Tauri invoke wrappers.
4. Brand assets: generate a target-specific app logo with
   `lov-gen-logo`, publish the chosen version into `assets/` and
   `public/`, prepare a macOS-safe padded icon source, then run the Tauri icon
   pipeline from that generated logo.
5. Lovinsp: invoke `lov-integrate-lovinsp` and verify click-to-code integration.
6. CI/CD: typecheck, lint/build where available, Tauri release workflow.
7. Auto update: Tauri updater plugin, signing keys/env placeholders, release
   endpoint wiring.
8. Verification: typecheck, build, and app launch where practical.

If the Tauri product also requires a Finder Quick Action, treat it as a hybrid macOS
package and follow the native reference; prefer a native Swift/SwiftUI containing app
when the extension is the product's main value.

#### Finder Quick Action

Follow `references/macos-finder-quick-actions.md`, run the audit with
`--native-integration finder-quick-action`, and complete its packaged/runtime checks
before claiming completion.

#### Upgrade Existing App

Do not rebuild the project from scratch. Patch the smallest surface needed:

1. Determine whether the existing app should remain web-only, become a PWA, or
   stay/become Tauri before applying the audit checklist.
2. Keep the existing package manager, router, folder layout, aliases, and style
   conventions unless they conflict with Skill Publisher requirements.
3. Add missing Skill Publisher layers from the audit; do not add Tauri to a web-only
   app unless the brief requires native desktop capabilities.
4. Preserve the requested native surface. A Quick Action remains a Quick Action after
   an upgrade; do not silently replace it with a Service because that path is easier.
5. Run `lov-integrate-lovinsp` to install/update Lovinsp and migrate any supported
   `code-inspector` integration.
6. Preserve user code and unrelated changes.
7. Prefer incremental commits/checkpoints when the app is already substantial.

### Step 5: Apply Brand and UI Standards

New apps must not use the canonical Skill Publisher logo as the app/product icon.
After the project identity and README describe the target clearly, invoke the
`lov-gen-logo` workflow from the new app root:

1. Generate `assets/logo-drafts/v1-*.png` and `.svg` based on what the app does,
   not a literal reading of its name.
2. Publish the chosen draft to `assets/logo.png`, `assets/logo.svg`,
   `public/logo.png`, and `public/logo.svg`.
3. For web-only apps, generate favicons and PWA icons from the target-specific
   logo as needed; do not run Tauri icon tooling.
4. For Tauri apps, before feeding the generated logo into the Tauri icon
   pipeline, ensure the icon source has transparent safe area. Do not use a
   512x512 edge-to-edge filled icon as the macOS app icon source; it appears
   oversized in Dock, Launchpad, and Finder. Prefer roughly 40-56px transparent
   padding on a 512x512 canvas, or a content bounding box around 80-85% of the
   canvas.
5. Use that padded generated logo as the source for
   `lov-install-tauri-logo` and any favicon/tray-icon generation.

For upgrades, keep an existing product logo unless the user asks to refresh it;
if the app has no logo, use `lov-gen-logo` before generating icons.

Resolve canonical assets without assuming a private machine layout:

1. Explicit paths supplied by the user.
2. `SKILL_PROFILE_PATH` and `SKILL_DESIGN_GUIDE`.
3. `${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}`.
4. Ask once when a required asset is still missing.

See `references/user-config.md` for the portable configuration contract.

Rules:

- Treat the canonical Skill Publisher logo as brand reference or fallback only, not as
  the default app icon for new apps.
- For Tauri/macOS icons, verify the generated app icon is visually aligned with
  normal macOS app icons. If ImageMagick is available, a quick sanity check is:
  `magick src-tauri/icons/icon.png -alpha extract -trim -format '%wx%h%O\n' info:`;
  for a 512x512 source, content around `400x400` to `440x440` with positive
  offsets is usually safer than `512x512+0+0`.
- Use semantic Tailwind classes such as `bg-background`, `text-foreground`,
  `bg-primary`, `border-border`; do not hard-code brand hex values in UI
  components.
- Keep the UI operational and app-like. Do not create a marketing landing page
  when the user asked for an app.
- Use shadcn/ui controls, lucide icons, compact panels, predictable navigation,
  and no nested cards.
- First screen should be the real product workflow.

When shadcn/ui is needed, use the existing `lov-install-shadcn-ui` skill
as the detailed reference. When TanStack Query is needed, use
`lov-install-tanstack-query`. For Tauri app icons, use
`lov-install-tauri-logo`; for new apps, run `lov-gen-logo` first
and feed the generated logo into the relevant favicon/PWA/Tauri icon pipeline.

### Step 6: Tauri App Baseline

Only for Tauri desktop apps, check these areas:

| Area | Expected |
|---|---|
| `src-tauri/tauri.conf.*` | app title, identifier, windows, bundle metadata |
| `src-tauri/Cargo.toml` | Tauri plugins, app metadata, updater if enabled |
| Rust commands | typed command boundary, no broad stringly APIs where avoidable |
| Frontend API | `invoke()` wrapped through query/mutation helpers for server state |
| Filesystem/native APIs | least permission needed in Tauri capabilities |
| Native extensions | when requested, signed `.appex` embedded in `Contents/PlugIns`; never Service-only fallback |
| Icons | generated through Tauri icon pipeline from the target-specific logo produced by `lov-gen-logo` |
| Dev server | stable project port, preferably via `lov-project-port` |

### Step 7: CI/CD, Deploy, and Auto Update

Default GitHub Actions surface for web-only apps:

- `check.yml`: install, typecheck, lint/build if present.
- Deploy wiring for the selected target: Vercel, Netlify, Cloudflare Pages,
  GitHub Pages, self-hosted static output, or a clearly documented manual
  deploy path.
- Environment variable placeholders only when the app actually needs them.

Default GitHub Actions surface for Tauri apps:

- `check.yml`: install, typecheck, lint/build if present.
- `release.yml`: Tauri build for target platforms, draft or publish GitHub
  Release, attach artifacts.
- Tauri updater wiring: plugin dependency, updater config, signing key env
  placeholders, and documented release process.
- For Tauri v2, `plugins.updater.pubkey` is required at runtime. Do not leave
  it out even during early scaffolding: a missing `pubkey` causes the app to
  panic during updater plugin initialization. Use a clear placeholder such as
  `PLACEHOLDER_REPLACE_WITH_TAURI_SIGNER_PUBLIC_KEY` until the real public key
  is generated with `pnpm tauri signer generate`.

Do not invent secrets. Use placeholder names and document where the user must
set them:

- `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
- platform signing/notarization secrets as required by the target app

### Step 8: Lovinsp

Invoke the existing `lov-integrate-lovinsp` workflow for every browser-rendered app.
Do not replace that workflow with a handwritten dependency-only installation: it
also performs version checks, idempotent configuration, and `code-inspector`
migration.

Completion requires all of the following:

- `lovinsp` exists in project dependencies.
- The supported build configuration registers `lovinspPlugin`.
- Vite registers `lovinspPlugin({ bundler: "vite" })` before the framework plugin.
- No supported legacy `code-inspector` dependency or configuration remains.
- A development-server readback proves the transform is active when practical.

For Vite apps, confirm the Vite config imports and registers
`lovinspPlugin({ bundler: "vite" })` before the framework plugin, not merely
that the package is installed. In dev mode, verify the served module contains
`lovinsp-component` or `[lovinsp v...]`:

```bash
curl -s http://127.0.0.1:<port>/src/main.tsx | rg "lovinsp-component|lovinsp v"
```

For web-only apps, start the dev server and provide the local URL when the user
needs to try the app:

```bash
pnpm dev --host 127.0.0.1
```

For Tauri apps, prefer launching dev mode through a persistent session when the
user wants to keep it running after the turn:

```bash
tmux new-session -d -s <slug>-dev -c "$PWD" 'pnpm tauri dev'
tmux capture-pane -pt <slug>-dev -S -120
```

### Step 9: Verification

Run the lightest reliable checks that the target repo supports:

```bash
pnpm exec tsc --noEmit --pretty false
pnpm build
# Tauri only:
pnpm tauri build --debug
```

Adjust for npm/yarn/bun and local instructions. If a dev server is needed to
verify frontend behavior, start it and give the user the local URL.

For UI changes, use browser or screenshot verification when practical. For
Tauri-native behavior, report what was and was not verified.

For Finder Quick Actions, source/build success is insufficient; complete every packaged
and runtime acceptance check in `references/macos-finder-quick-actions.md`.

## User Configuration

If local paths differ, prefer these environment variables rather than
hard-coding personal paths:

| Variable | Default / Usage |
|---|---|
| `SKILL_APP_GENERATOR_SKILL_DIR` | Installed `lov-app-generator` skill directory |
| `SKILL_DESIGN_GUIDE` | Configurable Academic design guide path |
| `SKILL_PROFILE_PATH` | Skill Publisher brand asset root or profile |

## CLI Reference

Run `python3 "$SKILL_DIR/scripts/audit_app_project.py" --help`; Finder Quick Action
audits must pass `--native-integration finder-quick-action` explicitly.

## Dependencies

```bash
python3 "$SKILL_DIR/scripts/audit_app_project.py" --help
```

No Python packages are required.

## Final Response Checklist

Report:

- App path and stack chosen.
- App type decision: web-only / PWA / Tauri, and why that fit the brief.
- Native surface decision and evidence, including Quick Actions versus Services when relevant.
- Skill Publisher layers added or confirmed: brand, UI, data layer, lovinsp, CI/CD,
  deploy/release, and updater only when applicable.
- `lov-integrate-lovinsp` result, including installation/update/migration status and
  runtime readback evidence.
- Commands/checks run and their result.
- Any remaining secrets, signing steps, or manual app-store/release actions.

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
