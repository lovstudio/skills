# Skill Card — lov-skill-add-case

## Description

把一次已明确认可的 Skill 结果变成公开摘要，并把脱敏后的完整 Session 作为目标
Skill 售价 1/10 的付费证据上传、关联和回读。

## Owner

LovStudio Skill contributors；维护入口为源仓库。

## License

MIT，详见 [`LICENSE`](LICENSE)。

## Use Case

适合在一次 Skill 调用完成并由用户明确确认满意后，补充该 Skill 的公开证据。

## Deployment Geography

本地工作区全球可用；公开同步使用 GitHub 与 LovStudio 官网。

## Requirements / Dependencies

本地需要 Python 3.10+、PyYAML 与 `lov-share-session`。Session 上传需要 LovStudio
账号；公开同步沿用目标仓库与官网已有权限。

## Known Risks and Mitigations

- 未获用户认可：硬性验收门阻止写入。
- 泄露私有信息：高风险模式检查、隐私说明与最终 diff 审查。
- 客户端伪造价格：只接受服务端按目标 Skill 售价计算并返回的 Credits 价格。
- 把 push 当上线：公开 JSON 指纹和官网详情页双回读。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Case contract](references/case-contract.md)

## Skill Output

一个带稳定 ID、真实 Input → Prompt → Output、验收证据和付费 Session 链接的案例；
公开目标另有 raw JSON 指纹、官网 HTTP 状态和付费墙 marker 证据。

## Skill Version

0.2.2

## Ethical Considerations

只发布得到明确认可的公开摘要与脱敏 Session，不制造评价、价格、指标、文件或上线状态。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：首案来自创建本 Skill 的真实需求。

### Dimension Map

`skill-card.yaml` 记录 evidence integrity、privacy、mutation safety、paid session
integrity 与 live truthfulness 五个维度及其证据状态。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。该 Skill 免费，用于提高整个 Skill
目录的案例可信度。

### Distribution

WorkBuddy 与 SkillPay 不计划上架。GitHub 已发布 `v0.1.0`；`v0.2.2` 目前仅在本地
完成实现，尚未发布或部署。
