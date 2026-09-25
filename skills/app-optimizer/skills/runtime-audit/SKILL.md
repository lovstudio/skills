---
name: lov-runtime-audit
description: >
  用于桌面、移动端与 Web/PWA 客户端的长运行性能审计；当用户要求定位 Electron、Tauri、原生 iOS/Android、React Native、Flutter 或浏览器 App 的卡顿、轮询、桥接和资源扇出时使用。
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  invocation: kit_only
  tags:
    - app-performance
    - runtime-audit
    - client-runtime
    - resource-ownership
    - fanout-analysis
    - evidence-ledger
  compatibility: "Portable Agent Skills format; kit-only invocation with target-specific desktop, mobile, web, process, profiler, storage, network, bridge, and lifecycle adapters."
  dependencies:
    - python
---

# 运行态体检 · Runtime Checkup

把“客户端越用越卡”拆成可复查的运行身份、时间序列、规模因子、资源所有权图和可证伪假设。根据目标 App 组合 adapter；保持诊断只读，并把现场测量、源码事实、因果推断和验收结论分开记录。

## Triggers

### Activate when

- 用户说“帮我审计这个桌面或手机 App 为什么越用越卡”“查清楚 Web/PWA 后台任务为什么不断增长”。
- 用户要求量化 Electron/Tauri IPC、React Native bridge、Flutter platform channel、原生线程/队列、浏览器事件、存储或网络工作如何随实体数放大。
- The user asks to audit a long-running client app, build a cross-runtime ownership graph, or test a fan-out hypothesis before changing code.

### Do not activate when

- 用户只要求实现一个已确认的修复；改用普通开发流程，完成后交给 `lov-runtime-verification`。
- 用户只要求强杀进程、删除目录、清缓存或释放磁盘；不要用审计结果替代明确授权和安全清理工具。
- The request is limited to SEO, generic Lighthouse scoring, bundle size, marketing copy, server-only performance, or hardware recommendations.

## Invocation and I/O contract

`invocation: kit_only`。本模块不承诺脱离 App Optimizer Kit 独立运行。把包含 `kit.yaml` 的目录解析为 `KIT_DIR`；证据合同、adapter 手册、Profile 与报告脚本等共享依赖一律从 `$KIT_DIR` 加载，不从模块目录复制或猜测。

### Inputs

要求至少提供或现场解析：

- 可观察症状与可复现工作负载，例如输入卡顿、掉帧、导航变慢、周期同步、后台唤醒、CPU 峰值、RSS/内存增长或电量/网络异常；
- `platform_family`、`runtime`、实际运行 build/deploy/device/browser 身份，以及当前生命周期状态；
- 可读取的运行时清单与目标源码，以便把大规模计数映射到具体 consumer、事件和循环。

缺少实际运行身份或最小只读访问时输出 `blocked`，不得把另一个 checkout、设备、部署或静态源码当作现场结论。

### Outputs

交付一个审计包，至少包含：

1. `platform_family`、`runtime`、启用的 adapters、build/deploy 身份和采样窗口；
2. idle、典型操作和周期/生命周期事件的基线表；
3. UI surface → owner/entity → runtime handle → thread/process/worker/service 的资源图；
4. 规模放大公式与独立计数对照；
5. 按 P0/P1/P2 排序的假设、支持证据、证据缺口和 falsifier；
6. `diagnosed` 或 `blocked` 终态，以及下一项最有判别力的测量。

输出可以是 Markdown；需要机器可读审计时，同时生成 `app-runtime-evidence/v1` JSON。审计模块不得输出 `diagnosed`、`blocked` 之外的终态，也不得把删除、kill、缓存重置或重装命令当作诊断结论。

## Adapter model

先选 `platform_family`，再选一个或多个 runtime adapters；组合应用必须同时覆盖跨层边界。

| Platform family | Runtime examples | Minimum identity and signals |
| --- | --- | --- |
| `desktop` | `electron`, `tauri`, native desktop, embedded webview | executable/bundle、version/commit、process tree、window/webview、event loop/thread、IPC/command、filesystem/storage |
| `mobile` | `native-ios`, `native-android`, `react-native`, `flutter`, hybrid | physical device、OS、build ID、app PID/lifecycle、frame stalls、native threads、bridge/channel/isolate、network/storage/background work |
| `web` | `browser`, `pwa`, embedded web client | origin/deploy ref、browser/profile、tab/frame、main thread、worker/service worker、cache/storage、fetch/WebSocket、visibility lifecycle |

