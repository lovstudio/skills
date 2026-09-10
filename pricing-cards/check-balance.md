# Skill Pricing Card：check-balance

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | 0.1.0 / 公开 Skill 源码、六个 provider 探测、JSON 输出、Profile 契约 |
| 目标买家 | 同时使用多个 agent 或 API 平台的个人开发者与小团队 |
| 建议价格 | 0 Credits |
| 稳定价格带 | 0 Credits，保持公开免费入口 |
| 首发测试价 | 0 Credits，持续到出现托管聚合或多机汇总需求 |
| 渠道 | LovStudio 官网 Skill Publisher |
| 置信度 | case-backed；真实排查案例与实跑输出已记录，长期使用样本仍然有限 |

## 为什么是免费

- 成本底线：约 3–5 小时需求排查、实现、文档和验证，外加每半年约 2–4 小时的接口漂移维护；纯 Python 标准库实现，无托管与固定 API 费用。
- 价值锚点：一次跨平台额度排查原本要分别打开多个账号面板、读本地数据库和网关日志，约 30–60 分钟；现在一条只读命令在数秒内给出剩余额度、重置时间和消耗速率。
- 价格位置：六维加权结果约 2.85/5。能力真实、验收明确，但替代方案较多且复制门槛低，当前由维护者承担成本，作为免费公开入口。
- 证据边界：已有真实排查案例（ChatGPT Pro 周窗口 100%、Claude 凭据过期、DeepSeek 共享余额、网关当日消费）与两条降级路径验证；尚缺外部用户、多机环境和长期运行的样本。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | 3.5 | 30% | 输出的是可观察的剩余额度、重置时间与消耗速率，直接支撑切换 provider 的决策 | 结果是状态查询而非可交付产物，价值集中在决策时刻 |
| 稀缺性与替代难度 | 3.0 | 20% | 官方 status 与各平台面板都是单点；跨订阅、预付余额、本地网关与共享池识别的组合链路少见 | 单个 provider 的等价查询普遍存在，用户也可自行组合脚本 |
| 质量证据与购买信心 | 3.5 | 15% | 六探测实跑通过、源码校验通过、两条降级路径与批量结算回退均已验证，附两个真实案例 | 尚无外部用户复现，未覆盖 Linux 与多机场景 |
| 价值飞轮潜力 | 1.5 | 15% | Profile 可沉淀网关日志路径与告警阈值，降低后续调用成本 | 每次运行彼此独立，用户之间没有网络效应，数据不复用 |
| 维护与交付效率 | 3.0 | 10% | 纯标准库、无托管成本、支持边界清楚，边际交付成本接近零 | 依赖 wham/usage 与 oauth/usage 等非公开接口，平台字段变化需要跟进 |
| 复制与渠道可控性 | 1.5 | 10% | 版本、案例与更新记录可以形成一定信任差异 | MIT 公开源码复制门槛低，核心逻辑单文件即可被重写 |

加权总分约 2.85 / 5；当前适合免费获客与口碑验证，不适合直接定价售卖。

## 买家得到什么

- 一条只读命令汇总六类来源：ChatGPT / Codex 官方窗口、Claude 官方订阅、DeepSeek 余额、OpenRouter 额度、本地 LiteLLM 消费、cc-switch 代理与限额。
- 统一输出剩余额度、已用百分比、重置时间与备用池，并给出已用满、余额低于阈值、未设置限额三类提醒。
- `--watch` 二次采样估算每小时消耗与可用天数；余额按批次结算时自动回退到网关计价并标注不可靠项。
- 只读不变量：不刷新 token、不写入凭据、不打印密钥；缺失来源降级为 labelled gap 而不中断整轮体检。
- 适用边界：需要本机已有登录态或 API key；不包含充值、订阅购买、密钥轮换、限额设置与通知投递。

## 渠道与推广

- 在 LovStudio 官网免费提供，重点展示“先看清再决策”，而不是罗列 provider 名称。
- 用真实结果说明：官方周窗口已用满并于固定时间重置、Claude 凭据过期、两条链路共用同一预付费余额。
- 试用入口先展示默认体检命令与 `--json`，再展示 `--watch` 与 `--only` 的进阶用法。
- 只有加入云端聚合、多机汇总、团队额度看板或托管巡检时，重新评估付费结构。

## 风险、假设与复评

- 使用风险：官方额度接口属于非公开接口，字段与语义可能变化；缺失凭据时部分 provider 只能标记不可用。
- 假设：用户能自行提供本机登录态或 API key，并理解预付余额与订阅窗口是两种不同的重置语义。
- 证据缺口：外部用户复现、Linux 环境、多台设备、长期接口稳定性与实际节省时间统计。
- 复评触发：累计 10 次外部真实使用、3 个非作者案例、接口字段变化、加入云端聚合或团队看板，或需要保证支持时复评。

## 机器可读摘要

```json
{
  "skill_id": "lov-check-balance",
  "version": "0.1.0",
  "display_unit": "credits",
  "billing_model": "free_entry",
  "recommended_price_credits": 0,
  "launch_price_credits": 0,
  "price_range_credits": [0, 0],
  "weighted_score": 2.85,
  "channel": "LovStudio Skill Publisher",
  "assumptions": ["one cross-provider quota check saves 30-60 minutes", "maintenance needs 2-4 hours per half-year"],
  "evidence_gaps": ["external users", "Linux and multi-device coverage", "upstream interface stability", "long-term saving measurements"],
  "confidence": "case-backed",
  "review_trigger": "10 external real uses, three non-author cases, interface change, cloud aggregation, team dashboard, or guaranteed support"
}
```
