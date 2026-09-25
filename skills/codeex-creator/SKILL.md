---
name: lov-codeex-creator
description: >
  为 Codeex 创建、验证和迭代本地运行时插件，覆盖 renderer、launch、control hooks、原生 UI 复用、分层重载与原子安装卸载。Use when users say“开发 Codeex 插件”or “create a Codeex plugin”.
license: MIT
compatibility: >
  Python 3.8+, Node.js 24+, PyYAML 6+ for self-validation, and a Codeex
  repository exposing the current local runtime plugin contract.
metadata:
  author: contributors
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - codeex
    - plugin-development
    - atomic-lifecycle
    - electron
    - local-first
  dependencies:
    - "PyYAML 6+ (self-validation only)"
---

# Codeex 插件工坊 · Codeex Plugin Studio

Deliver one self-contained Codeex runtime plugin whose source, permissions,
hooks, desired install state, active runtime state, and rollback path are all
auditable. Keep every plugin independently installable and uninstallable; never
patch another plugin to make the new one work.

## Triggers

### Activate when

- 用户说“开发一个 Codeex 插件”“把这个能力做成 Codeex plugin”或“原子安装/卸载这个插件”。
- 用户要新增或修改 `plugins/<plugin-id>/plugin.json`、`transformWebview`、`beforeLaunch`、`handleControlRequest` 或 Codeex 插件权限。
- The user asks to “create a Codeex plugin”, “add a Codeex runtime hook”, or “make this Codeex feature independently installable”.

### Do not activate when

- 用户要创建 Codex marketplace 的 `.codex-plugin/plugin.json`、Skill、MCP 或 App；使用 Codex `plugin-creator`，不要套用 Codeex 运行时契约。
- 用户只要把 Lovinsp 接入普通前端项目；使用 `lov-integrate-lovinsp`。
- 用户只要修复 Electron/Tauri 的通用 relaunch 行为，而没有 Codeex 插件交付物；使用 `lov-electron-app-relaunch`。
- 用户只要求启用或停用一个已经存在的插件，且不涉及开发或验证；直接使用 Codeex 插件中心或项目 CLI。

## Runtime Context and Profile

Read `skill.yaml` and resolve the Codeex repository in this order:

1. The current request or an explicit `--project-root`.
2. Current project context when it satisfies the Codeex contract.
3. `CODEEX_PROJECT_ROOT`.
4. `workspace.codeex_root` or `skills.lov-codeex-creator.records.codeex_root`
   from the shared Profile.
5. The current directory when it passes the contract check.

Do not save an inferred path. If the user explicitly says a Codeex root should
be reused in future sessions, persist it with `scripts/profile_store.py record
--skill-id lov-codeex-creator --path records.codeex_root --value <json-string>
--confirm` and report the canonical Profile path without echoing private data.

Read `references/skill-composition.md` before invoking adjacent capabilities.
External Skills are optional artifact handoffs, never runtime dependencies.

Proceed without a question when the repository, plugin boundary, and safe
verification path are discoverable. Use AskUserQuestion at most once when a
material choice cannot be recovered locally, especially authorization to
restart the active Codeex instance or a destructive source-removal request.

## Codeex Plugin Contract

Before editing, read these references completely:

- `references/plugin-contract.md` for manifests, hooks, and authoritative Codeex files.
- `references/atomic-lifecycle.md` for source, desired-state, runtime, and rollback semantics.
- `references/verification.md` for the risk-based evidence matrix.
- `references/development-loop.md` for native UI reuse, reload boundaries, and
  packaged-runtime readback.

Re-audit the target repository when its contract files differ from the
reference. Current source code is authoritative; this Skill must not freeze a
stale private API.

## Workflow (MANDATORY)

### Step 1: Define the plugin boundary

Record:

- one plugin ID in lower-case kebab-case;
- the user-visible outcome and one independently removable capability;
- whether it needs `transformWebview`, `beforeLaunch`, `handleControlRequest`,
  or a combination;
- every permission and why it is necessary;
- whether activation requires a renderer rebuild, a managed runtime restart,
  a launcher/control-service reload, or a combination;
- a rollback that leaves the currently running Codeex usable.

Reject a design that reaches into another plugin directory, mutates shared
state outside declared hooks, or requires deleting user data during uninstall.

### Step 2: Inspect the live contract

Verify the repository contains:

```text
plugins/catalog.mjs
plugins/state.mjs
scripts/plugins-cli.mjs
scripts/build-webview.mjs
scripts/start.mjs
scripts/control-server.mjs
scripts/launcher-server.mjs
scripts/verify.mjs
```

Inspect the current hook call sites and context objects. Search existing plugins
for the closest contract example, but do not copy feature-specific permissions,
ports, paths, or lifecycle behavior.

### Step 3: Scaffold or update the source

For a new plugin, use the staged creator:

```bash
python3 "$SKILL_DIR/scripts/codeex_plugin.py" scaffold <plugin-id> \
  --project-root "$CODEEX_ROOT" \
  --name "<display name>" \
  --description "<concrete user-visible outcome>" \
  --hook webview \
  --control-route
```

