---
name: lov-optimize-tauri-backend
description: >
  Optimize Tauri backend architecture and development ergonomics for Tauri 2
  apps, especially Rust restart pain, oversized src-tauri/src/lib.rs files,
  excessive #[tauri::command] surfaces, stringly invoke APIs, long IPC streams,
  and dev-state recovery. Use when the user asks about Tauri hot reload,
  Rust-side restarts, "lib.rs 太大", "commands 太多", "降低到 100 个以内",
  "Tauri 后端优化", "optimize-tauri-backend", "Tauri backend refactor",
  or "Tauri dev reload".
license: MIT
compatibility: >
  Instruction-only skill for Tauri 2 + Rust backends with React/Vite or similar
  frontends. No runtime dependencies. Use the target repository's package
  manager and honor local AGENTS.md / CLAUDE.md constraints.
metadata:
  author: contributors
  version: "0.2.0"
  tags: tauri rust backend ipc commands hot-reload modularization dev-experience
---

# optimize-tauri-backend — Tauri 后端优化

Use this skill to turn a growing Tauri backend into a smaller, more stable,
more pleasant development surface. The goal is not magical Rust HMR. The goal
is to reduce how often Rust changes are needed, make Rust restarts less
disruptive, and keep the Tauri command boundary small, typed, and auditable.

## When to Use

- The user is developing with `pnpm tauri dev` / `npm run tauri dev` and Rust
  file changes keep closing and reopening the app.
- `src-tauri/src/lib.rs` has become a God file.
- The app exposes 100+ or 200+ `#[tauri::command]` functions.
- Frontend code scatters raw `invoke("command_name")` strings across many
  components.
- Long-running `invoke` / `Channel` calls cause stale callback warnings after
  reload or HMR.
- The user wants backend modularization, command consolidation, better dev
  scripts, or restart-state recovery.

## Core Position

State this clearly when asked about hot reload:

| Surface | Dev behavior |
|---|---|
| Frontend Vite / React | real HMR |
| Rust / Tauri backend | recompile + restart native process |
| Best optimization | separate stable Tauri shell from volatile domain logic, then make restarts cheap |

Do not promise Rust backend HMR inside Tauri. Tauri's Rust-side "hot reload"
means watch, rebuild, and restart.

## Workflow

### Step 1: Read Local Rules First

Before changing files, inspect project instructions and config:

```bash
pwd
find .. -name AGENTS.md -print
find .. -name CLAUDE.md -print
rg -n "beforeDevCommand|devUrl|frontendDist|tauri dev|--no-watch|invoke\\(|#\\[tauri::command\\]|generate_handler" package.json src-tauri src 2>/dev/null
```

Honor local constraints. If the repo says not to run `pnpm build`, do not run
it. Prefer `rg` and small file reads. Do not revert unrelated user changes.

### Step 2: Baseline the Backend

Collect objective numbers before proposing or editing:

```bash
wc -l src-tauri/src/lib.rs 2>/dev/null
find src-tauri/src -maxdepth 3 -type f -name "*.rs" -print0 | xargs -0 wc -l | sort -n | tail
rg -n "#\\[tauri::command\\]" src-tauri/src | wc -l
rg -n "generate_handler!|invoke\\(" src-tauri/src src 2>/dev/null
```

Report:

- `lib.rs` line count.
- Largest Rust files.
- Number of Tauri commands.
- Whether command registration lives inside startup code.
- Whether frontend uses a centralized invoke adapter.
- Known long IPC streams or background tasks.

### Step 3: Classify the Problem

Use these buckets:

| Bucket | Symptom | Preferred fix |
|---|---|---|
| Dev loop | Rust edits restart the app during UI work | add no-watch dev script |
| God module | `lib.rs` has thousands of lines | split into real Rust modules |
| Command sprawl | 100+ command functions | consolidate by domain with typed routers |
| Invoke sprawl | raw command strings everywhere | frontend invoke adapter / API layer |
| Long IPC | stale callback warnings after reload | stream id + cancel + send-error stop |
| Restart pain | route/session lost after app restart | dev resume state + flush pending saves |
| Compile pain | small domain edits rebuild huge surfaces | move volatile logic out of Tauri shell |

### Step 4: Improve the Dev Loop

Add scripts without removing the existing full dev command:

```json
{
  "scripts": {
    "dev:web": "vite",
    "dev:app": "tauri dev",
    "dev:app:no-watch": "tauri dev --no-watch"
  }
}
```

Document usage:

- `dev:app`: full Tauri development with Rust watcher.
- `dev:app:no-watch`: frontend-focused development; Vite HMR stays active and
  Rust file changes do not restart the app.
- `dev:web`: pure web frontend when the app supports browser-only work.

Keep the existing `pnpm tauri dev` route working unless the user explicitly
asks to remove it.

### Step 5: Modularize the Rust Backend

Goal: `src-tauri/src/lib.rs` should be a thin entrypoint.

Target shape:

```rust
mod app;
mod diagnostics;
mod pty_manager;

pub use app::run;
```

Recommended backend shape:

