# lov-optimize-tauri-backend

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

Optimize Tauri 2 backend architecture, command surfaces, IPC streams, and Rust
development ergonomics.

Independent source repository, also distributed through [skill-publisher dev-skills](https://example.com/skills/dev-skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add skill-publisher/optimize-tauri-backend-skill --all -g
```

The aggregate bundle remains available:

```bash
npx skills add skill-publisher/dev-skills --all -g
```

Or through Claude Code plugin marketplace:

```text
/plugin marketplace add skill-publisher/dev-skills
/plugin install dev-tools@lov-dev
```

## What It Covers

- Explains why Rust-side Tauri changes restart the native app during `tauri dev`.
- Adds frontend-focused `tauri dev --no-watch` workflows.
- Splits oversized `src-tauri/src/lib.rs` into real Rust modules.
- Moves `generate_handler!` into a stable command registry.
- Reduces excessive `#[tauri::command]` counts through typed domain routers.
- Centralizes frontend `invoke()` calls through an app adapter.
- Adds stream id + cancel handling for long `Channel` IPC calls.
- Preserves dev restart state with hash/session resume and save flushing.

## Typical Use

```text
/lov-optimize-tauri-backend 分析这个 Tauri app 的 Rust 重启问题，并优化后端结构
```

```text
/lov-optimize-tauri-backend lib.rs 太大、commands 太多，帮我降到 100 个以内
```

```text
/lov-optimize-tauri-backend fix Tauri stale callback warnings after HMR/reload
```

## Expected Output

The skill guides the agent to report:

- current `lib.rs` line count;
- largest Rust backend files;
- total `#[tauri::command]` count;
- whether startup code owns command registration;
- whether frontend invokes are centralized;
- which long IPC streams need cancellation;
- verification results from `cargo fmt`, `cargo check`, and TypeScript checks
  when allowed by the target repo.

## Dependencies

No script dependencies. This is an instruction-only development skill.

## License

MIT