Infer `--hook webview`, `before-launch`, or `both` from the requested behavior.
Use `--hook control` for a control-only plugin, or add `--control-route` when a
webview or launch plugin also owns authenticated local API routes.
Use repeated `--permission "Label:Detail"` only for capabilities the plugin
actually exercises. The scaffold is created beside the final target and
renamed into place only after validation; an occupied target is rejected.

For an existing plugin, edit only its own directory plus focused shared tests
or contract code that is genuinely required. Never overwrite its directory
with the scaffold command.

### Step 4: Implement through declared hooks

- `transformWebview(context)` may change only the staged renderer tree passed by
  Codeex. It must return small diagnostics and must not edit the prepared
  upstream source or a running app bundle directly.
- `beforeLaunch(context)` may return an `env` overlay. Preserve the input
  environment, keep secrets out of logs, and make external process ownership
  explicit.
- `handleControlRequest(context)` receives an already authenticated local
  request, URL, Codex home, and official CLI path. Return `null` for routes the
  plugin does not own; bound request bodies and return `{ status, body }` for
  handled routes.
- Validate entry paths remain inside the plugin directory.
- Put user-facing permissions in `plugin.json`; absence from the UI is not
  permission minimization.
- Keep install/uninstall free of source deletion. Source removal is a separate,
  explicit destructive maintenance action.
- For official composer or sidebar UI, inspect the adjacent native DOM first.
  Reuse the real trigger classes, icons, elevated surface, and spacing when
  available; do not approximate an existing icon by eye. Mount idempotently,
  remove owned nodes on dispose, and anchor to stable semantic attributes.

### Step 5: Select the reload boundary

Classify every changed file before live verification:

- renderer transform or injected runtime: staged webview rebuild plus runtime
  restart, or an isolated smoke instance;
- `beforeLaunch`: a new managed runtime process;
- `handleControlRequest` or a transitive module it imports: launcher/control
  service reload before API readback; restarting only Electron is insufficient;
- launcher or host contract code: full wrapper/service reload followed by the
  relevant runtime verification.

Use `references/development-loop.md` for the exact loop. Resolve the current
owner PID and port before stopping anything; an `EADDRINUSE` error is evidence
of an existing service, not permission to launch duplicates.

### Step 6: Validate before changing desired state

```bash
python3 "$SKILL_DIR/scripts/codeex_plugin.py" validate <plugin-id> \
  --project-root "$CODEEX_ROOT"
pnpm check
```

Add focused tests for plugin logic. A webview transform needs a staged-bundle
assertion; a launch hook needs environment/process tests. Do not treat manifest
strings or a successful TypeScript parse as runtime proof.

Before handoff, prove the plugin is discoverable in the Codeex management UI.
Its card must render from the authoritative catalog with the correct desired and
active states, and the UI install/uninstall actions must round-trip through the
authenticated control API. A working CLI alone is not a manageable plugin.

### Step 7: Install or uninstall atomically

Use the wrapper, which delegates desired-state mutation to Codeex instead of
hand-editing JSON:

```bash
python3 "$SKILL_DIR/scripts/codeex_plugin.py" install <plugin-id> \
  --project-root "$CODEEX_ROOT"

python3 "$SKILL_DIR/scripts/codeex_plugin.py" uninstall <plugin-id> \
  --project-root "$CODEEX_ROOT"
```

The state transition is idempotent and file-atomic, but it is only the desired
state. Report `restart required` until the rebuilt runtime confirms the same
active plugin set. Do not restart the user's active Codeex instance unless the
request authorizes it; prefer `pnpm smoke` for isolated verification.

If activation fails, keep the old running runtime, reverse the desired-state
transition, and verify the state file again. Do not delete the plugin source as
rollback.

### Step 8: Verify the full lifecycle

For deterministic contract evidence:

```bash
python3 "$SKILL_DIR/scripts/codeex_plugin.py" exercise <plugin-id> \
  --project-root "$CODEEX_ROOT"
```

Then verify in proportion to risk:

1. Desired installed/uninstalled state is correct.
2. Rebuild is staged and the existing runtime remains usable on failure.
3. An authorized restart or isolated smoke reports the expected active set.
4. The plugin's visible behavior appears when installed and disappears when
   uninstalled without damaging official tabs, tasks, Skills, or MCP.
5. The Codeex management page lists the plugin and its install/uninstall action
   updates desired state, restart disclosure, and the card state correctly.
6. Existing plugins still pass their focused checks.
7. A native UI integration matches the adjacent control's icon geometry,
   computed color, placement, and one-mount invariant in the packaged runtime.
8. A control-route plugin was read back only after its launcher service loaded
   the changed handler and transitive modules.

### Step 9: Hand off

Report the plugin source, hooks, declared permissions, tests, desired state,
active state, runtime-restart state, launcher/control reload state, rollback
result, and any evidence not yet collected. Use `installed`, `active`, and
`verified` as separate states.

## Dependencies

- Python 3.8+ standard library for the portable lifecycle CLI.
- Node.js 24+ and the target Codeex repository for authoritative plugin loading.
- PyYAML 6+ only for `scripts/validate_skill.py`.
- No credentials, remote service, marketplace, or sibling Skill is required.

## Validation

Validate this Skill itself with:

```bash
python3 scripts/validate_skill.py .
```
