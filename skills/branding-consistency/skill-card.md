# Skill Card — lov-branding-consistency

## Description

`lov-branding-consistency` 为公众号、网站、App、策划案、海报、社交媒体与邮件建立统一的
受众、品牌角色、组件惯例和信息可见性门禁。它既能生成或改写文案，也能判断一句话
是否根本不该显示。

## Owner

LovStudio；本地 canonical Skill source 维护。

## License / Terms

MIT。Skill 指令和本地脚本可按许可证使用；输入、品牌资料与输出归用户所有。

## Use Case

面向创作者、产品经理、设计师、运营者和开发团队。输入一句文案、完整草稿、界面
选区或组件清单；输出可直接落位的版本、删除决策或聚焦审校。

## Deployment Geography

全球；在 Agent Skills 兼容运行时本地执行。

## Requirements / Dependencies

核心能力为 instruction-first，不需要凭据或外部 Skill。Python 3.8+ 用于 Profile 和
可选审计；PyYAML 用于完整源校验。

## Known Risks and Mitigations

- 品牌资料不足时，避免用“高级、专业、温暖”补造品牌性格；从当前场景作保守推断。
- 可见性防火墙阻止正文首图、官方 Logo、组件和生成方式进入读者文案。
- 删除测试保护理解、行动和必要归属，不把“越短越好”当作目标。
- 最终验收必须在邻近标题、图片、控件和平台字段中进行，不能只看孤立句子。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Context contract](references/context-contract.md)
- [Scene conventions](references/scene-conventions.md)
- [Quality gate](references/quality-gate.md)
- [Skill composition](references/skill-composition.md)

## Skill Output

UTF-8 文案、Markdown 局部成品、删除决策或 JSON 辅助审计。输入参数包括 surface、
component、audience、moment、job、brand role、tone、constraints 与 visibility。

## Skill Version

0.2.0

## Ethical Considerations

不虚构受众研究、评价、产品承诺、权利状态、紧迫性、法律保证或用户同意；内部语境
与制作信息不进入公开文案，除非法律、版权或透明度要求必须披露。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录 2026-08-30 公众号艺术首图 Caption 的真实
Input → Prompt → Output：最优结果不是润色制作说明，而是删除可见 Caption，并把
作者、作品、年代留给必要归属位置。

### Dimension Map

机器卡记录语境适配、可见性完整性、品牌一致性、组件惯例、事实与克制五个维度；
不制造无证据分数。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。当前为免费本地基础能力。

### Distribution

本地安装已验证；GitHub、LovStudio、WorkBuddy 与 SkillPay 均未发布或上传。
