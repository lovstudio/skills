---
name: lov-runtime-verification
description: >
  Verify client runtime fixes on actual desktop builds, physical iOS/Android devices,
  React Native/Flutter hosts, and deployed Web/PWA browsers with comparable workloads
  and lifecycle checks.
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  invocation: kit_only
  tags:
    - app-runtime-verification
    - performance-acceptance
    - real-device
    - browser-lifecycle
    - before-after
    - regression-gates
  compatibility: "Kit-only Portable Agent Skill for Electron, Tauri, native desktop, iOS, Android, React Native, Flutter, Web, and PWA targets; requires the shared $KIT_DIR contracts and an actual runnable build, device, or browser target."
  dependencies:
    - python
---

# 性能实测 · Performance Verification

验证具体客户端 App 的修复是否在真实宿主链路中减少了目标工作，同时保留正确性、恢复语义和用户体验。把源码边界、项目门禁、内部工作量、运行时指标、用户体验和宿主生命周期分别报告；缺少同负载前后对照时诚实停在较低终态。

## Triggers

### Activate when

- 用户说“帮我验证这个客户端性能修复是否真的生效”“在真机上复测后台恢复”“确认 Web/PWA 修复在真实浏览器生命周期中有效”。
- 用户要求验收 IPC/RPC 批量化、lazy hydration、轮询降载、缓存、进程/线程、内存、终端/session 回收或宿主生命周期修复。
- The user asks to verify a runtime fix on an actual Electron/Tauri/native desktop build, iOS/Android device, React Native/Flutter app, or deployed Web/PWA in a real browser.

### Do not activate when

- 用户还没有修复、基线或可复现工作负载；先调用 `lov-runtime-audit` 建立证据。
- 用户只要求跑一次单测、lint、编译或 Lighthouse，不要求真实 runtime 因果验收；使用项目原生校验流程或对应专项工具。
- The request only predicts performance from source, benchmarks hardware, or treats a simulator screenshot as proof of a physical-device lifecycle claim.

## Invocation and shared dependencies

- `invocation: kit_only`。本模块不能作为自带全部依赖的 standalone Skill 调用。
- `KIT_DIR` 必须解析为含 `kit.yaml` 的 App Optimizer Kit 根目录；`SKILL_DIR` 只指当前 `skills/runtime-verification` 模块。
- 共享契约和脚本一律从 `$KIT_DIR/references/*` 与 `$KIT_DIR/scripts/*` 读取，不复制、不猜测本地替代物。
- 至少需要 `$KIT_DIR/references/evidence-contract.md`、`$KIT_DIR/references/runtime-playbook.md`、`$KIT_DIR/references/platform-adapters.md`、`$KIT_DIR/scripts/evidence_report.py` 和 `$KIT_DIR/scripts/profile_store.py`；缺失时输出 `blocked` 并列出缺口。
- 机器可读证据使用 `app-runtime-evidence/v1`；旧的 Electron 专用 schema 只能作为待迁移输入，不能作为新报告格式。

## Kit-only I/O contract

### Inputs

要求至少提供或现场解析：

- `platform_family`、`runtime`、App/version/build/commit、构建模式和发布渠道；框架与宿主分开记录，例如 `mobile + react-native + ios`、`mobile + flutter + android`。
- baseline 的 metric definition、unit、process/thread/page boundary、workload、scale、sample window、sampler 与 provenance。
- 包含修复的真实产物及宿主：正在运行的 desktop build、安装到目标物理设备的 mobile build，或实际部署并由指定浏览器加载的 Web/PWA URL。
- 可复现触发事件与预先声明的阈值，至少覆盖一个用户体验指标和一个内部工作量或运行时指标。
- 项目要求的 format/lint/typecheck/test/build、平台签名/安装门禁，以及修复相关的 lifecycle、resume/restore 与数据保护不变量。

只有补丁和测试、没有实际 patched runtime 时，最高只能是 `implemented_not_runtime_verified`。已有部分真实运行证据但关键体验 A/B、目标生命周期或生产观察缺失时，最高只能是 `partially_verified`。

### Outputs

必须交付一个验收包，至少包含：

1. `app-runtime-evidence/v1` scope，含 platform family、framework/runtime、OS、hardware/browser、build identity 与宿主模式；
2. before/after 比较矩阵、provenance 和不可比项；
3. 项目门禁、构建、签名、安装/部署与实际启动结果；
4. 同一触发事件下的 IPC/network/DB/fs/subprocess/thread/resource 或 JS/native bridge 工作量；
5. input latency、frame/jank、long task、event-loop/run-loop、CPU、RSS/footprint 或 energy 中至少一项用户/运行时结果；
6. 相关宿主生命周期的冷/热启动、前后台、隐藏/恢复、进程重建、更新或离线恢复结果；
7. residual hotspots、下一项判别性测量和唯一终态。

测试数量、编译成功、安装成功、页面可打开或一次低 CPU 截图都不能单独构成性能验收。

## Platform and host contract

