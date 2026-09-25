---
name: lov-app-professional-design
description: >
  为桌面、Web 与移动应用诊断并落地商业级性能架构，覆盖启动初始化、前后端职责、增量数据桥、缓存失效和受控并发；当用户说“按商业产品优化这个应用”“页面切换又重新加载”或 "design a production-grade app performance architecture" 时使用。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  tags:
    - app-architecture
    - performance
    - incremental-data
    - bridge
    - concurrency
  compatibility: "Instruction-only skill for desktop, Web, mobile, Electron, Tauri and hybrid applications."
  dependencies: []
---

# 性能架构师 · Performance Architect

Turn an application's slow, restart-prone, or poorly divided data path into a
measured production architecture and implement the repair. Treat responsiveness,
resource use, lifecycle ownership, recovery, and freshness as one system.

## Triggers

### Activate when

- 用户说“把这个应用按商业级产品做性能架构设计”或“系统性优化初始化、数据加载和并发”。
- 用户说“页面切换又重新加载”“前端被后端任务卡住了”或“列表要实时增量更新”。
- 用户希望审查前端、bridge、后端线程、数据库和缓存之间的职责划分并直接修复。
- The user asks to “design a production-grade app performance architecture”.
- The user asks to “make this desktop app load incrementally without blocking the UI”.

### Do not activate when

- 只调整颜色、排版、动效或视觉层级；使用前端设计能力。
- 只处理一个已有明确根因、没有生命周期或跨层设计影响的小型缺陷；使用常规调试流程。
- 只治理 Tauri 命令数量、Rust 热重载或 `lib.rs` 拆分；使用 `lov-optimize-tauri-backend`。
- 用户只要求架构选型、成本比较或新系统方案，尚未进入现有应用性能设计；使用 solution architecture 能力。

## Required references

- Always read `$SKILL_DIR/references/architecture-playbook.md` before proposing or changing architecture.
- For IPC, native bridge, high-volume lists, polling, subscriptions, or streaming,
  also read `$SKILL_DIR/references/bridge-and-streaming.md`.
- For worker pools, threads, processes, database parallelism, or CPU budgeting,
  also read `$SKILL_DIR/references/concurrency-and-capacity.md`.
- Before declaring completion, read and apply
  `$SKILL_DIR/references/validation-checklist.md`.

## Operating principles

1. **Measure the real path.** Inspect the running build, current branch, active
   process, representative data size, and actual hot path before attributing cost.
2. **Own work at the right lifetime.** App-, account-, workspace-, database-,
   page-, and request-scoped work are different. A page must not own a durable
   domain job merely because it displays the result.
3. **Place work by responsibility, not fashion.** UI code subscribes, renders,
   owns ephemeral interaction state, and performs cheap view-local derivation.
   Authoritative data access and shared or heavy work belong in a domain runtime
   or bounded background execution. Do not move everything to either side.
4. **Make freshness explicit.** Cache identity, source fingerprint, generation,
   sequence, invalidation, and recovery are part of the protocol, not incidental
   component state.
5. **Stream usable progress.** Prefer cached-first snapshots and bounded batches
   over an empty screen followed by one giant payload.
6. **Bound concurrency.** More tasks, threads, queries, watchers, and processes
   are not automatically faster. Every queue needs a capacity and overload rule.
7. **Preserve a coherent snapshot.** During refresh, keep the last complete view
   unless partial replacement is itself the product contract.
8. **Prove user-visible improvement.** Compilation and unit tests are necessary
   evidence, but interaction latency, cold/warm startup, large-data behavior, and
   lifecycle regressions decide completion.

## Workflow (MANDATORY)

### Step 0: Resolve instructions and scope

1. Read repository-level agent instructions and the required references above.
2. Preserve unrelated working-tree changes and identify the actual integration branch.
3. Determine whether the request is diagnosis-only or change-oriented. A reported
   performance defect normally includes implementation unless the user explicitly
   asks only for a review or report.
4. Identify supported platforms and the real runtime currently under test.

