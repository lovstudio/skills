# Skill Pricing Card 规范

这份规范把文章中的定价思路整理成可复用的判断工具。它服务于 Agent Skill、Skill 套餐和 Skill 加服务的交付，不把一次性的市场猜测伪装成精确答案。

## 1. 输入清单

优先从源文件、真实使用记录和当前渠道页面提取；没有原始数据时，写出估算依据。

| 字段 | 说明 | 最小证据 |
| --- | --- | --- |
| `skill_id` / `version` | 交付物身份 | frontmatter、manifest 或用户命名 |
| `outcome` | 买家最终拿到的结果 | 输出文件、完成动作或可观察变化 |
| `audience` | 主要购买者与使用场景 | 用户描述、历史请求或产品页面 |
| `delivery_unit` | 一次购买包含什么 | 单项、额度、订阅、套餐或服务 |
| `build_hours` | 需求、实现、测试和文档时间 | 工时记录或带范围的回溯估计 |
| `maintenance_hours` | 复评周期内的更新、适配和支持 | 版本计划、问题记录或估计 |
| `creator_rate` | 创作者时间的货币基准 | 工资、目标时薪、项目报价或区间假设 |
| `direct_costs` | API、基础设施、素材、渠道和支付成本 | 账单、报价或标注过的假设 |
| `value_evidence` | 省时、替代采购、质量、收入或风险变化 | 实测、客户反馈、案例或保守估算 |
| `channel` | 公开市场、内容平台、安装市场或直销 | 当前页面、协议或用户指定 |
| `display_unit` | LovStudio 产品展示固定为 `credits` | 当前产品规则 |
| `credit_conversion` | 内部估值换算为 Credits 的当前规则 | 已核验配置或服务端常量 |

## 2. 成本底线

先把时间当作真实成本，再加入直接费用：

```text
total_hours = build_hours + maintenance_hours + support_hours
time_cost = total_hours × creator_rate
cost_floor = time_cost + direct_costs + support_reserve
```

`support_reserve` 可按预期购买量、问题率和每次处理时间估计。维护周期要写在卡片里，例如“按 6 个月复评”，避免把一次开发时间和长期服务混成一个数字。

建议给出 `low / base / high` 三档，而不是只写一个看似精确的工时。若创作者时薪来自假设，成本底线的置信度随之下降。

## 3. 价值锚点

按照买家真正拿到的结果估计可捕获价值：

```text
time_value = buyer_hours_saved × buyer_hourly_value × realization_rate
replacement_value = avoided_vendor_cost + avoided_rework_cost
growth_value = conservative_revenue_or_conversion_lift
risk_value = avoided_error_cost + avoided_delay_cost
value_anchor = time_value + replacement_value + growth_value + risk_value
```

只使用能说明来源的分项。尚未量化的结果放在定性证据中，并降低置信度；`value_anchor` 是价值空间的参考，不是对买家收益的承诺。

`realization_rate` 反映买家实际使用率、环境适配和交付完成率。一次性安装后很少使用的 Skill，时间节省按理论满额计入前需要额外证据。

## 4. 六维评分

每项 0–5 分，卡片必须同时保存分数、权重、加分事实和扣分事实。购买信心、维护负担和复制风险采用“分数越高越利于定价”的反向表达。

| 维度 | 权重 | 5 分表现 | 低分信号 |
| --- | ---: | --- | --- |
| 实际结果价值 | 30% | 结果直接可交付，时间或支出变化可回读 | 只有功能描述，结果需大量人工补全 |
| 稀缺性与替代难度 | 20% | 经验、数据、流程或组合能力少见 | 通用提示即可替代，选项极多 |
| 质量证据与购买信心 | 15% | 有重复使用、案例、样例或明确验收 | 没有样例，版本/依赖不清晰 |
| 价值飞轮潜力 | 15% | 使用会积累数据、模板、反馈或生态连接 | 每次使用彼此独立，复用沉淀弱 |
| 维护与交付效率 | 10% | 依赖稳定，支持边界清楚，边际成本低 | 频繁适配，人工支持重 |
| 复制与渠道可控性 | 10% | 版本、交付、更新和服务能形成差异 | 源内容易被转发，渠道缺少升级承接 |

```text
weighted_score = Σ(score / 5 × weight)
```

分数映射价格定位时使用相对语言：

- `0–1.9`：验证入口或免费获客，先积累使用证据；
- `2.0–2.9`：轻量/标准入口，边界收窄，降低首次购买摩擦；
- `3.0–3.9`：标准或专业交付，重点展示稳定结果与支持范围；
- `4.0–5.0`：专业/旗舰组合，可叠加持续更新、团队许可或落地服务。

这是定价位置的辅助刻度。成本底线、价值范围、渠道上限和购买信心仍然决定最终数字。

## 5. 价格推导

先形成价格空间，再决定一个可测试的数字：

```text
price_floor = cost_floor × recovery_target
price_ceiling = value_anchor × value_capture_rate
recommended_price = price_floor + capture_ratio × (price_ceiling - price_floor)
```

常用判断：