按目标功能追加 process、UI/frame、bridge/IPC、network、storage/database、scheduler/background、terminal/session 或 repository/worktree adapter。某信号没有可靠 adapter 时记录 `unknown`；不得用另一个平台的 proxy 冒充直接测量。

## Product and safety contract

- 把 `measurement`、`code_fact`、`inference`、`acceptance` 分开；审计通常不产生 acceptance。
- 每条数字记录 build/source、时间或窗口、工作负载、sampler、进程/线程/页面边界和单位；缺失项显式标为 evidence gap。
- 标注 mean、peak、p95、p99、瞬时值、inventory 与派生值；不得混用同一指标 ID。
- descendant RSS、浏览器聚合内存、系统能耗或 profiler estimate 必须标成 proxy，不与目标进程直接值混算。
- 遮蔽 token、credential、私有内容和用户数据；只记录定位证据所需的最小元数据。
- 保持只读。发现疑似孤儿资源时只分类，不终止进程/会话、不移除 worktree、不清应用数据。
- 目标身份不一致时仅在用户明确授权后重启或切换 build；否则把源码分析标为 historical，无法关联现场时输出 `blocked`。

## User Profile contract

每次调用先读取 `skill.yaml` 声明的 `user-profile/v1` 上下文。按“当前请求 → 当前项目与运行时 → `skills.lov-runtime-audit.records` → shared preferences → shared user/brand → 保守默认值”解析冲突。

只在用户直接声明并要求跨会话沿用时，通过 `$KIT_DIR/scripts/profile_store.py` 持久化默认平台/运行时、采样窗口、报告粒度或验收预算。不要持久化凭据、现场 PID、设备标识、私有绝对路径、采样数据、Yoda 数值或推断结论。完整契约见 `$KIT_DIR/references/user-profile.md`。

## Workflow (MANDATORY)

**必须按顺序执行；任何缺失证据都降低结论等级，不得用猜测补齐。**

### Step 0: Resolve the kit and adapters

1. 解析 `KIT_DIR`，读取 `$KIT_DIR/kit.yaml`、`$KIT_DIR/references/evidence-contract.md`、`$KIT_DIR/references/runtime-playbook.md` 与 `$KIT_DIR/references/platform-adapters.md`。
2. 验证 `$KIT_DIR/scripts/evidence_report.py` 和 `$KIT_DIR/scripts/profile_store.py` 可读；共享资源缺失时点名相对路径并输出 `blocked`。
3. 声明 `platform_family`、`runtime` 与 adapter 组合；解释每个 adapter 的 authoritative source、proxy 边界和不可见信号。
4. 读取 Profile，记录只读授权边界、目标 surface 和不会触碰的资源。

### Step 1: Pin the actual runtime identity

1. 桌面端固定 bundle/executable、PID/process tree、cwd（如适用）、version/commit、build mode、window/webview 和启动参数。
2. 移动端固定真实设备、OS、安装包/build ID、app PID、foreground/background 状态，并区分 native、JS、Dart、engine 与 extension/service 进程。
3. Web/PWA 固定 URL/origin、deploy ref、browser/version/profile、tab/frame、worker/service worker、cache 版本与 visibility 状态。
4. 记录配置、日志、数据库/storage 与 profiler 来源，但不复制 secrets 或用户内容。

### Step 2: Establish a reproducible baseline

1. 定义一个用户体验指标、一个运行时指标和一个规模指标；阈值来自该产品的 SLO、平台指南或用户明确预算。
2. 覆盖 idle foreground、idle/background 或 hidden、典型输入/导航，以及至少一个完整同步、刷新、后台任务或生命周期事件。
3. 使用多个短样本；记录 `observed_at`、sample count、cadence、window、workload ID、unit、mean/peak 和可用 percentile。
4. 把 App 事件、frame/event-loop/thread、IPC/bridge/network/storage/subprocess 与资源数量放在同一时间轴。

### Step 3: Build the ownership and amplification graph

1. 从用户可见 surface 追到 durable owner、resident entity、runtime handle、thread/process/worker/service 与持久化资源。
2. 从 timer/event/lifecycle callback 追到 subscriber/store、bridge/controller、DB/storage、network、filesystem 与 subprocess。
3. 计算 `event frequency × matching owners × resident entities × surfaces/subscribers × per-entity work`。
4. 检查无界并发、逐项 bridge/RPC、重复查询/序列化、全量 hydration、短周期扫描、后台反复唤醒和不可见 surface 继续工作。
5. 用源码预测调用次数，再用独立运行时 adapter 核对；不一致时修正模型，不挑选有利数字。

### Step 4: Construct the evidence ledger

