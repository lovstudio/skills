---
name: lov-reclamation-engineering
description: >
  This Skill should be used when the user asks “设计客户端 App 的安全资源回收”、
  “审查后台任务、缓存、会话或外部工作区的生命周期”, or “review fail-closed cleanup
  and ABA safety” for a concrete desktop, mobile, hybrid, or web client.
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  invocation: kit_only
  tags:
    - app-runtime
    - resource-reclamation
    - lifecycle-engineering
    - fail-closed
    - aba-race
  compatibility: "Portable Agent Skills format; concrete client App source plus host, runtime/framework, lifecycle, and test adapters. Python 3.9+ supports the shared dry-run evidence helper."
  dependencies:
    - python
---

# 资源回收设计 · Resource Reclamation

把具体客户端 App 的资源治理实现成所有权与生命周期协议，而不是“超过一段时间就 kill/delete”。覆盖 desktop、mobile、hybrid 与 Web/PWA；先服从宿主生命周期，再证明 durable owner、runtime lease、活动真相、恢复路径和实例身份。任一关键证据未知、失败或变化时保护资源。

## Triggers

### Activate when

- 用户说“设计客户端 App 不误伤用户状态的后台资源回收”“让闲置会话可恢复地休眠”或“检查关闭页面后 listener、worker、timer 为什么仍在运行”。
- 用户要求治理 window/scene/page、subscription、task、timer、worker/service、native handle、WebView/isolate、cache、socket、download 或可选 PTY/tmux/worktree 的生命周期。
- The user asks to review fail-closed cleanup, prevent an ABA race, or build a conservative lifecycle controller for a concrete client App.

### Do not activate when

- 用户只要求盘点或定位性能根因，尚未建立资源图；先调用 `lov-runtime-audit`。
- 用户只要求一次性清空缓存、强杀进程、删除目录或用户数据；改用对应安全工具并单独取得精确授权。
- The request concerns server retention, cloud garbage collection, or abstract lifecycle theory without a concrete client App and host lifecycle.

## Invocation contract

- `invocation: kit_only`
- 把 `KIT_DIR` 指向包含 `kit.yaml` 的 `lov-app-optimizer` 根目录。
- 从 `$KIT_DIR/references/` 与 `$KIT_DIR/scripts/` 加载共享政策和 helper；不要把本模块当成独立发布包。
- 缺少共享依赖时点名相对路径并输出 `blocked`，不得生成降级版删除命令。

## Kit module I/O contract

### Inputs

要求至少提供：

- 具体 App、host、runtime/framework、build identity 与生命周期事件；
- 资源类型、稳定 ID、durable owner、作用域和允许的动作级别；
- authoritative activity、attachment/consumer/registration/lease、恢复路径与 fingerprint；
- 授权边界：review、implementation、dry-run 或针对精确候选的已批准动作；
- 项目 teardown、background/foreground、suspend/resume、process-death 或 page freeze/restore 测试入口。

优先接受 `app-runtime-evidence/v1` JSON。缺少 owner、identity、activity、dirty/cwd、host lifecycle 或错误语义时仍可输出设计审查，但相关外部资源必须判为 `protect`。

### Outputs

交付一个可独立评审的回收工程包：

1. resource → scope → owner → lease → activity → resume → fingerprint → dependency-order 表；
2. 动作级别、`protect` / `candidate` verdict 与机器可读 reasons；
3. host lifecycle、single-flight、bounded concurrency、两阶段分类和原子最终检查协议；
4. 按需提供项目原生补丁与竞态测试，不提供一次性盲删脚本；
5. dry-run inventory、执行授权门、恢复验证和证据缺口；
6. `diagnosed`、`implemented_not_runtime_verified`、`partially_verified`、`verified` 或 `blocked` 终态。

共享 helper 只评估计划，不执行回收。没有真实同类资源的 teardown/resume 证据时，不得把测试通过升级成 `verified`。

## Action levels

按风险从低到高选择动作：

1. `scope_release`：取消 listener、subscription、timer、task 或 observer；作用域结束时优先执行。
2. `hibernate`：保留 durable state，释放可重建 runtime，并验证按需恢复。
3. `cache_evict`：只移除有明确重建来源和容量策略的缓存。
4. `external_reclaim`：处理 process、PTY/tmux、sidecar、download handle 或 worktree；必须两阶段核验与稳定 fingerprint。
5. `persistent_delete`：删除用户或持久业务数据；默认不属于自动动作，必须使用产品专用流程和独立授权。

## Cross-platform safety invariants

