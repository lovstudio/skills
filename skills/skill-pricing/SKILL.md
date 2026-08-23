---
name: lov-skill-pricing
description: >
  为一个或多个 Agent Skill 生成可解释的 Skill Pricing Card：结合创作者时间与维护成本、用户价值、稀缺性、购买信心和生态潜力，输出建议价、价格区间、渠道策略及证据缺口；触发语包括“给这个 Skill 定价”和 “price this Skill”。
license: MIT
metadata:
  author: contributors
  version: "0.2.0"
  tags:
    - pricing
    - skill-commerce
    - pricing-card
    - value-assessment
  compatibility: "Portable Agent Skills format; works with local Skill source, catalog metadata, or a structured capability brief."
  dependencies: []
---

# Skill Pricing Card

把 Skill 的价格从一次拍脑袋，变成一张可以向创作者、购买者和渠道解释的 Pricing Card。结果聚焦可交付价值：建议价、价格带、定价依据、渠道适配、推广动作、风险和证据缺口；内部提示、源文件细节和个人背景只作为判断上下文。

## Triggers

### Activate when

- 用户说“给这个 Skill 定价”“给所有 Skills 做统一定价”“生成 Skill Pricing Card”或“评估这个 Skill 值多少钱”。
- 用户提供 Skill 源码、README、能力说明、用户结果或现有价格，希望得到价格、套餐和推广建议。
- The user asks to “price this Skill”, “create a Skill Pricing Card”, “review Skill monetization”, or “set a price ladder for these Skills”.

### Do not activate when

- 用户只需要实现、修复、重构或发布 Skill，分别交给对应的开发或发布能力。
- 用户只需要查询某个平台当前费率、支付接口或合同条款，先使用事实核验能力，再把结论带回本 Skill。
- 用户只想做普通 SaaS 订阅或实物商品定价，且交付单元不是 Agent Skill。

## Product contract

- **结果单位：** 一项 Skill 对应一张卡；批量请求使用同一评分口径并保留每项独立的证据与假设。
- **成本底线：** 计入需求分析、开发、测试、文档、发布、维护、支持和直接费用；创作者时间按可解释的时薪或工资基准折算。
- **价值锚点：** 以用户节省的时间、减少的外包支出、交付质量、收入机会和风险降低为证据；结果描述优先于功能清单。
- **价值修正：** 评价稀缺性、购买信心、实际价值和数据/生态飞轮，并记录维护负担与复制风险。
- **渠道边界：** 区分标价、首发价、内部 Credits、订阅价、按次价、套餐价和服务报价；平台规则每次以当前来源核验。
- **公开表达：** 对外卡片解释“为什么这个价格合理、买家得到什么、使用风险是什么”，避免暴露内部提示、私有数据或不可验证的收益承诺。

完整评分表、公式、分数解释与卡片模板见 [Pricing Card 规范](references/pricing-card.md)。

## Workflow (MANDATORY)

**Follow these steps in order.**

### Step 0: Resolve the Skill root and reference

1. 使用 `SKILL_DIR`；缺少时从当前已安装 Skill 上下文推断根目录。
2. 检查 `$SKILL_DIR/references/pricing-card.md` 与 `$SKILL_DIR/scripts/validate_skill.py`。
3. 读取 Pricing Card 规范，再处理输入；缺少资源时报告相对路径并暂停产出。

手工校验时可运行：

```bash
export SKILL_DIR="/path/to/lov-skill-pricing"
```

### Step 1: Establish the pricing subject

从当前请求、Skill 源码、README、manifest、历史价格和用户结果中建立事实清单：

- `skill_id`、版本、交付单元和目标买家；
- 输入、输出、典型完成时间、复用频率和依赖条件；
- 需求分析到上线的创作者小时数、预计维护小时数、支持负担和直接费用；
- 用户获得的结果、可量化收益、替代方案和已存在的质量证据；
- 目标渠道、币种、计费周期、价格上限、结算方式和当前验证来源。

输入缺少字段时采用项目上下文与行业常识形成“暂定假设”，在卡片中逐项标注；仅当缺失字段会改变价格模型时才询问一个聚焦问题。没有用户结果证据时，降低购买信心分数，不用想象中的案例填空。

### Step 2: Separate capability from internal context

把信息分成四层：

1. `publishable capability`：买家能拿到的结果、交付范围和适用条件；
2. `cost evidence`：时间、维护、支持、基础设施和其他直接费用；
3. `value evidence`：节省时间、减少支出、质量提升、收入机会和风险下降；
4. `private context`：源提示、密钥、内部路径、个人背景、未公开策略和未验证承诺。

Pricing Card 对外只呈现前 1–3 层经过整理的结论；第 4 层仅用于内部判断，并在输出中以“证据缺口”概括。

### Step 3: Build the cost floor and value anchor

按 [Pricing Card 规范](references/pricing-card.md) 计算两条边界：

