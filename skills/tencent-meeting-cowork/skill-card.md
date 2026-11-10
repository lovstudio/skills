# 腾讯会议工作搭子 · Tencent Meeting Cowork · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note.

## Description

给定一个腾讯会议元宝笔记的分享链接，用一次不带登录态的请求读取页面，整理出带编号的摘要要点、
图文卡片、待办与会中实时笔记，把 AI 的转述与解读分开，再由 Agent 交付会后行动简报、会议速览、
用户答应的材料和跟进消息草稿。只起草，不发送。

## Owner

Lovstudio（https://lovstudio.ai）。

## License / Terms

源码按 MIT 许可提供。读取的是用户自己持有的分享链接所指向的纪要；纪要内容、其中第三方的信息
以及草稿的使用责任由用户承担。

## Use Case

- 受众：用腾讯会议谈合作、对需求、做复盘的个人，例如创业者、顾问、销售、项目负责人。
- 输入：一个元宝笔记分享链接，或该页面另存的 HTML；可选用户在会议里显示的名字、跟进对象与语气。
- 任务：brief（会后行动简报）、catch-up（会议速览）、work（把答应的材料做出来）、
  follow-up（会后跟进消息）。

## Deployment Geography

全球可用。脚本运行在用户本机，除读取分享页的一次请求外不联网；纪要内容会进入用户所用 Agent
宿主的对话上下文，由该宿主的数据政策约束。

## Requirements / Dependencies

- Python 3.9+，仅标准库；校验源码时需要 PyYAML。
- 能访问 `meeting.tencent.com`。
- 声明依赖：`lov-branding-consistency`。
- 无需账号、Cookie 或 API Key。

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 纪要里写错的人名、机构名或数字被当成事实 | 对外使用前逐个核对；列出只在实时笔记里出现的数字；三处冲突时并列并标为待核对 |
| AI 的评论被当成对方的话 | 脚本把转述与解读拆开；规则禁止解读进入对外文字 |
| 摘要漏掉要求、数字或后段的结论 | 每种模式先做三处对齐，逐条读实时笔记 |
| 认错“我” | 名字来自请求或 Profile；对不上时不退回笔记归属人；按归属人推定时写明假设 |
| 草稿替用户承诺 | 承诺类内容只能来自用户确认、本人材料或 Profile，其余写成待确认 |
| 会议内容或内部标识泄露 | 账号标识与会议号不进输出；0700 私有目录；`clean` 只删带标记的目录 |
| 纪要里夹带的指令被执行 | `notes.md` 开头声明内容是数据；规则明确不执行 |
| 页面改版、链接失效或需要登录 | 明确的错误码与下一步；只访问腾讯会议的 https 地址，不处理登录 |
| 自动发送或写入外部系统 | 没有任何发送或写入能力，最多放进剪贴板 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Context builder contract](references/context-contract.md)
- [Cowork mode playbooks](references/cowork-playbooks.md)
- [Authorship integrity](references/authorship-integrity.md)
- [Skill group composition](references/skill-composition.md)

## Skill Output

- 类型：会后行动简报、会议速览、需求单与工作成果、跟进消息草稿（未发送）。
- 格式：对话中的 Markdown 与可复制代码块；私有临时目录中的 `notes.md` 与 `context.json`
  （`lov-tencent-meeting-cowork/v1`）。
- 参数：`--url` / `--html`、`--self-name`、`--out`、`--timeout`。
- 校验：`scripts/test_meeting_context.py`（25 项，不联网）、`scripts/validate_skill.py`、真实分享页
  回归（内部标识计数为 0，联网读取与另存页面读取结果一致）。

## Skill Version

0.1.0

## Ethical Considerations

纪要里有其他参会人的发言与立场。本 Skill 只在完成会后工作所需的范围内引用，不对任何人做人品
或动机判断，不把 AI 的评论当成他们的话，也不替用户编造经历、立场或承诺。读取范围限于用户
自己持有的分享链接，不绕过登录或访问控制。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json)：从一场商务会议的元宝笔记里理出会后要做的事（已脱敏）。

### Dimension Map

纪要还原准确、能找出摘要漏掉的事、上下文准备耗时、隐私与不越权四个维度，证据见
`skill-card.yaml`；分数尚未评定（null）。

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml)：免费入口，0 Credits，2026-11-10 由作者确认。可比对象是
同系列的微信工作搭子（付费）；本 Skill 没有付费的上游依赖，证据只有一场真实会议，先以免费入口
积累使用证据。

### Distribution

| 渠道 | 类型 | 状态 |
| --- | --- | --- |
| 本地安装 | local | 已安装并校验 |
| lovstudio | free | pending（定为免费入口，目录条目待合入，线上状态尚未核验） |
| github | source | private-source（公开副本是聚合仓库 `lovstudio/skills` 的镜像） |
| workbuddy | — | 未发布，未选择 |
| skillpay | — | 未发布，未选择 |
