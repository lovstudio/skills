# Skill Group Composition

本记录是每个生成 Skill 的必备项，用于避免相邻 Skill 变成意外重复或隐藏依赖。

## Nearby Skills Inspected

检查了本地 skill 源与已装 catalog 中与词汇/数据维护相关的 Skill：

| Skill | 路由契约 | 判定 |
|---|---|---|
| lov-memory-add / lov-memory-search | 知识库记忆（memory + distill），结构化知识存取 | not composed：词汇表是面向语音输入的词条，非通用知识库；字段与同步语义不同 |
| lov-better-project-structure | 项目结构优化 | not composed：无关 |
| lov-app-optimizer | 应用运行时性能 | not composed：无关 |
| lov-app-generator / lov-app-release | App 生成与发布 | not composed：无关 |
| lov-skill-creator | 创建/验证/安装 skill | upstream atom：本 Kit 由它生成与校验 |

未发现任何 Skill 已拥有"个人词表维护 + 跨语音输入法同步"这一用户可见结果。

## Atomic Handoffs

| 方向 | 输入产物 | 所属 | 输出产物 | 验收边界 |
|---|---|---|---|---|
| 上游 | skill-creator 生成的骨架 | skill-creator | 本 Kit 源码 | validate_skill.py 通过 |
| 核心 | canonical vocabulary.json | canonical-store | 去重后的规范词库 | 按 phrase 去重、schema 校验通过 |
| 下游 | 规范词库 | app-adapters | 各 App 格式文件 | 字段映射符合 App 真实结构 |
| 下游 | 规范词库 + App 词条 | sync-plan | 同步差异计划 | add/skip/conflict/app_only 分类正确 |

无外部 sibling 硬依赖：app-adapters 与 sync-plan 都作为内嵌 Kit 模块随源码提供。

## Overlap Decisions

- 与 memory 类 Skill 无重叠：记忆存"知识/经验"，词汇表存"语音输入要识别的词条"，字段与用途不同，刻意分开。
- 各 App 适配器（openless/typeless/capcut）是同一模块内的声明式映射表，不拆成多个 sibling Skill。

## Composition Decision

自包含 **Skill Kit**（canonical-store → app-adapters → sync-plan），因为三阶段为同一用户可见结果"跨 App 复用个人词库"强耦合：canonical 是唯一事实来源，adapter 负责字段映射，sync-plan 负责差异。任一阶段缺一，结果不完整。外部 sibling Skill 均为可选，未内嵌任何隐藏依赖。
