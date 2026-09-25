# Codex Provider 修复 · Codex Provider Repair · Skill Card

本卡片与 `skill-card.yaml` 对应，是发布记录，不是实现笔记。评审者不打开源码也应能
理解用途、依赖、风险与验证边界。

## Description

对比 Codex 配置中已定义的 provider 与会话里持久化的 provider，定位桌面 App 会话打不开
的 `invalid_config` 故障，并给出补定义或带备份重打标签的修复路径。

## Owner

LovStudio，联系 mark@lovstudio.ai。

## License / Terms

MIT。本地诊断与修复；写操作必须先备份并显式确认；不含远程发布。

## Use Case

同时使用 Codex 桌面 App 与 Yoda 等集成入口的用户：集成建出的历史会话在桌面 App 里
打不开，报 `Model provider ... not found`，需要在不丢历史的前提下恢复可打开状态。

## Deployment Geography

global。主要面向 macOS 本地 Codex 目录与桌面 App 日志；其他平台需显式传入
`--desktop-log-root`，或只使用配置与索引证据。

## Requirements / Dependencies

- Python 3.8+ 标准库，无网络、无凭据。
- 可读的 `~/.codex/config.toml`、`state_5.sqlite`、`logs_2.sqlite`。
- 可选：`~/Library/Logs/com.openai.codex` 桌面日志，用于 resume 失败计数。

## Known Risks and Mitigations

- 桌面 App 运行中写入索引库：检测到 Codex 或 app-server 进程时拒绝写入。
- 误改仍在使用的共享 provider 桶：对 `yoda`、`custom` 优先补定义而非重打标签。
- 只改索引不改 rollout：默认同时改写 rollout 首行并抽样回读。
- 凭据泄露：脚本不读取、不打印凭据值，生成的片段只给 `env_key` 或占位符。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [机制与真实证据](references/mechanism.md)
- [修复手册](references/repair.md)

## Skill Output

只读诊断报告（终端表格或 JSON）、修复计划与命令、备份与回滚记录。校验点：7 个端到端
单元测试；对真实 `state_5.sqlite` 冷副本完成修复与回滚验证。

## Skill Version

0.1.0

## Ethical Considerations

只在本机读取配置、索引与会话日志；不打印凭据值；写操作先备份并需要显式确认；诊断报告
可能包含会话标题，外发前应自行检查。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：用户要求修复 `codex://threads/01a057eb-...`
（外滩大会发言稿会话），修复后 `thread/resume` 由 `-32600` 变为成功返回该 thread。

### Dimension Map

四个维度（取证正确性、修复有效性、可回滚性、扫描效率）的说明、证据与分数见
`skill-card.yaml` 的 `dimensions`。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)：免费，理由是纯本地诊断与可回滚修复，
无外部服务成本。

### Distribution

付费渠道 `workbuddy`、`skillpay` 计划中；免费渠道 `github` 本地源就绪尚未推送，
`lovstudio` 尚未上架。
