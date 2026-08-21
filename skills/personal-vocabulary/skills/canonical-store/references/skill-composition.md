# Skill Group Composition

## Nearby Skills Inspected

检查了与本模块相邻的能力：

- lov-personal-vocabulary（父 Kit）：core atom，本模块是其 canonical-store 阶段。
- lov-app-adapters / lov-sync-plan：下游 atom，分别消费本模块输出的规范词库。
- lov-memory-add / lov-memory-search：not composed，记忆存知识经验，与语音词条字段与用途不同。

## Atomic Handoffs

| 方向 | 输入产物 | 所属 | 输出产物 | 验收边界 |
|---|---|---|---|---|
| 上游 | app-adapters 解析出的外部词条 | app-adapters | 规范词库 entries | 按 phrase 去重、schema 校验通过 |
| 下游 | 规范词库 | sync-plan | 同步差异计划 | 字段映射一致 |

无外部 sibling 硬依赖。

## Overlap Decisions

与 memory 类 Skill 无重叠；词汇表是面向语音输入识别的词条，刻意分开。

## Composition Decision

本文件是自包含 Kit 内的一个模块（canonical-store），不是独立可分发 Skill。它只负责规范词库的结构、去重与导入导出；具体 App 读写与同步交给同 Kit 的其它模块。
