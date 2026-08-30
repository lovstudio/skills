# lov-writing-style

![Version](https://img.shields.io/badge/version-2.3.0-CC785C)

把事实、笔记或草稿写成工程实战驱动的第一人称中文内容。v2 基于 19 篇、约
12.46 万字元的真实样本画像，不靠堆叠口头禅，而是复现作者如何使用现场、证据、
概念边界与强判断。它们是高频材料，不是每篇文章都要复现的固定骨架。

## v2 的变化

- 用 2026-08-25 的 19 篇实证画像替换旧版未经当前来源支持的样本说明。
- 先建立事实账本，再选择技术深度、创业复盘、产品快评、个人随笔或演讲招募模式。
- 区分跨题材稳定特征与题材偶发特征，避免把短句、粗口和“我错了”写成戏仿。
- 增加本地风格审计、User Profile、真实案例、维度地图、定价依据和渠道状态。

## 2026-08-26 编辑校准

- 并列对象各有鲜明差异时，允许拆成连续一句段，不把所有对照塞进分号长句。
- 工作定义、核心论点和最终判断可以少量加粗，形成真正的信息层级。
- 四项以上同级技术例子优先列表化，多节对比后用独立汇总表收束。
- 同一事实边界只交代一次，删掉解释梗和重复辩护；但不把有限样本改写成绝对事实。

## 本地安装

从官网公开仓库安装到当前 Agent Skills 运行时：

    npx skills add lovstudio/writing-style-skill -g -y

从本地真源一次性安装：

    export SKILL_SOURCE_DIR="/path/to/writing-style-skill"
    npx skills add "$SKILL_SOURCE_DIR" --skill lov-writing-style

开发安装采用三层链：真源 → agents → 具体客户端。

    export SKILL_SOURCE_DIR="/path/to/writing-style-skill"
    mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills"
    ln -sfn "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-writing-style"
    ln -sfn ../../.agents/skills/lov-writing-style "$HOME/.claude/skills/lov-writing-style"
    ln -sfn ../../.agents/skills/lov-writing-style "$HOME/.codex/skills/lov-writing-style"

三个入口最终都应解析到同一真源目录，不复制 Skill 文件。

## User Profile

[skill.yaml](skill.yaml) 声明 user-profile/v1。每次运行读取用户、品牌、工作区和
本 Skill 的长期记录；用户直接声明的默认题材、受众、署名和文风 Profile 通过
[profile_store.py](scripts/profile_store.py) 原子写回共享 Profile。

完整约定见 [User Profile contract](references/user-profile.md)。

## 使用

### 从事实新写

输入：

> 这是一次 Skill 升级：旧版是 0.1.0；新画像来自 19 篇文章，约 12.46 万字元；
> v2 新增五种题材模式和事实账本。请按我的文风写一段发布说明，不新增事实。

调用：

> 使用 lov-writing-style 按产品实测 / 发布复盘模式写。

### 保真改写

> 用我的口吻重写这份创业复盘。保留所有日期、金额、失败和利益关系，不要为了
> 更有戏剧性补造经历。

### 文风诊断

> 诊断这篇稿子与我的文风差距最大的五处，并直接给出修订版。

### 非触发

> 从这三篇陌生作者文章里提取一种新文风。

这属于 lov-style-clone，不由本 Skill 接管。

## 五种题材模式

- 技术深度：定义、边界、方案、时间线和验证。
- 创业复盘：选择、投入、失败、结果、代价和方法。
- 产品实测 / 快评：真实 case、明确好恶和适用边界。
- 个人 / 旅行随笔：场景、人物、时间回望和具象收束。
- 演讲 / 招募：共同问题、现场关系和明确行动。

完整矩阵见 [Writing modes](references/writing-modes.md)。

## 输出契约

- 事实、数字、时间、名字、版本、代码、引语和不确定程度不变。
- 没有亲历时不虚构“我亲自做过”。
- 长句解释，短句落锤；一句段服务于节奏，不按配额生产。
- 每个主要章节都要有事实、案例、数字、亲历或明确来源。
- 结尾服从这篇文章尚未完成的工作：可以落到判断、行动、现场、问题或下一步，
  也可以在证据已经闭合时直接停住。

完整画像见 [v2 style profile](references/style-profile.md)。

## 本地风格审计

对 300 字以上的草稿，可以查看句长、段落、第一人称、数字锚点、公关套话等可观察
指标：

    python3 scripts/style_audit.py draft.md

结构化输出：

    python3 scripts/style_audit.py draft.md --format json

审计结果只用于诊断，不判定作者身份，不鼓励为了命中数字而牺牲内容。

## 原子组合

[Skill composition](references/skill-composition.md) 记录了与 lov-style-clone、
lov-human-writing、旧命令兼容扫描器、公众号品牌化和文章落盘能力的边界。
`lov-human-writing` 是新写与改写成稿的必经质量门；其他能力仍通过画像、正文或
报告可选交接。

## 可信度与案例

- [Machine-readable Skill Card](skill-card.yaml)
- [Human-readable Skill Card](skill-card.md)
- [Real user case](cases/cases.json)
- [Pricing basis](pricing-card.yaml)

## 质量门

    python3 scripts/validate_skill.py .
    python3 scripts/style_audit.py --self-test

还需验证一个触发短语、一个非触发任务、Profile 写入与三层安装链。

## 依赖

- Agent Skills 兼容运行时。
- `lov-human-writing`：作者性、篇章与表层验收的唯一规则真源。
- `lov-branding-consistency`：只审最终受众可见文案的媒介、受众与品牌语境，
  不改作者观点和个人声音。
- Python 3.8+：风格审计与 Profile 存储。
- PyYAML：完整 Skill 源校验。
- 无网络或 credential 依赖。

## License

MIT
