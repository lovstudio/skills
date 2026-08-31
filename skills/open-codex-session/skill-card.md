# Skill Card — lov-open-codex-session

## Description

接受 Codex thread UUID、deeplink 或已确认的 sessionId，在当前 Codex 主窗口打开准确任务，并以宿主返回的 `navigated: true` 验收。

## Owner

LovStudio Skills；联系入口：https://lovstudio.ai

## License / Terms

MIT。宿主应用及第三方服务继续受各自条款约束。

## Use Case

面向需要从搜索结果、任务列表或 deeplink 回到指定 Codex 任务的本地用户。输入必须能解析为唯一 thread ID，输出是当前主窗口进入该任务。

## Deployment Geography

本地 Codex desktop；没有地域限制，也不上传转录。

## Requirements / Dependencies

- Codex desktop 的任务导航能力。
- Python 3.8+，仅用于共享 Profile。
- 无凭据要求；`lov-search-chat` 只是缺少明确 ID 时的可选上游。

## Known Risks and Mitigations

- 相似关键词可能指向多个任务：必须先消歧并确认唯一稳定 ID。
- 宿主工具缺失可能诱发假成功：不使用 shell、浏览器或 Computer Use 冒充导航成功。
- 归档任务可能被误认为需要恢复：打开不修改归档状态，恢复必须另行明确请求。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Skill composition](references/skill-composition.md)

## Skill Output

输出是 Codex desktop 的任务导航结果和简短确认。核心参数为 `threadId`；验收要求目标唯一且宿主返回 `navigated: true`。

## Skill Version

0.1.0

## Ethical Considerations

只导航到用户本机可访问的任务；不持久化 thread ID 或转录，不生成分享页，不绕过访问控制。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录了真实的“微信读书投稿会话 → 成功导航”案例。

### Dimension Map

- 目标正确性：先确认唯一 sessionId。
- 运行验收：真实宿主返回 `navigated: true`。
- 范围安全：没有取消归档、发送消息或创建任务。

三个维度当前均为单案例验证状态，不外推为批量成功率。

### Pricing Basis

免费。本地基础导航不产生外部模型或服务成本；边界和复评条件见 [`pricing-card.yaml`](pricing-card.yaml)。

### Distribution

免费渠道：GitHub、LovStudio。WorkBuddy 与 SkillPay 不在本次发布范围内。
