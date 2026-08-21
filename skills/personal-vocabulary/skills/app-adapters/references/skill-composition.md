# Skill Group Composition

## Nearby Skills Inspected

- lov-personal-vocabulary（父 Kit）：core atom，本模块是其 app-adapters 阶段。
- lov-canonical-store：上游 atom，提供规范词库。
- lov-sync-plan：下游 atom，消费本模块读到的 App 词条。
- 无其它 Skill 提供跨 App 词库字段映射。

## Atomic Handoffs

| 方向 | 输入产物 | 所属 | 输出产物 | 验收边界 |
|---|---|---|---|---|
| 上游 | 规范词库 | canonical-store | 目标 App 格式文件 | 字段映射符合 App 真实结构 |
| 下游 | App 词条 | sync-plan | 同步差异计划 | 分类正确 |

无外部 sibling 硬依赖。

## Overlap Decisions

各 App 适配器（openless/typeless/capcut）是同一模块内的声明式映射表，不拆成多个 sibling Skill，避免重复。

## Composition Decision

本文件是自包含 Kit 内的一个模块（app-adapters），不是独立可分发 Skill。它只负责字段映射与 App 读写；规范词库与同步决策交给同 Kit 的其它模块。
