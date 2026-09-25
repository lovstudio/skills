# Skill Group Composition

本记录是每个生成 Skill 的必需部分，防止相邻 Skill 变成意外重复或隐藏依赖。

## Nearby Skills Inspected

| Skill | 路由契约 | 与本 Skill 关系 |
|---|---|---|
| `lov-find-logo` | 查找品牌 Logo 资产（文件/URL） | 不相关 — 找的是设计资产而非项目目录 |
| `lov-memory-search` | 搜索知识库（memory + distill） | 不相关 — 搜的是记忆内容而非文件系统路径 |
| `lov-search-chat` | 从 Ataru 索引召回历史会话上下文 | 不相关 — 召回的是对话内容；本 Skill 从聊天记录提取路径定位目录 |
| `lov-finder-action` | 生成 Finder 右键菜单 | 不相关 — 生成 UI 扩展，非定位能力 |
| `lov-repo-takeover` | 把 clone 的仓库转为自己的 GitHub 仓库 | 下游可选交接 — 定位到仓库路径后，若用户要接手该仓库可转给它 |

## Atomic Handoffs

- 下游（可选）：`lov-repo-takeover`
  - 交接物：`<绝对项目路径>`
  - 调用边界：仅在用户明确表达要接手/改写目标仓库时提及
  - 验收标准：目标路径指向一个 git 仓库，且用户主动要求接管

除上述可选交接外，本 Skill 无上游依赖、无下游依赖，不创建任何外部 sibling
依赖。

## Overlap Decisions

- 与 `lov-memory-search` / `lov-search-chat` 的边界：它们返回「记忆/会话内容」，
  本 Skill 返回「文件系统路径」。若用户问的是「当时讨论了什么」用它们；问的是
  「目录在哪」用本 Skill。二者不构成功能重复。
- 与 `lov-find-logo` 无重叠：对象类型完全不同（设计资产 vs 项目目录）。

## Composition Decision

**Single Skill**。一个用户可见结果（定位路径）+ 一个确定性本地 CLI
（`scripts/find_project.py`），各层搜索共用同一查询归一化与评分逻辑，没有需要
独立输入/输出契约的阶段，故无需 Skill Kit。四层搜索是同一 CLI 的 scope 参数，
不是独立模块。
