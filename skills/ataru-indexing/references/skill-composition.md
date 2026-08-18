# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Relation |
| --- | --- | --- |
| `lov-ataru-search` | 从本地 Ataru 记忆里召回过去的会话上下文，返回带稳定标识的命中与原文片段 | downstream atom |
| `lovstudio:release-via-cicd` | 幂等发布流程：changeset、bump、tag、CI 监控 | not composed |
| `lov-better-github-desc` | 依据 README 更新仓库描述与话题 | not composed |
| `lov-skill-creator` | 生成、校验并本地安装 Skill 源码 | not composed（它创建了本 Skill，不参与运行） |

检查依据是各自的输入/输出契约，不是名字：只有 `lov-ataru-search` 消费本 Skill
产出的状态。

## Atomic Handoffs

- **downstream —— `lov-ataru-search`**
  - 输入制品：一次 `ataru index status` 的结果，`searchAvailable: true`。
  - 交接边界：本 Skill 负责「索引可被检索」，不负责命中质量与排序。
  - 验收归属：`lov-ataru-search` 自己再确认一次状态，未就绪时报
    `ATARU_INDEX_NOT_READY` 并指回本 Skill；它不会替用户偷偷构建索引。
- **upstream** —— 无。索引的输入是用户机器上已存在的会话文件，不需要前置 Skill。

## Overlap Decisions

`lov-ataru-search` 也会读取索引状态，但只读、只用于拒绝一次错误的检索，不构建、
不重建、不等待。构建这一侧的所有权完整留在本 Skill，两者没有需要合并的重叠。

## Composition Decision

Single Skill。用户要的是两个独立可触发的动作：把索引搞好，以及去检索。它们的
输入输出契约不同、失败模式不同、耗时相差两个数量级（分钟级构建 vs 秒级查询），
不属于同一个用户可见结果，因此不做成 Kit。为保持可移植，约一百行的二进制解析
逻辑在两个 Skill 中各自自带，而不是引入 sibling 依赖。