```text
src-tauri/src/
├── lib.rs
├── app/
│   ├── mod.rs
│   ├── run.rs
│   ├── command_registry.rs
│   ├── command_routers.rs
│   ├── settings_core.rs
│   ├── session_cache.rs
│   ├── session_listing.rs
│   └── ...
└── shared_runtime_modules.rs
```

Rules:

- Prefer real `mod` modules over long-term `include!`.
- During large migrations, a temporary `include!` split is acceptable only as
  a compile-preserving checkpoint. Convert it to real modules before finishing.
- Keep each file under roughly 1000 lines unless the user sets a stricter
  threshold.
- Move `generate_handler!` out of `run.rs` into `command_registry.rs`.
- Keep `run.rs` focused on app lifecycle, plugins, menus, windows, and
  watchers.

### Step 6: Reduce Commands Without Destroying the Boundary

Do not replace 200 commands with `do_anything(action, payload)`. That removes
type and permission boundaries.

Good consolidation pattern:

```rust
#[tauri::command]
async fn settings_command(action: String, payload: serde_json::Value) -> Result<serde_json::Value, String> {
    match action.as_str() {
        "patch_settings" => { /* typed deserialize + validate */ }
        "get_settings" => { /* typed return */ }
        _ => Err(format!("unknown settings action: {action}")),
    }
}
```

Better when possible:

```rust
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", tag = "kind")]
enum SettingsPatch {
    SetEnv { key: String, value: String },
    DeleteEnv { key: String },
    TogglePlugin { plugin_id: String, enabled: bool },
}
```

Recommended domains to consolidate:

| Domain | Typical router |
|---|---|
| templates / marketplace install | `template_command` |
| file utilities | `file_command` |
| PTY lifecycle | `pty_command` |
| workspace state | `workspace_command` |
| MaaS/provider settings | `maas_command` |
| settings/env/permissions/plugins | `patch_settings` or `settings_command` |

Keep explicit commands for:

- High-risk operations where an explicit name improves auditability.
- Commands with distinct permission or capability requirements.
- Public app API surfaces that should remain stable.

Target: under 100 commands for medium-sized apps, lower only if domain routers
stay typed and auditable.

### Step 7: Centralize Frontend Invokes

Create one adapter such as `src/lib/tauri.ts`:

```ts
import { invoke as tauriInvoke, type InvokeArgs, type InvokeOptions } from "@tauri-apps/api/core";

const COMMAND_ROUTES: Record<string, { command: string; action: string }> = {
  install_skill_template: { command: "template_command", action: "install_skill_template" },
  pty_write: { command: "pty_command", action: "pty_write" },
};

export function invoke<T>(cmd: string, args?: InvokeArgs, options?: InvokeOptions): Promise<T> {
  const route = COMMAND_ROUTES[cmd];
  if (!route) return tauriInvoke<T>(cmd, args, options);
  return tauriInvoke<T>(route.command, { action: route.action, payload: args ?? {} }, options);
}
```

Then replace component imports from `@tauri-apps/api/core` with the app adapter.

Use TanStack Query or a local query wrapper for server-state reads. Keep
imperative side effects imperative.

### Step 8: Fix Long IPC and Reload Warnings

When a command streams via `Channel`, use a request id and cancellation:

Frontend:

```ts
const streamId = crypto.randomUUID();
const channel = new Channel<Event>();
invoke("list_items_streamed", { streamId, onEvent: channel });

return () => {
  invoke("cancel_items_stream", { streamId }).catch(() => {});
};
```

Also cancel on HMR / pagehide:

```ts
if (import.meta.hot) {
  import.meta.hot.dispose(() => cancelStream("hmr-dispose"));
}
window.addEventListener("pagehide", () => cancelStream("pagehide"));
```

Rust:

```rust
static STREAM_CANCELS: LazyLock<Mutex<HashMap<String, Arc<AtomicBool>>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));
```

Rules:

- `invoke` should resolve quickly after starting a background stream.
- Every stream has a `streamId`.
- Cleanup removes the stream token.
- Sending to a dead channel must stop the loop.
- HMR / route unmount / pagehide should cancel active streams.
- Do not hide stale callback warnings globally with `console.warn = ...`.

### Step 9: Restore State After Dev Restarts

Make restarts less disruptive:

- Persist current hash in development.
- Persist active workspace conversation/session id.
- Flush debounced workspace saves on `pagehide`, `visibilitychange`, and HMR
  dispose.
- On reload, if the app lands on an empty/default hash, restore the last hash.
- For expensive session lists, keep a memory/query cache and re-stream in the
  background.

Keep this dev-oriented unless the product requires production resume semantics.

### Step 10: Verify

Run only checks allowed by local instructions:

```bash
cargo fmt
CARGO_TARGET_DIR=target/codex-check cargo check
pnpm exec tsc --noEmit --pretty false
```

Use a separate `CARGO_TARGET_DIR` when the user's `tauri dev` process holds the
normal Cargo build lock.

Report:

- `lib.rs` line count.
- Largest Rust file count.
- Tauri command count.
- Rust check result.
- TypeScript check result, including unrelated existing blockers.
- Scripts added and how to use them.

## Output Checklist

Final answer must include:

- What changed in dev scripts.
- What changed in backend module/command structure.
- What changed in IPC/restart lifecycle.
- Exact verification commands run.
- Any remaining warnings or blocked checks.

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
