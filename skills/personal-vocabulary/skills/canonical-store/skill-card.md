# Skill Card — lov-canonical-store

## Description

维护规范个人词汇表 vocabulary.json 的结构与读写，支持按 phrase 去重合并与导入导出。

## Owner

LovStudio / 手工川工作室 — https://lovstudio.ai

## License / Terms

MIT；只维护用户自己的词库。

## Use Case

需要单一份统一词汇表的个人用户，建立、去重并导出规范词库。

## Deployment Geography

Global；本地 agent runtime。

## Requirements / Dependencies

Python 3.9+（仅标准库）。

## Known Risks and Mitigations

- 重复词条膨胀 → 按 phrase 精确去重。
- 字段映射错误 → 仅做映射，不改 canonical。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

JSON vocabulary.json，含 phrase/category/lang/enabled 等字段。

## Skill Version

0.1.0

## Ethical Considerations

仅处理用户自己的词库，不批量抓取。

## LovStudio Evidence

### User Cases

真实 21 条 OpenLess 词库 merge 后 0 重复、validate 0 错误。

### Dimension Map

- correctness（去重准确）：4
- effectiveness（单一来源）：4
- efficiency（幂等合并）：4

### Pricing Basis

免费，通用个人生产力工具。

### Distribution

free：github、lovstudio；paid：无。
