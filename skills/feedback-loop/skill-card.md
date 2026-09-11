# Feedback Flywheel Skill Card

## Description

把用户对 Agent 的情绪与判断记成可统计的反馈事件，按最小作用域迭代规则，
并输出满意度复盘。

## Owner

LovStudio · https://lovstudio.ai

## License

MIT。源码与本地账本归使用者所有；报告摘录用户原话前必须去敏。

## Use Case

用户在完成任务后说了什么、语气如何、是否反复纠偏，都应当变成能回填结果的记录。
四个主动入口是评价、回扫、复盘与接入；自动链路由根 Prompt 规则驱动。

## Deployment Geography

全球；本地运行，默认不联网。

## Requirements

Python 3.8+ 标准库即可运行；`scripts/validate_skill.py` 需要 PyYAML。
无需任何凭据或外部服务。

## Known Risks

- 情绪误判产生噪音：被动信号必须带原话证据，低强度需形成模式。
- 原话泄漏隐私：证据截断并去敏，默认只写本地账本。
- 越权改规则：跨领域证据才允许改全局 Prompt，发布仍需显式授权。
- 接入覆盖他人配置：只写托管块，改动前备份。

## References

- `references/protocol.md` — 信号、强度、作用域与闭环协议
- `references/store-schema.md` — 事件与结果字段
- `references/host-adapters.md` — 宿主接入位置

## Skill Output

`feedback-event/v1` 与 `feedback-outcome/v1` 的 JSONL 记录，
Markdown、自包含 HTML、JSON 三种格式的满意度报告，以及宿主接入结果。

## Skill Version

0.3.0

## Ethical Considerations

情绪推断只服务于改进本机 Agent 表现；对外分享、训练上传或用于其他目的，
都需要用户显式授权。用户的原始表达在报告中使用前先去敏。

## User Cases

首个真实案例来自 2026-09-11 的 Codex 会话：用户要求把“情绪感知 + 主动 judge”
做成可迭代、可统计的机制。Kit 依此落地，并在同一天按用户判断收敛为单 Skill。

## Dimension Map

| 维度 | 判定问题 | 证据 |
| --- | --- | --- |
| 信号保真 | 判定是否贴合原话与语气 | 真实原话分别落账 negative/positive |
| 作用域纪律 | 是否选最窄层且编号稳定 | 根 Prompt 只追加 48–50 |
| 验证链 | 改动是否有回读证据 | 四个分发副本 SHA-256 回读 |
| 可统计性 | 能否支持趋势与时长统计 | stats 与 report 基于真实账本 |
| 接入安全 | 写入宿主前是否可预演 | dry-run 计划与 .bak 备份 |
| 收据克制 | 收据是否一行说完 | 固定三段事实模板 |

## Pricing Basis

免费：反馈闭环是基础设施能力；不包含云端同步、团队看板与托管服务。

## Distribution

免费渠道：GitHub、LovStudio 目录、本地安装。
