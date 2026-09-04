# Skill Card — lov-publish-event-onto-hdx

This human-readable card mirrors `skill-card.yaml`.

## Description

诊断活动行活动的分类与标签配置，找出在分类导航页不可见的根因（Category=0 未分类），
提供基于 3800+ 个活动真实数据的标签替换建议，并在用户修复后回读排名变化。

## Owner

Lovstudio — mark@lovstudio.ai

## License / Terms

MIT — 自由使用、修改和分发，保留版权声明。

## Use Case

面向在活动行发布付费或免费活动的主办方，尤其是在分类页找不到自己活动的用户。
典型场景：活动发布后进行曝光检查，或收到反馈说某分类下看不到活动时的诊断。

## Deployment Geography

中国大陆（huodongxing.com）

## Requirements / Dependencies

- ego-browser（继承用户已登录的活动行会话）
- Python 3.8+（profile_store.py）
- 无需额外凭据

## Known Risks and Mitigations

- **极验滑块验证阻断**：检测到验证页时自动交接给用户，等待完成后继续；不尝试自动绕过。
- **活动行改版**：ativityJson 结构变化时字段读取加 null 保护，降级到 meta keywords 提取。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [User cases](cases/cases.json)

## Skill Output

- 类型：诊断报告（中文散文）+ 标签现状说明 + 写入后字段回读比对
- 格式：终端 Markdown 文本
- 验证：回读 ativityJson 的 Category / Setting.HdxTags / Organizers / Tag 四项与改动前基线比对，Category 不为 0；在热门点击排序下找到活动并报告位置

## Skill Version

0.4.0

## Ethical Considerations

仅读取公开活动页信息，不存储用户登录凭据，不尝试绕过平台验证机制。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)。手工川 AI 创造营第五期：Category=0 → 改为 11 → 热门点击第 4 位。

### Dimension Map

| 维度 | 分数 | 证据摘要 |
|---|---|---|
| 状态读取准确性 | 0.95 | ativityJson 读取值与后台实际一致，回读验证通过 |
| 根因定位有效性 | 0.90 | Category=0 是直接字段，指向后用户一次修复成功 |
| 操作路径简洁性 | 0.85 | 一次浏览器调用，给出明确后台路径 |

### Pricing Basis

免费。见 [`pricing-card.yaml`](pricing-card.yaml)。

### Distribution

| 渠道 | 状态 |
|---|---|
| github | 已准备 |
| lovstudio | 已准备 |
| workbuddy | 未计划 |
| skillpay | 未计划 |
