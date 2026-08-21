# Skill Card — lov-sync-plan

## Description

比较规范词库与各 App 实际词条，产出 add/skip/conflict/app_only 同步计划，确认后再执行，默认不覆盖对方已有词条。

## Owner

LovStudio / 手工川工作室 — https://lovstudio.ai

## License / Terms

MIT；默认只做 add，不删除用户数据。

## Use Case

需要把规范词库同步到某款 App 并先审差异的用户，比对词库与 App 词条，生成同步计划。

## Deployment Geography

Global；本地 agent runtime。

## Requirements / Dependencies

Python 3.9+（仅标准库）。

## Known Risks and Mitigations

- 误判冲突覆盖 App 词条 → 默认只执行 add；conflict 与 app_only 需用户明确裁决。
- App 侧字段缺失导致误报 → 仅比较 App 实际携带的字段，缺失视为已同步。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

只读同步差异计划（add/skip/conflict/app_only）。

## Skill Version

0.1.0

## Ethical Considerations

默认不覆盖或删除用户已有词条；仅执行用户确认的写入。

## LovStudio Evidence

### User Cases

真实 21 条词库 diff 全部正确归为 skip，无误报 conflict。

### Dimension Map

- correctness（差异分类准确）：4
- effectiveness（审阅再写）：4
- efficiency（秒级 diff）：4

### Pricing Basis

免费，通用同步规划工具。

### Distribution

free：github、lovstudio；paid：无。
