# Skill Pricing Card：lov-feedback-loop

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | 0.3.0 / 公开 Skill 源码、反馈协议契约，以及账本、回扫、报告、接入脚本 |
| 目标买家 | 想让 Agent 随真实使用持续改进，又不希望靠记忆和感觉调整 Prompt 的个人与团队 |
| 建议价格 | 0 Credits；免费入口 |
| 渠道 | LovStudio 官网目录，源码公开在 `lovstudio/feedback-loop-skill` |
| 置信度 | entry |

## 为什么免费

- 六维加权约 3.8 / 5，落在标准交付档；但反馈闭环的价值随使用量上升：越多人真实使用，信号样本、未闭环模式与作用域判断才越准。
- 方法本身可复现，付费点不在“知道要做反馈闭环”，而在长期实现与维护；用一次买断挡住早期用户，换不到它最需要的真实使用证据。
- 因此先用 0 Credits 作为公开入口，等出现云端聚合、团队协作与托管需求时，再评估分层付费。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | 4.0 | 30% | 把被动情绪与主动 judge 统一成可统计事件，并给出未闭环清单与修复时长 | 价值依赖用户真的采纳反馈闭环，短期感受偏基础设施 |
| 稀缺性与替代难度 | 3.6 | 20% | 协议、账本 schema、作用域阶梯与接入器形成完整链路 | 概念容易被自建脚本模仿，源码公开后更如此 |
| 质量证据与购买信心 | 3.6 | 15% | 已有 9 条真实用例，其中包含另一条会话自动触发落账的实证 | 首个公开版本，缺大样本外部使用数据 |
| 价值飞轮潜力 | 4.2 | 15% | 反馈本身会持续产出改进样本，根规则与协议越用越准 | 效果取决于宿主是否持续执行根规则 |
| 维护与交付效率 | 4.0 | 10% | instruction 加标准库脚本，无外部服务与基础设施成本 | 宿主目录约定与目录规范变化需要跟进适配 |
| 复制与渠道可控性 | 3.0 | 10% | 免费入口最大化目录、Agent 与用户之间的分发面 | 无价格闸门，只能靠案例与口碑区分质量 |

加权评分约 3.8 / 5；免费不改变交付标准，只改变价值回收方式。

## 买家得到什么

用户得到一条从“用户表态”到“规则迭代”的闭环：评价词表与被动情绪判定、追加式反馈账本、作用域阶梯（任务到技能、规则、全局 Prompt）、满意度报告（趋势、未闭环清单、修复时长），以及把同一套机制接入其他宿主的能力。

适用边界：本机运行、默认不联网；跨设备同步、团队看板、多人权限与托管服务不在交付范围内。

## 渠道与推广

- 官网免费安装，主打“满意与不满都留得下证据，改哪一层有依据”。
- 用真实案例降低理解成本：历史会话回扫抓到未闭环不满、另一条会话自动落账、报告与账本数字一致。
- 与 `skill-optimizer`、`skill-add-case` 形成补位：一个优化技能本身，一个沉淀结果案例，本 Skill 负责收集反馈信号。

## 风险、假设与复评

- 使用风险：被动判定可能误报；协议要求证据原话、置信度小于 1，低强度信号需形成模式才落账。
- 假设：维护时间来自本次发布过程；价值锚点按每次省下 5–30 分钟重复解释估算。
- 证据缺口：真实安装量、30 天留存、跨宿主使用比例与平均支持时长。
- 复评触发：达到 100 次真实安装、版本变化，或出现云端聚合、团队协作与托管需求时，复评是否引入分层付费。

## 机器可读摘要

```json
{
  "skill_id": "lov-feedback-loop",
  "version": "0.3.0",
  "display_unit": "credits",
  "billing_model": "free_entry",
  "recommended_price_credits": 0,
  "launch_price_credits": 0,
  "price_range_credits": [0, 0],
  "delivery_mode": "public_source",
  "weighted_score": 3.8,
  "channel": "LovStudio Skill Publisher",
  "assumptions": ["maintenance only, no infrastructure cost", "5-30 minutes saved per avoided re-explanation"],
  "evidence_gaps": ["real install volume", "30-day retention", "cross-host usage", "average support time"],
  "confidence": "entry",
  "review_trigger": "100 real installs, a version change, or emerging cloud-aggregation, team-collaboration, and hosting needs"
}
```
