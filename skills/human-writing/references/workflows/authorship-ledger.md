# Authorship Ledger Workflow

这是 `lov-human-writing` 的内部阶段，不是可独立发现或调用的 Skill。

## 输入

- 原始材料或待改稿；
- 用户明确给出的判断、经历、边界与禁编要求；
- `references/authorship-integrity.md`。

## 步骤

1. 完整读取材料，不从摘要或标题猜作者意图。
2. 建立 `source_question`、`author_positions`、`firsthand_evidence`、
   `editorial_decisions`、`counterevidence`、`open_questions`、
   `preserve_verbatim` 与 `forbidden_inventions` 八类字段。
3. 每项记录来源位置与确定程度；推断值标为推断，不冒充作者原话。
4. 缺失项保持缺失。只有它会改变核心立场或造成虚构时才问一个聚焦问题。
5. 输出精简内部账本给后续篇章审计；引语、术语和原始数据逐字不变。

用户只要表层指标时可以跳过本阶段，但必须明确这不构成作者性验收。