- `cost_floor`：创作者时间成本 + 维护/支持准备金 + 直接成本；
- `value_anchor`：用户可感知的时间价值、替代采购成本、质量收益、收入机会和风险降低的保守估计。

分别给出基准值和范围。成本范围来自时间或费率不确定性；价值范围来自用户结果证据强弱。两者之间是可讨论的价格空间；成本底线直接作为售价、理论价值直接作为收费结果，都需要额外论证。

### Step 4: Score the card

按 0–5 分记录以下维度、权重、证据和备注：

- 实际结果价值：30%；
- 稀缺性与替代难度：20%；
- 质量证据与购买信心：15%；
- 价值飞轮潜力：15%；
- 维护、支持与交付负担的反向分：10%；
- 复制风险与渠道可控性的反向分：10%。

分数只用于把理由固定下来，不替代事实。卡片必须同时写出“加分事实”和“扣分事实”，并把总分映射成价格定位：验证入口、标准交付、专业交付或旗舰组合。高分但证据稀薄时，优先采用可验证的首发价与试用机制。

### Step 5: Select the commercial shape

根据交付方式和使用频率选择：

- 一次性购买：结果清晰、边界稳定、支持负担有限；
- 订阅或额度：持续维护、持续生成或基础设施成本显著；
- 按次/按量：单次价值容易计量，用户使用频率差异大；
- 免费入口 + 付费组合：渠道缺少付费能力、购买心智尚在形成，或需要先积累结果证据；
- Skill 套餐 + 服务：多个阶段互相增强，或买家需要落地、迁移和定制支持。

输出单项建议价、首发测试价、稳定价格带和套餐关系。每个数字都附带币种、周期、渠道和依据；内部积分价格与公开货币价格分开记录。

### Step 6: Match the channel and promotion

核验目标渠道当前规则，再生成对应动作：

- 渠道仅支持安装：用免费入口、内容分发、结果样例和后续服务承接价值；
- 内容绑定 Skill：把文章/视频的即时收益、复刻路径和 Skill 交付边界写清楚；
- 强制标价或 Agent 自助支付：提供机器可读的价格、安装、试用、版本和支付后交付信息；
- 支持付费创作市场：用首发价、使用示例、清晰支持范围和升级路径降低购买犹豫。

文章中的平台观察属于背景材料，不等同于现行平台契约。遇到费率、价格上下限、结算或协议问题，标注核验时间和来源；查询结果过期时重新核验。

### Step 7: Render the user-facing Pricing Card

按模板输出，顺序固定：

1. 一句话结果与建议价；
2. 价格区间、计费形态、渠道和首发测试方案；
3. 成本底线与价值锚点；
4. 六维评分表及每项证据；
5. 买家得到的结果、适用边界和使用风险；
6. 推广策略、套餐关系和下一次复评触发条件；
7. 假设、证据缺口、来源与置信度。

批量模式最后附一张横向比较表，并说明统一口径与个体差异。面向买家的文案用能力和收益描述，内部标签、个人信息和实现来源放进证据备注而非主文案。

### Step 8: Validate the deliverable

交付前逐项检查：

- 建议价位于成本底线和价值范围之间，或明确说明越界原因；
- 每个关键数字都有输入、假设或来源；
- 公开价格、内部 Credits、套餐和渠道状态没有混写；
- 风险、维护范围、版本和支持边界可被买家理解；
- 文章观察与当前平台事实已经分层；
- 没有把功能数量、源码长度或作者投入单独当作用户价值；
- 缺口、置信度和复评条件清楚可见。

发现因果矛盾时回到 Step 1–3 重算，并在最终卡片中保留调整理由。验证脚本只检查 Skill 源码结构；Pricing Card 的事实验收仍以输入证据和当前渠道回读为准。

## Output contract

默认输出 Markdown Pricing Card；用户指定时可同时输出 JSON 摘要。JSON 字段至少包含：`skill_id`、`version`、`currency`、`billing_model`、`recommended_price`、`price_range`、`cost_floor`、`value_anchor`、`weighted_score`、`channel`、`assumptions`、`evidence_gaps`、`confidence`、`review_trigger`。

## Dependencies

None. 若需要当前平台费率或规则，使用运行时可用的事实核验能力，并把来源和时间写入卡片。

## Runtime context

运行前读取同目录 `skill.yaml`，由宿主的 `skill-runtime` 按“当前请求、项目上下文、个人配置、品牌 Profile、安全默认值”的顺序注入，只使用 manifest 声明的字段。

- 缺少 `required: true` 字段时，按 `questions` 向用户提出一个聚焦问题；回答只用于本次运行，除非用户明确要求保存。
- Profile 只用于公开品牌事实；个人配置只用于决策，不自动写入产物或源码。
- 调试报错提供可复制的 `context_id`、字段路径和来源，不输出秘密、完整私人路径或原始内容。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