- 证据初建：`recovery_target` 与 `value_capture_rate` 取保守范围，配合首发测试价；
- 有重复结果：提高 `capture_ratio`，从低摩擦入口过渡到稳定价格；
- 结果接近替代真人服务：按交付结果与支持范围定价，避免只按源码或制作分钟数计费；
- `price_ceiling < price_floor`：先检查输入、范围和交付形态，再选择缩小范围、改成套餐或改走服务报价；
- 渠道存在价格上下限：记录“模型价格”和“渠道可执行价格”两列，保留差异原因。

价格卡至少包含三种数字：

1. `recommended_price`：当前最值得测试的主价格；
2. `launch_price`：用于验证转化和收集反馈的短期价格，带结束条件；
3. `price_range`：成本、价值和证据变化后的可讨论区间。

### LovStudio 展示契约

成本底线和价值锚点可以使用明确的内部估值币种，但 LovStudio 的产品卡、详情页、套餐、订阅和购买入口只显示 Credits：

```text
recommended_price_credits = convert_with_verified_rule(recommended_price)
launch_price_credits = convert_with_verified_rule(launch_price)
price_range_credits = convert_with_verified_rule(price_range)
```

不得在 Skill 产品界面展示 `¥`、`$`、`HKD`、`CNY` 等法币金额，也不得把法币金额与 Credits 并列作为“参考价”。法币只允许出现在 Credits 充值界面。外部市场强制要求法币时，其金额仅属于该外部渠道执行记录；LovStudio 产品价格仍为 Credits。兑换规则必须来自当前已核验配置，不硬编码可能过期的汇率。

## 6. 渠道与套餐

文章提到的 WorkBuddy、内容绑定分发、支付宝 SkillPay 与 youmind 可作为渠道类型示例；它们是文章中的观察，当前价格、协议、结算与支付能力必须重新核验。

| 渠道形态 | Pricing Card 应强调 | 常见承接 |
| --- | --- | --- |
| LovStudio 产品界面 | Credits 价格、周期、权益与兑换结果 | Credits 单项购买、订阅或套餐 |
| 安装优先 | 免费结果样例、安装摩擦、使用边界 | 付费套餐、持续更新或落地服务 |
| 内容绑定 | 内容即时收益、复刻路径、Skill 额外交付 | 内容转化、订阅或创作者分成 |
| 强制标价/Agent 支付 | 机器可读价格、版本、安装与支付后交付 | 单项购买、额度或组合调用 |
| 付费创作市场 | 样例、首发价、支持范围、升级路径 | 单项、套餐、订阅或授权 |

套餐设计围绕不同交付深度，而非简单堆数量：

- 轻量：单一结果、清晰边界、低支持负担；
- 标准：完整主流程、常见输入和基本更新；
- 专业：复杂输入、质量验收、持续适配或团队使用；
- 旗舰：多个 Skill 的闭环、落地服务、定制连接或长期陪跑。

批量定价时先分别完成各项 Pricing Card，再讨论组合折扣。组合价必须说明新增的协同价值与支持成本，避免把多个独立低价简单相加。

## 7. 卡片模板

```markdown
# Skill Pricing Card：<skill_id>

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | <version> / <unit> |
| 目标买家 | <audience> |
| 建议价格 | <recommended_price_credits> Credits / <billing_model> |
| 稳定价格带 | <low_credits>–<high_credits> Credits |
| 首发测试价 | <launch_price_credits> Credits，持续至 <review_trigger> |
| 渠道 | <channel> |
| 置信度 | <high / medium / low> |

## 为什么是这个价格

- 成本底线：<cost_floor>，依据 <evidence>。
- 价值锚点：<value_anchor>，依据 <evidence>。
- 价格位置：<position>；捕获比例和渠道限制为 <reason>。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | <x> | 30% | <evidence> | <gap> |
| 稀缺性与替代难度 | <x> | 20% | <evidence> | <gap> |
| 质量证据与购买信心 | <x> | 15% | <evidence> | <gap> |
| 价值飞轮潜力 | <x> | 15% | <evidence> | <gap> |
| 维护与交付效率 | <x> | 10% | <evidence> | <gap> |
| 复制与渠道可控性 | <x> | 10% | <evidence> | <gap> |

## 买家得到什么

<结果、输入、输出、适用边界和支持范围。>

## 渠道与推广

<样例、试用、首发、内容、套餐和升级路径。>

## 风险、假设与复评

- 使用风险：<环境、依赖、复制、支持或交付风险>。
- 假设：<输入假设>。
- 证据缺口：<需要补的实测、案例或平台事实>。
- 复评触发：<版本、用户量、转化、支持成本或渠道规则变化>。
```

## 8. 质量检查

一张可用的卡片应满足：

- 买家只看主文案也能理解结果、价格、范围和风险；
- LovStudio 产品卡、详情页、套餐、订阅和购买入口只出现 Credits，法币只出现在 Credits 充值界面；
- 创作者能从成本、价值和评分备注复算结论；
- 渠道运营能直接拿到首发、稳定价、套餐和推广动作；
- 后续复评能定位是哪一个输入或证据变化造成价格变化。

来源：用户指定的公众号文章 [Q9HkH6mGloXDyBFLQnhMTw](https://mp.weixin.qq.com/s/Q9HkH6mGloXDyBFLQnhMTw)。
