# Skill Pricing Card：lov-feedback-loop

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | 0.2.0 / 单项 Skill 完整交付，含加密安装包、反馈协议契约与账本、回扫、报告、接入脚本 |
| 目标买家 | 想让 Agent 随真实使用持续改进，又不希望靠记忆和感觉调整 Prompt 的个人与团队 |
| 建议价格 | 139 Credits / 一次性解锁 |
| 稳定价格带 | 139 Credits |
| 首发测试价 | 139 Credits，首发 30 天或 100 次付费兑换后复评 |
| 渠道 | LovStudio 官网 Skill Publisher |
| 置信度 | entry |

## 为什么是这个价格

- 成本底线：本版本经历机制设计、六个模块与协议落地、按调用模型收敛为单 Skill、加密交付适配与发布校验；按 6–10 小时构建与半年 4–8 小时维护估算，直接基础设施成本接近零。
- 价值锚点：每次被忽视的不满通常意味着一次返工或一轮重新解释，单次 5–30 分钟；账本与复盘让“哪条不满还没闭环、从反馈到修复花了多久”第一次可查。
- 价格位置：139 Credits 是与 70 Credits 档同比例的入口验证价，明显低于它在长期协作里省下的重复解释成本；不包含云端同步、团队看板、托管服务与人工代运营。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | 4.0 | 30% | 把被动情绪与主动 judge 统一成可统计事件，并给出未闭环清单与修复时长 | 价值依赖用户真的采纳反馈闭环，短期感受偏基础设施 |
| 稀缺性与替代难度 | 3.6 | 20% | 协议、账本 schema、作用域阶梯与加密交付形成完整链路 | “记录反馈并改 Prompt”的概念容易被自建脚本模仿 |
| 质量证据与购买信心 | 3.6 | 15% | 已有 9 条真实用例，其中包含另一条会话自动触发落账的实证 | 首个付费版本，缺大样本付费转化与长期留存数据 |
| 价值飞轮潜力 | 4.2 | 15% | 反馈本身会持续产出改进样本，根规则与协议越用越准 | 效果取决于宿主是否持续执行根规则 |
| 维护与交付效率 | 4.0 | 10% | instruction 加标准库脚本，加密包按版本重新打包即可 | 宿主目录约定与 helper 版本变化需要跟进适配 |
| 复制与渠道可控性 | 3.0 | 10% | 加密交付、授权校验与官网兑换形成可回读链路 | 方法层面公开可复现，付费点主要在完整实现与维护 |

加权评分约 3.8 / 5，对应标准交付。139 Credits 是入口验证价，不代表成本或用户价值上限。

## 买家得到什么

用户得到一条从“用户表态”到“规则迭代”的闭环：评价词表与被动情绪判定、追加式反馈账本、作用域阶梯（任务到技能、规则、全局 Prompt）、满意度报告（趋势、未闭环清单、修复时长），以及把同一套机制接入其他宿主的能力。

适用边界：本机运行、默认不联网；跨设备同步、团队看板、多人权限与托管服务不在交付范围内。

## 渠道与推广

- 官网以 139 Credits 一次性解锁，主打“满意与不满都留得下证据，改哪一层有依据”。
- 用真实案例降低购买不确定性：历史会话回扫抓到未闭环不满、另一条会话自动落账、报告与账本数字一致。
- 与 `skill-optimizer`、`skill-add-case` 形成补位：一个优化技能本身，一个沉淀结果案例，本 Skill 负责收集反馈信号。

## 风险、假设与复评

- 使用风险：被动判定可能误报；协议要求证据原话、置信度小于 1，低强度信号需形成模式才落账。
- 假设：构建与维护时间来自本次发布过程；价值锚点按每次省下 5–30 分钟重复解释估算。
- 证据缺口：付费转化率、30 天留存、跨宿主使用比例与平均支持时长。
- 复评触发：首发 30 天、100 次付费兑换、版本变化、新增 10 个用户确认案例，或支持成本明显变化。

## 机器可读摘要

```json
{
  "skill_id": "lov-feedback-loop",
  "version": "0.2.0",
  "display_unit": "credits",
  "billing_model": "one_time",
  "recommended_price_credits": 139,
  "launch_price_credits": 139,
  "price_range_credits": [139, 139],
  "delivery_mode": "encrypted_bundle",
  "weighted_score": 3.8,
  "channel": "LovStudio Skill Publisher",
  "assumptions": ["6-10 build hours", "4-8 maintenance hours over 6 months", "5-30 minutes saved per avoided re-explanation"],
  "evidence_gaps": ["paid conversion", "30-day retention", "cross-host usage", "average support time"],
  "confidence": "entry",
  "review_trigger": "30 launch days, 100 paid redemptions, a version change, 10 new accepted cases, or material support-cost change"
}
```