| Platform family | Runtime examples | Actual target required | Lifecycle seams to select from |
| --- | --- | --- | --- |
| `desktop` | Electron、Tauri、macOS/Windows/Linux native | 实际 dev/package build，核对 executable、process tree、cwd/version/commit；含 WebView 时同时固定 engine 版本 | cold/warm launch、window create/hide/show/close/reopen、background、sleep/wake、crash/relaunch、update |
| `mobile` | iOS/Android native、React Native、Flutter | 签名产物安装到目标物理设备，记录 device model、OS、artifact/build、native host 与 JS/Dart engine | install/upgrade、foreground/background、suspend/resume、memory pressure、OS process death、relaunch、offline/online |
| `web` | 浏览器 Web App、PWA | 实际 deployed URL、浏览器/version/profile、deployment/build ID；PWA 还需固定 service worker 与 install mode | cold/warm navigation、route change、visible/hidden/frozen/restored、service-worker install/activate/update、cache cold/warm、offline/online、browser restart |

只测试与修复相关且预先声明的 seams，但不得用模拟器、headless-only 结果或另一个浏览器替代声称覆盖的真实 device/browser。模拟器、emulator 和 headless browser 可以作为补充回归门，必须单独标注。

## Acceptance and evidence rules

- 每条证据记录 build/source ref、observed time、workload ID、sample window、sampler、process/page/device boundary 与原始 artifact；缺失字段明确写为 evidence gap。
- 只有 metric ID、unit、aggregation、boundary、workload、scale、build mode、window 和 sampler 足够一致时，才计算 before/after delta。
- 源码推导或 inventory × code path 得到的是 `inference` / code-derived upper bound；与 runtime telemetry 对照时使用 `comparison.quality=directional`。只有两侧都是同定义的精确配置边界时才使用 `implementation_bound`。
- 运行时计数是 `measurement`。只有与预先声明阈值和可比 baseline 配对后，才可另立 `acceptance` 记录。
- test count、format/lint/typecheck/build、签名、安装和 smoke flow 放入 `verification_gates`，不放入性能 observation。
- 对内部工作量修复同时验证 user/runtime metric；只有一侧改善时保留替代解释。
- 对 hydration/cache 修复验证显式加载、deep link、刷新、离线与状态重建；对 reclamation 修复验证 protected reasons、teardown 和 resume。
- 对 React Native/Flutter 同时标明 JS/Dart 与 native host 边界；对 Electron/Tauri 标明 renderer/WebView 与 native/main 边界；对 Web/PWA 标明 page、worker 与 browser process 边界。

## User Profile contract

每次调用先读取 `skill.yaml` 声明的 `user-profile/v1`。按“当前验收请求 → 本次 baseline 与 patched target → `skills.lov-runtime-verification.records` → shared preferences → shared user/brand → 无通过结论的保守默认值”解析冲突。

只有用户直接声明并要求跨会话沿用的 acceptance budget、reference workload 或 report detail，才可通过 `$KIT_DIR/scripts/profile_store.py` 写入 `records.<field>`。写入必须带 `--confirm` 并回报 profile path。不得持久化现场 PID、设备标识、私有路径、遥测原文、凭据、临时 commit 或未经确认的阈值。完整契约见 `$KIT_DIR/references/user-profile.md`。

## Workflow (MANDATORY)

**必须按顺序执行；先冻结身份、比较与生命周期契约，再采集 after，不得事后改口径迎合结果。**

### Step 0: Resolve the kit and target

1. 解析 `KIT_DIR` 与 `SKILL_DIR`，读取共享 evidence contract、runtime playbook 与 `$KIT_DIR/references/platform-adapters.md`；涉及资源回收时再读取 reclamation policy。
2. 验证共享 evidence/profile 脚本可读，读取 `lov-runtime-verification` Profile。
3. 记录 `platform_family`、`runtime`、native host/engine、目标 OS/hardware/browser、artifact/deployment 与权限。
4. 列出 baseline、build/device/browser、workload、sampler 与生命周期缺口，并提前声明最高可能终态。

### Step 1: Freeze the comparison matrix

对每个指标预先写明：

1. metric ID、kind、unit、aggregation、process/thread/page boundary；
2. build mode、data/content scale、projects/items/accounts/tabs/sessions 等规模；
3. 用户动作或周期事件、warm-up、sample count、cadence、window；
4. source/sampler、before 值、threshold、threshold source、falsifier 与 noise budget；
5. 机器输入的 comparison quality 只能是 `paired`、`implementation_bound` 或 `directional`；报告器再生成对应的 `paired_observation`、`implementation_bound` 或 `directional_evidence`，异质证据使用 `directional`。

不满足同口径的指标标为 contextual，不生成百分比。

### Step 2: Run correctness and build gates

1. 先跑修改 seam 的 focused tests，覆盖成功、失败和竞态路径。
2. 按目标仓库规定串行运行完整门禁，不自行删减硬门。
3. 生成目标 artifact；记录命令、commit/build ID、exit status、test count、skipped/failed、签名或部署结果。
4. 把这些结果写入 `verification_gates`，不得写成 runtime acceptance。

### Step 3: Pin the actual runtime target

