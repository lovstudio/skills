# Skill Card — lov-writing-style

## Description

依据经 19 篇真实样本校准的个人中文文风，把事实、笔记或草稿写成工程实战驱动的
第一人称深度内容，并支持保真改写、文风诊断与五种题材适配。

## Owner

LovStudio；维护入口为本地 Skill source。

## License / Terms

MIT。Skill 指令和本地脚本可按许可证使用；输入、原始语料与输出归用户所有。

## Use Case

面向需要长期保持个人声音的中文创作者、工程师、创业者和独立开发者。输入已经
确认的事实、笔记、草稿或资料，输出技术深度稿、创业复盘、产品实测、个人随笔、
演讲招募稿，或现有稿件的文风诊断。

## Deployment Geography

可在全球任意兼容 Agent Skills 的运行时使用；核心写作与本地审计无需联网。

## Requirements / Dependencies

需要具备高质量中文写作能力的语言模型，并安装 `lov-human-writing` 与
`lov-branding-consistency`。前者是作者性、篇章和表层门禁，后者只检查最终可见
文案的受众与品牌语境。无 credential 或 API 依赖；Python 3.8+ 用于风格审计和
Profile 存储，PyYAML 用于完整源校验。

## Known Risks and Mitigations

主要风险是为强化第一人称而虚构经历、把口头禅堆成戏仿、为命中统计数字而损害
内容、不同题材使用同一结构，以及下游改写破坏作者声音。v2 用事实账本、稳定 /
偶发特征分离、诊断而非评分、五种模式矩阵和原子交接边界降低这些风险。

## References

- [Primary Skill instructions](SKILL.md)
- [Verified v2 style profile](references/style-profile.md)
- [Writing mode matrix](references/writing-modes.md)
- [Skill composition](references/skill-composition.md)
- [Machine-readable card](skill-card.yaml)

## Skill Output

输出 UTF-8 Markdown 或纯文本的新稿、保真改写、局部适配或聚焦诊断；可选审计
输出 JSON。验收事实完整、题材匹配、论证成立、节奏自然、没有虚构第一人称经历
和未验证发布声明。

## Skill Version

2.3.0

## Ethical Considerations

只使用用户授权的素材与 Profile 记录；不分发原始私人样本，不虚构自传事实，不
冒充无关作者，不把推测写成归因。

## LovStudio Evidence

### User Cases

[cases/cases.json](cases/cases.json) 收录本次 v2 升级的真实发布复盘案例。输入、
最小 Prompt、输出、事实断言和证据路径均可回读。

### Dimension Map

机器卡记录事实保真、论证结构、节奏与版式、题材适配和防戏仿五个维度。当前只有
一条真实创建案例，不制造数值评分；每个维度都指向案例、行为契约或可运行脚本。

### Pricing Basis

[pricing-card.yaml](pricing-card.yaml) 将 v2 定为免费本地能力：语料与 Profile
由用户拥有，没有云端成本，也没有公开渠道的付费转化或支持成本证据。公开发布、
云服务、画像主版本变化或 20 个跨题材案例会触发复评。

### Distribution

本地 agents、Claude 与 Codex 入口安装并验证。WorkBuddy 与 SkillPay 未准备付费
包；GitHub 与 LovStudio 未发布。本卡不把本地源码或准备材料写成已上线。
