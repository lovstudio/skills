---
name: lov-app-optimizer
description: >
  用真实运行时证据系统优化交互式应用的卡顿、耗电、内存增长、后台风暴与资源泄漏，覆盖 Electron、Tauri、原生桌面、iOS、Android、React Native、Flutter、Web/PWA；适用于“应用越用越卡”“后台任务和会话不释放”“请做同负载前后验收”，不用于单纯 Lighthouse、后端调优或盲目清理。
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - app-performance
    - runtime-observability
    - lifecycle
    - resource-reclamation
    - desktop
    - mobile
    - web
  compatibility: "Portable Agent Skills format; Python 3.9+ and access to the target source/runtime. Platform profilers, devices, browsers, Git, tmux and SSH are optional adapters."
  dependencies:
    - python
---

# 应用性能医生 · App Performance Doctor

把“应用总是很卡”变成一条可复查的工程证据链：先确认用户实际运行的构建、设备与工作负载，再定位无效工作、重复工作、无界工作和生命周期泄漏，最后用冻结的对照协议复测。核心方法不绑定框架；Electron/Yoda 是第一个完整案例，不是适用边界。

## Triggers

### Activate when

- 用户要求系统优化 Electron、Tauri、原生桌面、iOS、Android、React Native、Flutter 或 Web/PWA 应用的输入延迟、掉帧、卡顿、CPU、内存、耗电、启动、后台任务或长时运行退化。
- 用户要求追踪 IPC/bridge、DB、文件系统、网络、worker、sidecar、同步器、轮询、任务水合、缓存、PTY/tmux、Agent session、worktree 等运行时扇出或生命周期泄漏。
- 用户已有性能补丁，要求在相同设备、构建、数据规模和操作脚本下完成前后验收。
- The user asks for evidence-backed app runtime optimization, safe reclamation, or comparable before/after verification.

### Do not activate when

- 只是普通功能错误、UI 调色、可访问性或产品设计任务，没有运行时性能目标。
- 只要 Lighthouse/SEO、bundle 大小、图片压缩或静态资源建议；这些不是完整应用运行时审计。
- 目标只是后端、数据库服务器、云成本、CDN 或 API 延迟，客户端没有待验收的运行时症状。
- 只是打包、签名、发布、依赖升级、CI 或硬件/操作系统调优。
- 用户只想强杀全部进程、清空缓存或递归删除数据；使用专门清理流程并取得精确授权。
- 请求只有“优化一下代码”，没有具体应用、症状或可重放工作负载。

## Product contract

