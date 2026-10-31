# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-install-tanstack-query` | Makes TanStack Query the shared server-state layer, with `useInvokeQuery`-style wrappers for Tauri | optional downstream atom | Route server-state reads there after the invoke adapter exists; see Overlap Decisions |
| `lov-refactor-modular` | Splits a long file by responsibility while keeping public interfaces and behavior | not composed | Generic split; this Skill carries the Tauri rules (thin `lib.rs`, command registry, typed routers, no long-term `include!`) |
| `lov-app-optimizer` | Fixes runtime jank, battery drain, memory growth, and leaks with before/after evidence | not composed | Runtime performance of a running app goes there; this Skill targets the dev loop and backend structure |
| `lov-app-generator` | Generates or standardizes a whole app, including new Tauri apps | not composed | This Skill restructures an existing Tauri backend; it never scaffolds one |
| `lov-app-release`, `lov-app-delta-updater` | Run a verified multi-channel release; add or verify desktop auto update | not composed | Release and updater work is out of scope here |

## Atomic Handoffs

```text
lov-optimize-tauri-backend
  input: an existing Tauri 2 app (Rust backend plus a React/Vite or similar frontend)
  baseline: lib.rs line count, largest Rust files, command count, invoke usage
  output: no-watch dev scripts, modular backend with a command registry, typed
          domain routers, one frontend invoke adapter, cancellable streams,
          cargo fmt / cargo check / tsc evidence
                |
                v
optional: lov-install-tanstack-query (server-state reads on top of the adapter)
```

This Skill owns acceptance of the command boundary: the registry, routers, and
adapter must agree, and the baseline numbers are reported again after the change.

## Overlap Decisions

Both this Skill and `lov-install-tanstack-query` touch frontend `invoke()` calls.
This Skill owns the adapter that maps old command names onto consolidated
routers; the query Skill owns caching above it. When both apply, the query
wrappers import `invoke` from the adapter rather than `@tauri-apps/api/core`,
otherwise commands moved behind a router stop resolving.

## Composition Decision

Single Skill. The dev loop, module split, command consolidation, invoke adapter,
and stream cancellation all act on one command boundary and share the baseline
metrics; renaming a command touches the registry, a router, and the adapter
together, so splitting the steps into a Kit would separate changes that must
land consistently.
