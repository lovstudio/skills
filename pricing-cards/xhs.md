# Skill Pricing Card：lov-xhs

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | 0.2.0 / 公开 Skill 源码与当前版本使用说明 |
| 目标买家 | 需要从小红书主题快速得到调研结论、路线规划、选题判断或证据摘要的个人创作者、旅行规划者和内容研究者 |
| 建议价格 | 免费 |
| 稳定价格带 | 免费 |
| 首发测试价 | 免费 |
| 渠道 | LovStudio 官网 Skill Publisher |
| 置信度 | case-backed |

先用免费公开入口验证「小红书主题 → 有来源报告」是否真正被使用；不把搜索次数或抓取量本身当成付费价值。

## 为什么是免费

- 成本底线：复用本机 `xiaohongshu-cli` 和 Python 标准库采集，没有托管推理、专有数据或固定基础设施成本。
- 价值锚点：一次完整调研通常可减少 30 分钟至 3 小时的检索、筛选、整理与判断时间。
- 价格位置：当前优先验证使用频率、报告采纳率和真实用户反馈；暂不设置付费门槛。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | 4.0 | 30% | 直接把主题变成结论、方案和证据链接 | 结果质量受样本量和平台内容质量影响 |
| 稀缺性与替代难度 | 3.0 | 20% | 登录态搜索、正文采集和报告契约组成完整链路 | 通用搜索工具和人工整理仍可替代部分价值 |
| 质量证据与购买信心 | 3.0 | 15% | 有真实冈仁波齐案例、20 篇正文采集记录与自动化校验 | 缺少大规模跨主题使用数据 |
| 价值飞轮潜力 | 2.5 | 15% | Profile、案例和报告模板可持续沉淀 | 默认不共享跨用户数据，飞轮依赖主动反馈 |
| 维护与交付效率 | 3.0 | 10% | Python 标准库采集，部署边界清晰 | 小红书 API、风控和登录态需要持续适配 |
| 复制与渠道可控性 | 2.0 | 10% | 公开源码和目录可追踪 | 源码公开后复制门槛较低 |

加权总分约 3.1 / 5；当前采用免费生态入口，而不是高价单项工具。

## 买家得到什么

- 默认把主题请求整理成报告，而不是只返回搜索结果。
- 支持精确输入词优先、放宽查询说明、标题过滤和原始 JSON 导出。
- 提供正文采集脚本、报告契约、作者诚信契约、案例和验证脚本。
- 适用边界：需要本机可用的小红书登录态、网络和当前平台可用性。

## 渠道与推广

- 在 LovStudio 官网免费提供，重点展示真实案例和可复用报告结构。
- 用「主题 → 结论 → 证据 → 行动」对比普通搜索结果，降低试用门槛。
- 收集真实使用反馈；只有加入托管服务、专有数据或保证支持时才重新评估收费。

## 风险、假设与复评

- 使用风险：小红书接口、风控、登录态和页面结构变化会影响结果；报告必须保留来源边界和人工确认项。
- 假设：用户拥有本机登录态和网络环境，且愿意按报告契约使用结果。
- 证据缺口：不同主题的成功率、报告采纳率、长期留存、维护工时和真实用户反馈。
- 复评触发：加入托管服务、专有数据、保证支持、直接付费交付或维护成本明显变化。

## 机器可读摘要

```json
{
  "skill_id": "lov-xhs",
  "version": "0.2.0",
  "currency": "Credits",
  "billing_model": "free",
  "recommended_price_credits": 0,
  "launch_price_credits": 0,
  "price_range_credits": [0, 0],
  "public_delivery_mode": "public_source",
  "weighted_score": 3.1,
  "channel": "LovStudio Skill Publisher",
  "assumptions": ["local login and network are available", "one run saves 30-180 minutes"],
  "evidence_gaps": ["cross-topic success rate", "report adoption", "long-term retention", "support cost"],
  "confidence": "case-backed",
  "review_trigger": "hosted service, proprietary data, guaranteed support, direct paid delivery, or material maintenance-cost change"
}
```
