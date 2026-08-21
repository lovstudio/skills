# Skill Group Composition

## Nearby Skills Inspected

- lov-personal-vocabulary（父 Kit）：core atom，本模块是其 sync-plan 阶段。
- lov-canonical-store：上游 atom，提供规范词库。
- lov-app-adapters：上游 atom，提供 App 词条。
- 无其它 Skill 提供词汇同步差异规划。

## Atomic Handoffs

| 方向 | 输入产物 | 所属 | 输出产物 | 验收边界 |
|---|---|---|---|---|
| 上游 | 规范词库 | canonical-store | 差异计划 | 分类正确 |
| 上游 | App 词条 | app-adapters | 差异计划 | 分类正确 |

无外部 sibling 硬依赖。

## Overlap Decisions

与 memory 类 Skill 无重叠；同步差异是词汇表特有语义，不复制记忆检索逻辑。

## Composition Decision

本文件是自包含 Kit 内的一个模块（sync-plan），不是独立可分发 Skill。它只负责差异计算与计划；规范词库维护与 App 读写交给同 Kit 的其它模块。