- 对 desktop 持久进程，区分 window close、hidden/tray、background worker、sidecar 和 App exit。
- 对 iOS/Android，服从 foreground/background、suspend、Doze、process death 和系统回收；不得以主动 kill 代替正常生命周期验收。
- 对 React Native/Flutter，同时处理 native host 与 JS/Dart runtime、module/plugin、isolate/channel 的所有权。
- 对 Web/PWA，覆盖 visibility、pagehide/pageshow、freeze/resume、BFCache、tab discard 与 Service Worker 更新/终止；不得依赖 unload 清理。
- 对 external resource，证据缺失、畸形、超预算、陈旧、超时、transport error、跨 owner 或身份不稳时 fail closed。
- `working`、`awaiting_input`、`unknown`、attached、consumer active、registration active 与 operation active 一律保护。
- filesystem/worktree 的 dirty、dirty unknown、cwd in use 与 unregistered 一律不自动删除。
- 同名资源不等于同一实例；最终动作核对 creation time、PID、generation、activity stamp、attachment state 或 adapter fingerprint。
- 先停止无条件 rehydration/restart，再添加 sweep；确认失败时保留 durable identity 以便重试。

## User Profile contract

每次调用先读取 `skill.yaml` 声明的 `user-profile/v1`。按“当前请求与明确授权 → 当前 App/host 状态 → `skills.lov-reclamation-engineering.records` → shared preferences → shared user/brand → fail-closed 默认值”解析冲突。

只在用户直接声明并希望长期沿用时，通过 `$KIT_DIR/scripts/profile_store.py` 保存默认 policy、action level、grace period 或 dry-run 模式。写入必须带 `--confirm` 并回报 profile path。不得持久化资源 ID、PID、session 名、文件路径、凭据、现场状态或一次性授权。完整契约见 `$KIT_DIR/references/user-profile.md`。

## Workflow (MANDATORY)

**必须按顺序执行。任何未知状态都保护外部或持久资源；不得为了提高回收数量放宽判定。**

### Step 0: Resolve the kit, App identity, and authorization

1. 解析 `KIT_DIR`，读取 `$KIT_DIR/references/evidence-contract.md`、`$KIT_DIR/references/reclamation-policy.md` 与 `$KIT_DIR/references/platform-adapters.md`；需要运行时复测时再读 `$KIT_DIR/references/runtime-playbook.md`。
2. 验证 `$KIT_DIR/scripts/evidence_report.py` 与 `$KIT_DIR/scripts/profile_store.py` 可读。
3. 固定 App/build、host、runtime/framework、device/OS/browser engine 与生命周期事件。
4. 读取 Profile，并记录本次权限仅为 review、implementation、dry-run 或 exact-target action。
5. 共享资源、目标身份或权限缺失时输出 `blocked`，并保持所有高风险候选为 `protect`。

### Step 1: Model scopes and ownership before idleness

1. 标出 App、window/scene/page、route/view、background worker/service、runtime/isolate/WebView 与 external resource 的作用域。
2. 为每类资源写清 durable owner、runtime lease、activity truth、resume path、fingerprint 和 dependency order。
3. 把 recent timestamp 与 authoritative idle 分开；把 host suspension 与任务完成分开。
4. 无法回答必需项时，把 external resource 降为 `inventory_only`，把 scoped resource 保留到明确 owner teardown。

### Step 2: Normalize one bounded inventory

1. 每类 marker 只列举一次，批量加载 owner、registration 与 host lifecycle state。
2. 填充 evidence contract 的 activity、attachments、registration、operation、cwd、dirty、identity、evidence 与 retention 状态。
3. 对 artifact、filesystem、provider 与 system query 设置 byte/record/time budget；空、畸形、被系统暂停或预算耗尽不等于 idle。
4. 使用 adapter 显式返回 `unsupported`；不得为缺失平台能力伪造等价状态。

### Step 3: Classify by action level and policy

1. 先应用 universal blockers，再判断 `scope_release`、`hibernate`、`cache_evict` 或 `external_reclaim` 条件。
2. 对 filesystem/worktree 重读 durable references、registration、canonical path、clean status、live cwd 和 identity。
3. 对 unknown directory、foreign session、corrupt row 与用户数据只输出 inventory/protect。
4. 为每个 verdict 返回稳定 reason code；用 `$KIT_DIR/scripts/evidence_report.py` 生成只读计划。

### Step 4: Block ABA for external actions

