# Skill Card — lov-do-they-love-me

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把两个人的微信私聊做成有证据的恋爱指数分析：量化互动节奏，用本地模型把消息分成
工作／情感／生活三类，再产出一张手机竖版信息图，并给出每项结论的口径与误差。

## Owner

Lovstudio.AI（手工川）。

## License / Terms

MIT。仅用于分析使用者本人有权读取的聊天记录；不得用于跟踪、骚扰或评价第三方；
交付物中不得包含账号、数据库路径与联系方式。

## Use Case

读者是当事人本人。输入是本机微信私聊导出；期望结果不是一句安慰，而是一份可核查的
关系结构：谁在推进、聊的到底是什么、热度里有多少是工作。

## Deployment Geography

本地桌面（macOS），全球可用；语义标注默认走本机模型，不依赖境外服务。

## Requirements / Dependencies

无凭据。Python 3.9+、Playwright for Python、本地 Ollama 模型；可选上游
`lov-wdb-cli`（取数）与下游 `lov-mobile-infographic`（成卡）。

## Known Risks and Mitigations

- 把工作内容算成情感热度 → 先做语义分层，工作类单独统计并写在卡面。
- 把自定义指数当成情绪测量 → 指数公式固定并公开，命名限定为活动度／构成。
- 第三方私人聊天外泄 → 默认本地模型与本地落盘；外发模型、公开渠道与长段引用先取得授权。
- 对第三方下人格判决 → 结论只指向可核查行为，并同时给出反证。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

互动量化（`metrics.json`、`matrix.json`）、语义构成（`labels.jsonl`、`accuracy.json`、
`composition.json`）、三张 SVG 图形，以及下游渲染的手机竖版卡片（`card.html`、
`card.png`、`card.audit.json`）。参数：时间窗、对象、语义模型、卡片比例（默认 `long`）。
校验：语义必须过手工校准阈值、卡片必须过 `--strict` 审计、图形必须过几何复核。

## Skill Version

0.2.0

## Ethical Considerations

处理的是第三方私人对话，默认只在本机分析与交付给本人；不得用于跟踪、骚扰、
职场或家庭胁迫；不得输出对他人人格与感情的判决句；涉及自伤或胁迫时停止娱乐化表达，
改为提示真实求助渠道。聊天原文属于当事人，引用只保留短标注并自动剔除联系方式。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free Skills still explain their value,
boundary, and review trigger.

### Distribution

Keep paid channels (`workbuddy`, `skillpay`) and free channels (`github`, `lovstudio`)
explicit. A planned or unavailable channel must not be described as live.