Do not begin with a generic rewrite plan. Start from the failing interaction or
measured hot path supplied by the user.

### Step 1: Establish the runtime truth

Collect evidence proportionate to the problem:

- running binary/version versus repository commit and worktree;
- cold start, warm start, page revisit, account/workspace switch, and app resume;
- representative and worst-case data volume;
- main-thread long tasks or event-loop lag;
- backend CPU, memory, I/O, query count, subprocess count, and queue depth;
- bridge call frequency, payload size, serialization cost, and dropped/stale events;
- the code path that starts, cancels, retries, caches, and invalidates the work.

Record observed facts separately from inferences. If full profiling is expensive,
instrument the smallest decisive path and leave copyable diagnostics useful for
the next run.

### Step 2: Draw the ownership and lifecycle map

For every expensive job or shared dataset, write a compact matrix:

| Concern | Owner | Lifetime/identity | Start | Invalidate | Consumer |
|---|---|---|---|---|---|
| Example index | backend supervisor | database snapshot | app bootstrap | source fingerprint changes | search views |

Classify each item as app-, session-, account-, workspace-, database-, page-, or
request-scoped. Flag these mismatches immediately:

- page mount starts app-scoped initialization;
- component unmount cancels a shared domain job;
- backend work is repeated for each subscriber;
- frontend stores authoritative large datasets or scans storage directly;
- file events force full reloads without source verification;
- navigation replaces valid content with `0` or an empty loading state.

### Step 3: Define the performance contract

Define concrete behavior before code:

- what must be interactive first;
- what cached data may appear immediately;
- first useful batch and progress semantics;
- freshness and consistency expectations;
- retry, offline, crash, and partial-failure behavior;
- CPU/memory/I/O budget and priority relative to foreground interaction;
- cold, warm, revisit, large-data, and mutation acceptance scenarios.

Use product-derived targets. Label any temporary engineering budget as provisional;
do not invent benchmark wins or claim production readiness from synthetic numbers.

### Step 4: Design the control plane and data plane

Separate two paths:

- **Control plane:** initialize, subscribe, unsubscribe, inspect source, invalidate,
  retry, pause, resume, and expose health.
- **Data plane:** cached snapshot, incremental batch/patch, progress, error, and
  completion events.

The normal target architecture is:

```text
app lifecycle / source watcher
          │ invalidate or ensure(identity)
          ▼
global domain runtime ── bounded backend workers ── storage / index / services
          │ versioned snapshot + ordered deltas
          ▼
frontend external store ── subscriptions ── pages and components
```

Adapt this seam to the framework. Do not create an extra service or process when
an existing application runtime can safely own the job.

### Step 5: Design startup and initialization

Partition startup work:

1. **Bootstrap:** restore minimal durable state and make the shell interactive.
2. **Essential readiness:** start idempotent global services required by the
   current identity.
3. **Background preparation:** build indexes, scan metadata, hydrate large stores,
   and publish progress without blocking first interaction.
4. **Idle/conditional work:** defer features that have no current consumer or
   product deadline.

Initialization must be deduplicated by stable identity, survive page navigation,
publish inspectable status, and support restart/recovery. Persist checkpoints only
when rebuilding is costly enough to justify versioning and migration complexity.

### Step 6: Design incremental data flow and invalidation

Use a versioned snapshot protocol with stable identity, generation, monotonic
sequence, phase, progress, and completion. For large data:

- hydrate the last complete snapshot first when valid;
- send bounded batches or patches;
- coalesce updates to the renderer's useful cadence;
- reject stale generations and out-of-order sequences;
- keep one producer for many subscribers;
- distinguish consumer cancellation from producer cancellation;
- apply backpressure instead of growing an unbounded event queue;
- verify source fingerprints before reloading;
- retain the last coherent snapshot during background refresh, then swap or
  reconcile according to the consistency contract.

Use the bridge reference for protocol and failure details.

### Step 7: Design concurrency and resource control