1. 完成第一次 inventory/classify 后 yield 或等待业务 grace period。
2. 再列举一次 marker，并重新批量读取 owner 与 host state；不沿用第一次可变状态。
3. fingerprint 变化时视为新实例并跳过。
4. 最终动作前执行 O(1) live lease/registration check，并用原 fingerprint 做 atomic conditional action。
5. 条件失败、自然退出、系统回收、timeout 或 transport error 均返回可重试状态，不扩大目标集合。

### Step 5: Repair creation, hydration, and teardown seams

1. 先取消作用域结束后仍活跃的 listener/task/timer，再处理可恢复 runtime 与 external resource。
2. 只启动 pending work、连接 canonical live instance、响应显式可见/恢复请求或宿主许可的后台任务。
3. 把逐实体 inventory 改为 shared snapshot、batch read、point lookup 与 single-flight，并限制 start/stop/scan 并发。
4. 让 parent teardown await child resource；未确认时保留 durable identity 与用户数据。
5. 保留目标仓库现有改动，不用一次性脚本掩盖生命周期缺陷。

### Step 6: Test host lifecycle, decisions, and races

至少覆盖 working/awaiting/unknown/idle、attached/consumer/registration/operation、空或畸形 artifact、timeout/permission/provider failure、同名重建 ABA、并发 cleanup single-flight，以及宿主对应的 background/suspend/process-death 或 hidden/freeze/BFCache 流程。

filesystem/worktree adapter 另覆盖 registered clean、dirty、dirty unknown、cwd in use、identity changed 与 unregistered directory；external process adapter 另覆盖自然退出、kill failure 和 resume。

### Step 7: Enforce the execution gate and assign status

1. 默认停在 review/implementation/dry-run；helper 永不执行回收。
2. 只在用户授权精确目标与动作后，允许项目代码执行二次核验和原子条件动作。
3. 动作前展示 candidate、fingerprint、owner、reason、依赖顺序与恢复/回滚路径。
4. 动作后验证 durable state、runtime absence 与 on-demand resume；失败时保留 identity 并报告重试条件。
5. 仅设计审查写 `diagnosed`；代码与测试完成但无 live teardown/resume 写 `implemented_not_runtime_verified`；部分真实流程完成写 `partially_verified`；同负载和宿主生命周期验收全部满足才写 `verified`。

## Evidence calibration: Yoda

把 Yoda 保留为首个案例校准，不把其资源或阈值泛化：

- `platform_family: desktop`
- `runtime: electron`
- `case_version: Yoda v0.18.10`
- `implementation_commit: 290fbc48c713163f20bd6f956e80e15d00dfa357`
- `code_fact`：`tmux-reclamation.ts` 实现 snapshot、两阶段 revalidation、fingerprint 与 bounded cleanup；`tmux-reclamation.test.ts` 覆盖 fail-closed、ABA replacement 与 concurrent single-flight。
- `code_fact`：`worktree-cwd-guard.ts`、`worktree-service.ts` 和对应测试保护 live cwd、dirty、unregistered 与 changed-branch worktree；`unregistered-worktree-inventory.ts` 只读列举未知目录。
- `code_fact`：`task-runtime-reclamation.ts` 与测试让 teardown 在 detached-session sweep 前完成，并在失败时保留可重试结果。
- `correctness_gate`：案例记录 3,115 tests 及 format/lint/typecheck/build 通过；该门只证明实现回归，不是 live reclamation acceptance。
- `boundary`：没有执行生产批量 kill、blind worktree remove 或递归删除，也没有完成真实 teardown 后的 on-demand resume 验收。因此终态保持 `implemented_not_runtime_verified`。

## Dependencies

- 目标 App 的 host lifecycle、owner model、runtime/framework adapters、teardown APIs 与测试框架。
- Python 3.9+，用于 `$KIT_DIR` 中的共享 Profile 和只读证据报告。
- Electron、Tauri、native、iOS、Android、React Native、Flutter 与 Web/PWA adapter 按目标组合加载；Git/tmux/SSH/SQLite 仅是可选 Yoda-style external adapters。

## Shared references

- `$KIT_DIR/references/reclamation-policy.md` — policy、universal blocker、两阶段协议与测试矩阵。
- `$KIT_DIR/references/evidence-contract.md` — `app-runtime-evidence/v1` 资源字段与 verdict 契约。
- `$KIT_DIR/references/platform-adapters.md` — host、runtime/framework 与 optional resource adapter 组合。
- `$KIT_DIR/references/runtime-playbook.md` — 具体 App 身份、宿主生命周期与运行时复测。
- `$KIT_DIR/references/user-profile.md` — Profile 读取与持久化规则。
