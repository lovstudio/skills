# Skill Card — lov-search-chat

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note.

## Description

从本机 Ataru 记忆索引里召回过去的 AI 会话上下文：先确认索引就绪，再按 turn / run /
session / project 粒度检索，返回带稳定标识的排序命中，并支持围绕任一命中读回一段
原始转录。输出经过投影与截断以便直接消费。

## Owner

Lovstudio（手工川工作室），https://lovstudio.ai

## License / Terms

MIT。自由使用、修改与再分发，保留版权与许可声明。本许可不覆盖 Ataru 本体。

## Use Case

面向在本机工作、需要用到自己过去 AI 会话记录的 Agent 与开发者。典型场景是当前问题
以前遇到过，结论散落在历史会话里，需要找回并引用，而不是凭印象重新推导。

## Deployment Geography

全球，纯本机执行。适用于已安装 Ataru 且索引已就绪的 macOS 机器，或同一仓库内的
本地 dev build。

## Requirements / Dependencies

无凭据。需要 Python 3.8+（仅标准库）、Ataru 0.41.3 或更新版本、已就绪的关键词索引，
以及索引目录与会话历史的本机读权限。

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 索引未就绪时返回零结果，会被误读为「历史里没有这件事」 | 检索前先读状态，未就绪报 `ATARU_INDEX_NOT_READY`、正在构建报 `ATARU_INDEX_BUILDING`，并指向 `lov-ataru-indexing` |
| 命令行只有关键词检索，同义表述会漏召 | 响应原样带出 `mode`、`requestedMode`、`semanticAvailable`，指示换词换粒度重试 |
| 原始响应可达数 MB，会挤掉真正要解决的问题 | 默认只输出投影字段并截断，完整响应需显式 `--full` |
| 旧版 Ataru 把 index 子命令当成桌面启动参数，打开窗口抢走前台 | 每个候选先跑 `--version`，低于 0.41.3 直接拒绝 |
| 项目 ID 以短横线开头，会被参数解析器当成另一个选项 | 解析前把已知取值选项改写成等号形式 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Skill group composition](references/skill-composition.md)

## Skill Output

stdout 上的单个 UTF-8 JSON 对象。`search` 返回 `query`、`level`、`mode`、`tookMs`、
`total` 与命中数组，每个命中含 `projectId`、`sessionId`、`messageId`、`lineNumber`、
`role`、`timestamp`、`snippet`；`read` 返回会话总消息数、实际返回数与按窗口切出的
消息正文。所有截断都标注剩余字符数。

## Skill Version

0.2.0

## Ethical Considerations

检索对象是用户本机完整的 AI 会话历史，可能包含凭据、私人信息与第三方内容。全程本地
执行，不上传任何消息内容；默认截断降低了敏感正文整段进入上下文的量。引用历史内容
必须给出可回溯的会话标识，不得把历史结论冒充为当前事实。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：在 2704 会话、847072 消息的真实本机语料上
完成一次跨工具召回，并用命中标识把原文读回。

### Dimension Map

机器可读卡记录了 correctness、honesty、transparency、efficiency 四个维度及其证据。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。作为 Ataru 检索内核的无界面外壳免费分发。

### Distribution

免费渠道：github、lovstudio。无付费渠道。
