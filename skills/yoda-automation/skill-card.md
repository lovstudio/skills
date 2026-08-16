# Skill Card — lov-yoda-automation

## Description

配置、修复、核验和停用 Yoda 原生自动化，并以保存后的计划与运行记录作为完成证据。

## Owner

LovStudio · Lovstudio.AI

## License

MIT；外部操作遵循用户当次明确请求。

## Use Case

适用于周期提醒、状态巡检、一次性计划修复和完成后自动化收口。

## Deployment Geography

全球；运行于支持原生 Automations 的 Yoda 环境。

## Requirements

Yoda 原生自动化能力；使用只读验证脚本时需要 Python 3.8+。

## Known Risks

- 单次时间误写为 cron：保存前后验证字段和 future next run。
- 双重提醒：优先编辑既有记录并停用替代计划。
- 应用退出：读取失败运行并区分历史证据与修复后计划。

## References

- [Primary Skill instructions](SKILL.md)
- [Schedule contract](references/schedule-contract.md)
- [Machine-readable card](skill-card.yaml)

## Skill Output

Yoda 自动化记录与 JSON 核验结果，包含计划、时区、下次运行、最新运行和完成后停用规则。

## Skill Version

0.1.0

## Ethical Considerations

不写入凭据和私人路径；通知、外呼、支付和上传等外部动作只按用户明确范围执行。

## User Cases

见 [真实案例](cases/cases.json)。

## Dimension Map

计划正确性、去重控制和运行证据均记录在 [Skill Card](skill-card.yaml) 的 dimensions 中，并附有可回读证据。

## Pricing Basis

本地可靠性基础能力免费提供；边界和复评条件见 [pricing card](pricing-card.yaml)。

## Distribution

当前仅本地安装。WorkBuddy、SkillPay、GitHub 与 LovStudio 渠道均未发布。