1. 给每条记录分配稳定 ID、stage、kind、value/unit、source 和 note。
2. 为所有记录补 `provenance`：`build_ref`、`source_ref`、`observed_at`、`workload_id`、`sample_window` 与 `sampler`；不适用或未知时写明原因。
3. 把源码可证明的调用链写成 `code_fact`；把乘法结果写成 `inference`，并在 `derivation` 中记录 inputs、formula、assumptions、rounding 与 falsifier。
4. 把现场清点或采样写成 `measurement`。只有同负载复测达到该产品预先声明的 threshold 时，后续 verification 模块才能写 `acceptance`。
5. 为跨证据类型对照写 `comparison.quality: directional`；输入只使用 `paired | implementation_bound | directional`，异质证据不得输出精确下降率。

### Step 5: Normalize the report

需要双格式报告时运行：

```bash
python3 "$KIT_DIR/scripts/evidence_report.py" \
  --input evidence.json \
  --json-output runtime-audit.json \
  --markdown-output runtime-audit.md
```

检查 schema、warning、缺失 support ID、provenance gap、不可比较单位和 proxy 边界。脚本只评估证据与计划，不执行终止、删除或重置。

### Step 6: Rank findings and hand off

1. 只把同时具备时间相关性、调用链和规模放大证据的项列为 P0；否则降为 P1/P2 或明确 `retrospectively_supported`。
2. 为每个 inference 写一个可执行 falsifier，并指出需要哪个 adapter 获取结果。
3. 给出最小干预层级：先阻止不应启动的工作，再批量/共享，再有界并发，最后才考虑回收。
4. 输出 `diagnosed` 或 `blocked`；把运行时 A/B 与 SLO 判定交给 `lov-runtime-verification`。
5. 将 `app-runtime-evidence/v1` JSON、资源图和假设列表作为实现或回收模块的独立输入。

## First-case calibration: Yoda

Yoda 只用于校准证据等级：`platform_family=desktop`、`runtime=electron`。详细记录见 `$KIT_DIR/cases/evidence/yoda-runtime-evidence.json`；以下数字不是其他 App 的默认规模、预算或 threshold。

- `measurement`：2026-08-09 的一次现场 inventory 在最大已挂载项目内清点到 916 条 task records（33 active、883 archived）；同日一次 canonical tmux server snapshot 清点到 61 个 sessions。两项都是有边界的单次清点；保留了审计日期但没有墙钟时刻，只能说明该现场规模，不能证明泄漏或因果。
- `code_fact`：历史实现的完成事件沿 resident-task 路径逐项处理，并进入 task 级 remote read。
- `inference`：`916 task records × 每 task 1 次 IPC ≈ 916 IPC`；`约 916 RPC × 每 RPC 2 次 Git remote 读取 ≈ 1,832 Git subprocess work items`。公式依赖源码路径和一次事件的假设，属于近似预测，不是 trace 计数。
- `measurement`：补丁后的下一次 8-remotes 同步用高频进程采样获得 600 个 samples，在约 4 秒窗口观察到 15 个 unique Git subprocess，peak concurrency 为 5。它只佐证放大方向已收敛；由于 before 是 inference、after 是后续 measurement，输入使用 `comparison.quality=directional`，报告不得生成精确 delta。
- `boundary`：15 不是 acceptance，也没有可迁移 threshold；本审计案例终态为 `diagnosed`。任何其他 App 都必须重新定义工作负载、sampler、SLO 与验收门槛。

## Dependencies

- 通过 App Optimizer Kit 调用；共享合同、脚本和 Profile 仅从 `$KIT_DIR` 解析。
- Python 3.9+ 仅用于确定性证据报告和 Profile 读取；共享脚本使用标准库。
- 目标源码、实际运行客户端与只读运行时数据；真机、浏览器、profiler 或平台工具按所选 adapter 提供。
- Git、tmux、SSH、SQLite、系统进程查询和设备调试工具均为可选 adapter，不是跨平台强制依赖。

## Shared references

- `$KIT_DIR/references/evidence-contract.md` — `app-runtime-evidence/v1`、provenance、comparison 与资源 verdict 契约。
- `$KIT_DIR/references/runtime-playbook.md` — 身份核验、采样、规模放大与因果复测方法。
- `$KIT_DIR/references/platform-adapters.md` — 桌面、移动、Web 及可选资源 adapter 的只读采样入口。
- `$KIT_DIR/references/reclamation-policy.md` — 仅在审计触及回收候选时读取的保护边界。
- `$KIT_DIR/references/user-profile.md` — 跨会话 Profile 的读取与持久化规则。