Classify work as CPU-bound, I/O-bound, latency-sensitive, throughput-oriented,
or isolation-sensitive. Then choose async tasks, worker threads, a bounded pool,
or processes for a reason.

Requirements:

- derive CPU worker limits from available capacity while reserving foreground
  responsiveness;
- cap database and network concurrency independently;
- prioritize visible/interactive work over indexing and maintenance;
- expose queue depth, active workers, throughput, cancellation, and failures;
- shut workers down cleanly on identity change or application exit;
- test oversubscription and slow-consumer behavior.

Use the concurrency reference before adding threads or processes.

### Step 8: Implement the smallest coherent vertical slice

Fix the complete path instead of moving the bottleneck across the bridge:

1. backend/domain runtime and lifecycle ownership;
2. typed/versioned bridge or service contract;
3. frontend external store and subscription lifecycle;
4. cache schema and source fingerprint;
5. invalidation, retry, stale-event isolation, and diagnostics;
6. UI progress, retained content, and copyable failure details;
7. targeted tests and runtime instrumentation.

Reuse established project primitives. Keep domain loading out of route components.
Keep raw bridge calls out of presentation components when an adapter/store seam
already exists. If the change alters multiple subsystem lifetimes or contracts,
record the decision in an ADR.

### Step 9: Run architecture regression tests

At minimum, cover the scenarios relevant to the change:

- two simultaneous subscribers start one producer;
- leaving and returning to a page reuses the active or complete snapshot;
- unsubscribing one consumer does not cancel shared work;
- unchanged source signals do not reload or replace the list;
- changed source refreshes in the background;
- stale generations and out-of-order batches are ignored;
- errors preserve the last good snapshot and expose retry/diagnostics;
- identity changes isolate old data and terminate obsolete work;
- large datasets remain incrementally visible and interactive;
- configured worker and queue limits hold under load.

Prefer deterministic unit tests for lifecycle/state machines plus one realistic
integration or runtime verification for the actual bridge.

### Step 10: Validate and report

Apply `$SKILL_DIR/references/validation-checklist.md`. Re-run the exact failing
interaction on the real runtime when practical. Compare before/after with the same
data and environment.

Report:

1. confirmed root cause and evidence;
2. ownership/lifecycle change;
3. bridge, cache, invalidation, and concurrency contract;
4. code and ADR paths;
5. cold/warm/revisit/large-data verification;
6. tests, measurements, and remaining evidence gaps;
7. integration or merge result when requested.

## Architecture gates

Reject or repair these patterns unless evidence shows they are appropriate:

- `Promise.all` over all startup work before first useful render;
- full-dataset transfer on every poll, mount, or file event;
- moving all application logic into either frontend components or backend commands;
- page-local ownership of reusable initialization;
- per-row renderer events without batching or coalescing;
- giant datasets in `localStorage` or component state as the source of truth;
- unbounded task creation, worker pools, watchers, queues, or retries;
- adding threads while leaving duplicate queries, subprocesses, or serialization;
- a single loading boolean that discards valid content during refresh;
- cancellation tokens shared incorrectly between producer and subscribers;
- cache reuse without identity, schema version, or source validation;
- cache invalidation that always means immediate full recomputation;
- declaring success from build output while the reported interaction remains untested.

## Dependencies

None. Use the target application's existing profiler, test runner, bridge, state
management, storage, and backend concurrency primitives where suitable.

## Runtime context

运行前读取同目录 `skill.yaml`，由宿主的 `skill-runtime` 按“当前请求、项目上下文、个人配置、品牌 Profile、安全默认值”的顺序注入，只使用 manifest 声明的字段。

- 缺少 `required: true` 字段时，按 `questions` 向用户提出一个聚焦问题；回答只用于本次运行，除非用户明确要求保存。
- Profile 只用于公开品牌事实；个人配置只用于决策，不自动写入产物或源码。
- 调试报错提供可复制的 `context_id`、字段路径和来源，不输出秘密、完整私人路径或原始内容。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
