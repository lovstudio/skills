# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Relation |
| --- | --- | --- |
| `lov-ataru-indexing` | 检查并构建本机 Ataru 记忆索引，交回可判断的状态报告 | upstream atom |
| `lovstudio:release-via-cicd` | 幂等发布流程：changeset、bump、tag、CI 监控 | not composed |
| `lov-better-github-desc` | 依据 README 更新仓库描述与话题 | not composed |
| `lov-skill-creator` | 生成、校验并本地安装 Skill 源码 | not composed（它创建了本 Skill，不参与运行） |

检查依据是各自的输入/输出契约，不是名字：只有 `lov-ataru-indexing` 产出本 Skill
所需的前置制品。

## Atomic Handoffs

- **upstream —— `lov-ataru-indexing`**
  - 输入制品：一次 `ataru index status` 的结果，`searchAvailable: true`。
  - 交接边界：对方负责索引可被检索，本 Skill 负责召回质量与可引用性。
  - 验收归属：本 Skill 自己再确认一次状态。未就绪时报 `ATARU_INDEX_NOT_READY`
    并指回对方，**不**自行构建索引——分钟级的全量构建不应该藏在一次检索里发生。
- **downstream** —— 无固定下游。命中里的稳定标识是通用制品，任何调用方都能直接消费。

## Overlap Decisions

两个 Skill 都会读取索引状态，但读的目的不同：本 Skill 只读、只用于拒绝一次注定
错误的检索；构建、重建、等待并发构建的所有权完整留在 `lov-ataru-indexing`。这不是
需要合并的重叠，而是刻意保留的一次前置校验。

## Composition Decision

Single Skill。检索与索引构建是两个独立可触发的用户动作，输入输出契约不同、失败模式
不同、耗时相差两个数量级，不属于同一个用户可见结果，因此不做成 Kit。为保持可移植，
约一百行的二进制解析逻辑在两个 Skill 中各自自带，而不是引入 sibling 依赖。
