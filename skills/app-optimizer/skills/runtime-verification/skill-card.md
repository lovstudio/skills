# 性能实测 · Performance Verification · Skill Card

## Description

在真实 desktop build、移动真机或实际浏览器中复现同一工作负载，把内部工作量、运行时/体验指标、宿主生命周期、回归门和残余风险组成诚实的客户端 App before/after 验收。没有同负载体验 A/B 时，即使目标调用数下降也不写成整体 `verified`。

本模块覆盖 Electron、Tauri、macOS/Windows/Linux native desktop、iOS、Android、React Native、Flutter、Web 和 PWA；框架、native host、设备/浏览器与 build identity 分开记录。

## Owner

维护方：LovStudio / 手工川工作室。联系入口随源码分发渠道提供。

## License

[MIT License](../../LICENSE)。允许使用、修改和再分发；性能结果只对记录的 build、设备/浏览器、数据规模、工作负载与采样口径负责。

## Use Case

面向需要验收客户端 App 性能、hydration、IPC/bridge/network 批量化、轮询降载、缓存或资源生命周期修复的工程师与发布负责人。补丁和门禁已存在时，本 Skill 在实际 build/device/browser 及相关宿主生命周期中选择 `verified`、`partially_verified`、`implemented_not_runtime_verified` 或 `blocked`。

## Deployment Geography

全球；在实际 Electron/Tauri/native desktop build、安装目标签名产物的物理 iOS/Android 设备（含 React Native/Flutter），或加载真实 deployment 的指定浏览器/PWA standalone 环境运行。

## Requirements

- `invocation: kit_only`；共享依赖从 `$KIT_DIR` 解析，不能把本模块当作完整 standalone 包。
- 可比 baseline、实际 patched artifact/deployment、可复现 workload、数据规模、sampler 与目标 lifecycle seams。
- 目标仓库完整门禁，以及对应平台的 build、签名、安装或 deployment 命令。
- Python 3.9+，用于共享 Profile 与证据归一化。
- 生产、远端或设备服务只使用使用者提供的最小权限。

## Known Risks

- 不同 build、设备/浏览器、规模、热状态或窗口会产生虚假 A/B。缓解：采样前冻结完整 target identity 与比较矩阵。
- 测试、构建、安装成功或调用数下降可能被误写成体验改善。缓解：分开报告 correctness gates、internal work 和 runtime/user metric。
- inventory × code path 可能被误写成 TaskStore、内存或进程 telemetry。缓解：标成 code-derived upper bound，使用 `comparison.quality=directional`，不计算精确下降率。
- simulator、emulator 或 headless 结果可能被冒充真实宿主证据。缓解：它们只作为补充门禁，真实结论绑定实际 device/browser。
- 修复可能破坏 deep link、前后台恢复、进程重建、service worker 更新或离线数据。缓解：按平台验证 host lifecycle 与 resume/restore。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Runtime audit and verification playbook](../../references/runtime-playbook.md)
- [Runtime evidence contract](../../references/evidence-contract.md)
- [Platform adapters](../../references/platform-adapters.md)
- [Yoda runtime verification case](cases/cases.json)

## Skill Output

输出 Markdown 与可选 `app-runtime-evidence/v1` JSON 验收包，包括 platform/runtime/host/build identity、比较矩阵、provenance、完整门禁、内部工作量、runtime/user metric、宿主生命周期、恢复语义、不可比项、残余热点和终态。只有同口径 runtime measurements 才生成数值 delta；旧 `electron-runtime-evidence/v1` 只作为兼容输入迁移。

## Skill Version

0.2.0

## Ethical Considerations

不篡改采样口径、不选择性隐藏失败、不把局部收益包装成整体性能承诺。采样设备、浏览器或用户环境时只收集最小指标，并遵守远端、生产和设备访问授权。

## User Cases

[Yoda post-fix 首案](cases/cases.json)明确标记 `platform_family=desktop`、`runtime=electron`：

- 8 remotes 周期中观察到 15 个 unique Git subprocess；这是 600 个高频样本、约 4 秒窗口内的 `measurement`，不是 acceptance。
- 916 条总 task records 与 33 条 active records，结合全量/active-only hydration 代码路径，只支持初始 hydration eligibility 上界 916→33。它不是 resident `TaskStore` telemetry，不计算精确下降率。
- 完整门禁包含 3,115 tests；它属于 correctness gate，不替代 live 用户体验 A/B。
- 缺少正式同负载、同 build mode、同窗口和同 sampler 的 inputLatency/RSS before/after，因此整体保持 `partially_verified`。

## Dimension Map

| 维度 | 目标 | Evidence | Score status |
| --- | --- | --- | --- |
| 真实目标保真度 | build、设备/浏览器和 host boundary 可追溯 | 首案只声明 desktop/electron，不冒充其他平台证据 | case_backed |
| 对照可比性 | workload/scale/build/host/window/sampler 一致 | 缺 inputLatency/RSS 同负载 A/B，阻止 verified | case_backed |
| 证据语义保真 | measurement、bound、gate、gap 独立 | 15 为 measurement；916→33 为 code-derived bound；3,115 为 correctness gate | case_backed |
| 宿主生命周期覆盖 | desktop/mobile/web 的相关 lifecycle seam 被真实重放 | contract 定义真实 host 门；首案不产生跨平台量化分数 | method_defined |
| 结论诚实度 | 最弱关键证据约束终态 | Yoda 明确保留 partially_verified 与下一项 A/B | case_backed |

分数保持 `null`；`case_backed` 表示有首案证据，`method_defined` 表示已有验证契约但尚无跨平台 benchmark。

## Pricing Basis

[Pricing card](pricing-card.yaml)采用免费模型，定价为 CNY 0。范围包含跨平台比较契约、共享证据归一化和本地报告方法，不包含持续生产监控、设备实验室、托管 CI 或性能 SLA。

## Distribution

| Channel | Channel class | Current offer | Publication state |
| --- | --- | --- | --- |
| workbuddy | paid-capable marketplace | free；无付费 SKU、无渠道产物 | not_prepared |
| skillpay | paid-capable marketplace | free；无付费 SKU、无渠道产物 | not_prepared |
| github | source repository | free | source_ready_not_published |
| lovstudio | source catalog | free | local_ready |

没有渠道被描述为 live，也没有付费 SKU 或付费分发产物。
