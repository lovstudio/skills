# 运行态体检 · Runtime Checkup · Skill Card

## Description

为 Electron、Tauri、原生 iOS/Android、React Native、Flutter、Web/PWA 等客户端选择并组合只读 adapters，建立可复查基线、资源所有权图与扇出模型。默认不以“大量实体”“高内存”或一张 CPU/帧率截图直接宣判根因。

## Owner

维护方：LovStudio / 手工川工作室。联系入口随源码分发渠道提供。

## License

[MIT License](../../LICENSE)。允许使用、修改和再分发；运行时日志、设备数据、用户数据与远程系统访问仍由使用者负责授权和最小化处理。

## Use Case

面向维护桌面、移动端、跨平台或 Web/PWA 客户端的工程师、性能负责人和代码审查者。适用于输入变慢、掉帧、事件循环/线程拥堵、IPC/bridge/channel 扇出、后台反复唤醒、存储/网络重复工作或长运行资源增长。

先声明 `platform_family` 与 `runtime`，再按需组合 process、UI/frame、bridge/IPC、network、storage/database、scheduler/background 和 lifecycle adapters。跨层应用可组合多个 adapter；没有 authoritative source 的信号保持 `unknown`。

## Deployment Geography

全球。可在本地桌面环境、已连接真实移动设备/受控设备实验室，或已固定 deploy ref、浏览器和 profile 的 Web/PWA 环境运行。

## Requirements

- 仅通过 App Optimizer Kit 调用：`invocation: kit_only`。
- 实际 client build/deploy/device/browser identity、目标源码和可复现工作负载。
- 至少一个对目标 runtime 有效的只读 adapter；共享 adapter 目录见 [`$KIT_DIR/references/platform-adapters.md`](../../references/platform-adapters.md)。
- Python 3.9+，用于共享 Profile 与确定性证据报告。
- 默认不需要凭据；远程、真机或生产采样只接受使用者提供的最小只读权限。

## Known Risks

- 平台 proxy 可能被误写成目标 runtime 的直接测量。缓解：固定 platform/runtime/adapter 和 process/thread/page 边界，unsupported signals 保持 unknown。
- 派生调用数可能被误写成直接测量。缓解：严格区分四类证据，为 inference 记录 inputs、formula、assumptions、rounding 和 falsifier。
- 错误 build、设备、浏览器 profile、部署或工作负载会产生虚假对照。缓解：每条数字补 build/source ref、observed_at、workload ID、sampler 和窗口。
- 日志可能包含凭据、设备标识或用户内容。缓解：只保留最小元数据，不把 secrets、原始内容或现场标识写入报告与 Profile。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [App runtime evidence contract](../../references/evidence-contract.md)
- [Platform adapter catalog](../../references/platform-adapters.md)
- [Runtime audit and verification playbook](../../references/runtime-playbook.md)
- [Yoda first calibration case](cases/cases.json)

## Skill Output

输出 Markdown 审计包，并可同时输出 `app-runtime-evidence/v1` JSON。审计包包含 platform/runtime/adapter、实际运行身份、采样口径、资源图、放大公式、provenance、支持证据、falsifier、优先级和证据缺口。

审计终态只允许 `diagnosed` 或 `blocked`。实现状态与产品 SLO 判定属于后续模块。跨证据类型对照必须使用 `comparison.quality=directional`，不计算精确 delta 或百分比。

## Skill Version

0.2.0

## Ethical Considerations

采用只读和最小数据原则。未经授权不采集用户内容、不连接远端、不重启或切换 build、不终止会话、不删除资源；对 proxy、近似值、历史源码和证据缺口明确标注。

## User Cases

[Yoda 首案](cases/cases.json)固定为 `platform_family=desktop`、`runtime=electron`：

- 916 条 task records 是 2026-08-09 最大已挂载项目内的一次现场 inventory（33 active、883 archived）；61 个 tmux sessions 是同日 canonical server 的一次 snapshot。保留了审计日期但没有墙钟时刻，两者只说明当时有边界的规模。
- 约 916 IPC 与约 1,832 Git subprocess work items 来自源码乘法模型，属于 inference。
- 补丁后一次 8-remotes 同步在约 4 秒内采集 600 samples，观察到 15 个 unique Git subprocess，peak concurrency 为 5；这是后续 measurement，不是 acceptance。
- before inference 与 after measurement 只提供方向性佐证，输入使用 `comparison.quality=directional`，报告抑制精确 delta。Yoda 数字不是其他 App 的默认预算或 threshold。

## Dimension Map

| 维度 | 目标 | Evidence | Score status |
| --- | --- | --- | --- |
| 平台可迁移性 | 通用流程与目标 adapter 分离 | desktop/mobile/web × Electron/Tauri/native/RN/Flutter/browser/PWA 组合矩阵 | method_defined_single_case |
| 证据保真度 | 四类证据、边界与 provenance 不混用 | 916/61 inventory、约 916/1,832 inference、15 subsequent measurement 分开记录 | case_backed |
| 扇出覆盖度 | 事件到内部工作的乘法链可核对 | 通用公式覆盖 owners、resident entities、surfaces/subscribers 与 per-entity work | method_defined_single_case |
| 诊断安全性 | 默认只读，未知即降级 | 终态仅 diagnosed/blocked；案例不执行 kill、删除、reset 或未授权重启 | case_backed |

维度暂不赋分；当前只有 Yoda 一个校准案例，不声称跨平台 benchmark。

## Pricing Basis

[Pricing card](pricing-card.yaml)采用免费模型，定价为 CNY 0。范围包含 kit 内审计方法、组合式 adapter 选择、证据契约和共享本地脚本；不包含生产访问、专有 profiler、项目专属 adapter 实现、现场实施、托管服务或性能保证。

## Distribution

| Channel | Channel class | Current offer | Publication state |
| --- | --- | --- | --- |
| workbuddy | paid-capable marketplace | free；无付费 SKU、无渠道产物 | not_prepared |
| skillpay | paid-capable marketplace | free；无付费 SKU、无渠道产物 | not_prepared |
| github | source repository | free | source_ready_not_published |
| lovstudio | first-party catalog | free | local_ready |

WorkBuddy 与 SkillPay 当前没有付费 SKU，也没有渠道产物；GitHub 仅表示源码就绪但未声称发布；LovStudio 仅表示本地包就绪。