- 核对实际运行对象：源码/commit、构建模式、版本、设备或浏览器、OS、进程/线程/isolate/WebView/worker 边界、配置、数据规模与热状态。不能用另一个 checkout、模拟器或开发构建替代生产结论。
- 证据分为 `measurement`、`code_fact`、`inference`、`acceptance`。源码推导不是现场测量，测试通过不是性能验收，主观改善不是受控 A/B。
- 前测后冻结比较合同：同构建类型、设备/浏览器、网络与缓存条件、数据规模、操作脚本、采样器和时间窗口。不可比较时只给方向性结论。
- 至少覆盖四个轴：用户体验、运行时资源、内部工作量、规模因子。只看 CPU 或只看调用数都不足以证明用户体验改善。
- 优化顺序固定：停止不该发生的工作 → 批量/去重 → 限制并发与预算 → 按可见性/生命周期调度 → 最后才回收资源。
- 诊断默认只读。回收需证明 durable owner、activity、lease、resume path、instance fingerprint 与删除顺序；证据不足时 fail-closed。
- 不自动删除 dirty/unknown 数据，不误杀 attached/visible/working/awaiting/registration-active 资源，不把移动端系统挂起或 Web Service Worker 终止误当成可控常驻进程。
- 没有目标平台 adapter 或真实设备/运行时证据时，降低结论等级，不伪装成跨平台实测。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1` 上下文。优先级为：当前请求、项目上下文、本 Skill records、共享 preferences、共享 user/brand、保守默认值。

只有用户直接声明且明确希望长期沿用的性能预算、保留期或输出偏好，才可通过 `scripts/profile_store.py record --confirm` 写入 Profile。凭据、私人路径、设备标识、现场进程信息和推断结论不得持久化。完整约定见 `$KIT_DIR/references/user-profile.md`。

## Skill Kit modules

本 Kit 的嵌入模块只通过 controller pipeline 调用；Step 0 必须完整加载所选模块：

- `$SKILL_DIR/skills/runtime-audit/SKILL.md` — `lov-runtime-audit`：建立现场基线、运行时/资源图和可证伪根因排序。
- `$SKILL_DIR/skills/reclamation-engineering/SKILL.md` — `lov-reclamation-engineering`：设计并实现保守、竞态安全的平台生命周期与回收协议。
- `$SKILL_DIR/skills/runtime-verification/SKILL.md` — `lov-runtime-verification`：在冻结的真实工作负载上做前后对照与残余热点验收。

`kit.yaml` 定义 `optimize-runtime`、`audit-only`、`review-reclamation`、`verify-change` 四条流水线。

## Workflow (MANDATORY)

### Step 0: Resolve context, adapter, and pipeline

1. 解析 `SKILL_DIR` / `KIT_DIR`，读取 `kit.yaml`、`skill.yaml` 和 Profile。
2. 完整治理用 `optimize-runtime`；只诊断用 `audit-only`；审查生命周期/回收方案用 `review-reclamation`；已有补丁复测用 `verify-change`。
3. 读取 `$KIT_DIR/references/evidence-contract.md`、`$KIT_DIR/references/runtime-playbook.md` 和 `$KIT_DIR/references/platform-adapters.md`；涉及回收时再读 `$KIT_DIR/references/reclamation-policy.md`。
4. 选择 host adapter、runtime/framework adapter 与可选 resource adapter。unsupported adapter 必须记录为 evidence gap。
5. 记录授权边界。获准改代码不等于获准执行破坏性现场清理。

### Step 1: Freeze symptom, workload, SLO, and safety

定义一个可重放场景，并记录：

- 用户体验指标：input latency、frame/jank、long task、启动/导航耗时、ANR/hang 或交互吞吐；
- 运行时指标：CPU、event-loop/UI-thread lag、RSS/footprint、heap、energy、process/thread/isolate count；
- 内部工作量：IPC/bridge/query/fs/network/subprocess/worker/render 次数或字节量；
- 规模指标：records、views、sessions、jobs、projects、tabs、caches 或数据体量；
- 安全不变量：例如 dirty/unknown 永不自动删除，后台切换不丢工作。

在采样前冻结设备/浏览器、OS、构建类型、网络、温度/电量、缓存、数据规模、操作脚本、采样器和窗口。阈值必须来自产品预算或本轮明确声明，不能事后挑选。

### Step 2: Run `runtime-audit`

1. 核对真实版本与运行边界；区分 desktop host/WebView/sidecar、mobile UI/JS/native 线程、browser main/worker/service worker/frame。
2. 采集 idle foreground、idle background、典型交互和至少一个已知周期事件；记录时间戳和采样器开销。
3. 构造 ownership/work graph：surface → owner → runtime resource，以及 timer/event → subscribers → per-item work。
4. 量化放大：`event frequency × owners × resident entities × surfaces × per-item work`；检查全量 hydration、N+1 RPC/query、广播、重复扫描、无界并发和隐藏面板轮询。
5. 把事实写入 `app-runtime-evidence/v1`；报告器只归一化证据与评估候选，不执行清理。
6. 只有时间相关性、调用链和规模放大共同成立时才把假设升为 P0。

### Step 3: Reduce runtime work

按顺序选择最小完整 seam：

1. 停止不可见、过期或无 owner 的工作与自动复活；
2. 用批量查询、索引更新、共享 cache、single-flight 消除重复；
3. 给启动、停止、网络、磁盘、解析和子进程设并发/字节/时间/驻留预算；
4. 按 foreground/background、visible/hidden、active/inactive、online/offline 调整调度；
5. 将昂贵详情放到可见或显式操作之后。

### Step 4: Run `reclamation-engineering` when needed

1. 给每类资源定义 durable owner、runtime lease、authoritative activity、resume path、fingerprint 和 dependency order。
2. 将动作区分为 `scope_release`、`hibernate`、`cache_evict`、`external_reclaim`、`persistent_delete`；后两类需更强证据，持久删除绝不作为自动性能手段。
3. 使用两阶段批量 inventory/classify，并在动作前 O(1) 重验 live lease 与实例身份，或由服务端原子条件操作阻止 ABA。
4. archive/delete/close 流程按依赖顺序 await；终止未确认时保留 durable identity 以便重试。
5. 移动端遵守 suspend/process-death/background execution 规则；Web 遵守 BFCache、page lifecycle、tab discard 与 Service Worker 生命周期，不能套用桌面 kill 语义。

### Step 5: Implement and test the smallest complete change

- 每个变更同时覆盖 happy path、规模边界、生命周期迁移和失败关闭。
- 高危回收 seam 必测 same-name ABA、刚恢复、visible/attached/consumer/registration active、unknown/malformed evidence、timeout/transport failure、dirty/cwd-in-use 数据和并发 cleanup single-flight。
- 保留用户已有改动；不要用一次性清理脚本掩盖生命周期缺陷。

### Step 6: Run `runtime-verification`

1. 跑目标仓库要求的聚焦测试、静态门与完整 build/test；它们是正确性门，不是性能结果。
2. 确认真实运行的是补丁 build/commit。
3. 在冻结合同下复测用户体验、运行时资源、内部工作量和规模；记录样本数、窗口、均值/峰值/分位数。
4. Desktop 用真实 release/package；iOS/Android/React Native/Flutter 最终验收用真实设备 release/profile build；Web/PWA 分开报告实验室指标与 field/RUM，不能互相替代。
5. 回收策略先 dry-run inventory，再验证保护理由、真实 hibernate/resume/restore 和数据完整性；“删得更多”不是成功标准。

### Step 7: Report the outcome

先给结论，再报告：根因与放大公式、实施机制与安全不变量、同负载前后证据、正确性门、残余热点与 evidence gaps。

终态只能是：`diagnosed`、`implemented_not_runtime_verified`、`partially_verified`、`verified` 或 `blocked`。未达到预先声明的阈值时不能写 `verified`。

## Deterministic evidence helper

```bash
python3 "$SKILL_DIR/scripts/evidence_report.py" \
  --input evidence.json \
  --json-output runtime-report.json \
  --markdown-output runtime-report.md
```

当前输入为 `app-runtime-evidence/v1`，兼容读取旧 `electron-runtime-evidence/v1`，但始终输出 `app-runtime-report/v1` 并给出迁移警告。脚本不会杀进程、清缓存或删除文件。

## Dependencies

- Python 3.9+；证据报告器只使用标准库。
- 可读取的目标源码、实际运行时和项目测试命令。
- 平台 profiler、真机、浏览器 RUM、Git、tmux、SSH、SQLite 等按 adapter 选用，不是核心强依赖。

## References

- `$KIT_DIR/references/evidence-contract.md` — 跨平台证据、状态和报告契约。
- `$KIT_DIR/references/runtime-playbook.md` — 审计、降载与冻结对照方法。
- `$KIT_DIR/references/platform-adapters.md` — Electron/Tauri/native/mobile/Web 的测量与生命周期边界。
- `$KIT_DIR/references/reclamation-policy.md` — 所有权矩阵、动作分级、保护规则和竞态边界。
- `$KIT_DIR/cases/cases.json` — Yoda/Electron 的第一个完整真实案例。
