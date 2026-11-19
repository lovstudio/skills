# 博主克隆 · Creator Clone · Skill Card

## Description

博主克隆：从一个博主的公开文章（先支持公众号）得到冻结的、带逐字证据的八维风格包、盲测与留出检验、风格说明书，并可封装成按该风格写作的专属 Skill。

## Owner

Local skill contributors；通过宿主会话反馈，未创建公开支持渠道。

## License / Terms

MIT。被分析作品的文字、作者身份、品牌与观点的权利不因分析而转授；风格包只含规则、度量、短引文与哈希指纹，不含原文。

## Use Case

想系统学习某位博主的写法、再用自己的素材写作的创作者与 AI 工作流。输入公众号名称（经 `lov-wxmp-cli` 导出）或文章目录；输出冻结风格包、留出检验、说明书，可选专属写作 Skill。

## Deployment Geography

本地优先，兼容 AGENTS/Skills 的 AI 宿主。

## Requirements / Dependencies

Python 3.9+ 标准库；PyYAML（Profile 与校验）；依赖 `lov-branding-consistency`；公众号导出用 `lov-wxmp-cli`，封装用 `lov-skill-creator`。

## Known Risks and Mitigations

- 冒充博主：身份标识进入禁用清单，审计命中即失败；品牌位只迁移形态。
- 复制原文：风格包不含原文；20 字以上连续重合审计失败。
- 过拟合与污染：阅读前冻结拆分，冻结前封存留出，解封后构建的新版本自动标记受污染。
- 误读指标：对照稿给出基线；质量结论只来自人工盲评。
- 迁移观点与笔误：作者性契约只让 style 进入规则。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Rules and evidence](references/rules-and-evidence.md)
- [Holdout and blind trials](references/holdout-and-trials.md)

## Skill Output

冻结拆分与样本台账、训练集度量、风格包、风格说明书（JSON、JSONL、Markdown），可选专属写作 Skill 源码。风格包冻结与留出检验通过都不等于风格认可。

## Skill Version

0.1.0

## Ethical Considerations

不冒充被分析的博主，不复制其文章，不迁移其身份事实、商业关系与观点；不绕过平台访问限制，不收集评论区与读者信息；原文只留在本地；不自动发布。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：公众号「数字生命卡兹克」，39 条规则、257 条证据，留出 117 项命中 87；度量带吻合留出原文 0.70、画像稿 0.71、对照稿 0.34；人工盲评未做。

### Dimension Map

证据可追溯、留出纪律、迁移信号、原文与身份防护，证据与分数状态见机器可读卡片（分数暂为空，等待人工盲评）。

### Pricing Basis

免费入口，见 [`pricing-card.yaml`](pricing-card.yaml)。

### Distribution

本地已安装；源码在私有仓库 `lovstudio/blogger-cloner-skill`，公开副本为 `lovstudio/skills` 镜像。LovStudio 官网免费目录条目（0 Credits）已上线（2026-11-19）：详情页 `/skills/blogger-cloner` 返回 200 并显示 v0.1.0，`npx lovstudio skills add blogger-cloner --project` 安装出 v0.1.0。未请求 WorkBuddy 与 SkillPay。
