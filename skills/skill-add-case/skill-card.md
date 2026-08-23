# Skill Card — lov-skill-add-case

## Description

把一次已明确认可的 Skill 结果变成真实、脱敏、可回读的公开案例。

## Owner

LovStudio Skill contributors；维护入口为源仓库。

## License

MIT，详见 [`LICENSE`](LICENSE)。

## Use Case

适合在一次 Skill 调用完成并由用户明确确认满意后，补充该 Skill 的公开证据。

## Deployment Geography

本地工作区全球可用；公开同步使用 GitHub 与 LovStudio 官网。

## Requirements / Dependencies

本地需要 Python 3.10+ 与 PyYAML。公开同步沿用目标仓库与官网已有权限。

## Known Risks and Mitigations

- 未获用户认可：硬性验收门阻止写入。
- 泄露私有信息：高风险模式检查、隐私说明与最终 diff 审查。
- 把 push 当上线：公开 JSON 指纹和官网详情页双回读。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Case contract](references/case-contract.md)

## Skill Output

一个带稳定 ID、真实 Input → Prompt → Output 与验收证据的案例；公开目标另有
raw JSON 指纹、官网 HTTP 状态和页面 marker 证据。

## Skill Version

0.1.0

## Ethical Considerations

只发布得到明确认可且可脱敏公开的事实，不制造评价、指标、文件或上线状态。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：首案来自创建本 Skill 的真实需求。

### Dimension Map

`skill-card.yaml` 记录 evidence integrity、privacy、mutation safety 与 live
truthfulness 四个维度及其证据状态。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。该 Skill 免费，用于提高整个 Skill
目录的案例可信度。

### Distribution

WorkBuddy 与 SkillPay 不计划上架；GitHub 与 LovStudio 初始发布前保持 pending，
只有公开回读完成后才改为 live。