1. Desktop：启动目标 build，核对 executable、PID/process tree、cwd、version/commit、WebView/engine 与 build mode。
2. iOS/Android/RN/Flutter：把目标 artifact 安装到物理设备并启动，核对 bundle/application ID、version/build、device/OS、native host 与 JS/Dart engine。
3. Web/PWA：打开目标 deployed URL，核对 deployment/build ID、browser/version/profile、service worker、cache 与 install/standalone mode。
4. 证明目标含补丁；仍指向旧 checkout、旧 binary、旧 bundle、旧 deployment 或旧 service worker 时停止采样并修正。

### Step 4: Replay workload and host lifecycle

1. 恢复 baseline 的数据规模、账号、网络、权限、窗口/tab、设备状态与可控后台条件。
2. 使用相同 sampler、cadence、window、warm-up 与 aggregation 重放用户动作和至少一个相关周期事件。
3. 按 platform contract 重放本次修复相关生命周期，例如 window reopen、background/resume、OS process death/relaunch 或 service-worker update。
4. 同时采集目标内部工作量和至少一项 user/runtime 指标；保留原始 timestamp、sample count 与 artifact ref。

### Step 5: Triangulate causality

1. 将 work reduction 与 input latency、frame/jank、long task、event-loop/run-loop、CPU、memory 或 energy 至少一项相连。
2. 检查改善是否出现在同一事件与生命周期窗口，而非不同 scheduler、thermal、network 或 cache phase。
3. 比较源码预测、runtime measurement 和用户可见结果；冲突时保留假设，不挑选单一有利指标。
4. 用 `$KIT_DIR/scripts/evidence_report.py` 归一化证据；异质 evidence 只写方向性支持，不计算虚假精确 delta。

### Step 6: Verify safety and regressions

1. 验证 lazy/batched/cached 实体仍能 point lookup、deep link、显式打开、刷新与实时更新。
2. 验证持久状态、离线数据、账号、权限、dirty/unknown 资源和失败重试仍受保护。
3. 验证 teardown、background/resume、process recreation、browser reload/update 后 identity 与 state 不重复、不丢失、不错误复活。
4. 若生命周期变更涉及 cleanup，验证 changed identity、concurrent cleanup 和 transport failure 仍 fail-closed。

### Step 7: Assign the terminal status

- `verified`：真实目标上，同负载 user/runtime 与 internal-work 指标达到预设阈值，正确性和相关宿主生命周期门均通过。
- `partially_verified`：真实目标已有关键方向证据，但体验 A/B、目标生命周期、production observation 或另一热点仍缺失。
- `implemented_not_runtime_verified`：代码和门禁通过，但没有可比 live before/after。
- `blocked`：无法确认 patched build/device/browser、baseline、权限或权威 sampler。

先给结论，再列通过证据、不可比项、残余风险和下一项最有判别力的测量。

## Evidence calibration: Yoda

Yoda 只是首个校准案例，不是其他 App 的默认规模或阈值：

- identity：`platform_family=desktop`，`runtime=electron`，目标为 Yoda desktop。
- `measurement`：8 remotes 的一个 post-fix 周期内，600 个高频进程样本观察到 15 个 unique Git subprocess；窗口约 4 秒，peak concurrency 为 5。它是运行时测量，不是 acceptance。
- `code-derived upper bound`：inventory 显示 916 条 task records、其中 33 条 active；结合修复前全量与修复后 active-only hydration 代码路径，只能推导初始 hydration eligibility 上界从 916 收敛到 33。它不是 resident `TaskStore` telemetry，输入使用 `comparison.quality=directional`，报告不计算精确下降率。
- `verification gate`：完整门禁含 3,115 tests；它证明 correctness，不证明用户体验或 runtime 性能。
- `evidence gap`：没有正式的同负载、同 build mode、同窗口和同 sampler inputLatency/RSS before/after A/B。
- verdict：扇出与 active-only hydration 获得方向性支持，整体保持 `partially_verified`。下一项测量是在相同 8-remotes 周期和稳定 build 上补齐 inputLatency、event-loop 与 main/renderer RSS A/B。

## Dependencies

- App Optimizer Kit 的共享 `$KIT_DIR` contracts、Profile helper 与 evidence reporter。
- 实际 patched desktop build、物理 iOS/Android 设备上的目标 artifact，或部署到真实浏览器的 Web/PWA。
- 可比 baseline、可复现 workload 与目标项目完整门禁。
- Git、platform profiler、device tools、browser tooling、tmux、SSH 或数据库 adapter 按验收矩阵启用，不是所有平台的统一强依赖。

## Shared references

- `$KIT_DIR/references/evidence-contract.md` — `app-runtime-evidence/v1`、provenance、comparison 与 observation 契约。
- `$KIT_DIR/references/runtime-playbook.md` — 跨 desktop/mobile/web 的身份核验、同负载复测和终态规则。
- `$KIT_DIR/references/platform-adapters.md` — Electron/Tauri/native desktop、iOS/Android/RN/Flutter 与 Web/PWA 的采样和宿主 adapter。
- `$KIT_DIR/references/reclamation-policy.md` — lifecycle 回收变更的保护与恢复边界。
- `$KIT_DIR/references/user-profile.md` — Profile 读取与持久化规则。
