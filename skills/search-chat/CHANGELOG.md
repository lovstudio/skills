# Changelog

## [0.2.4] - 2026-10-31

### Fixed

- compatibility 按 Agent Skills 规范从 metadata 移到 SKILL.md frontmatter 顶层；scripts/validate_skill.py 的 frontmatter 白名单同步加入 compatibility，否则顶层字段会被拒绝

## [0.2.3] - 2026-10-31

### Fixed

- 修复按行号回读必然失败：read 改按 session read 返回的 line_number 匹配 --around，并以 lineNumber 输出
- search 与 index-status 比对 manifest 与会话文件：有漂移时给出 indexStale、pendingSessions、removedSessions，warnings 首条为 ATARU_INDEX_STALE，零命中不再与「没找到」混淆；--full 同样携带
- indexUpdatedAt 改取 manifest 的 indexedAt（上次构建完成时间）；原值是 CLI 读状态的时刻，恒为当前时间

## [0.2.2] - 2026-09-07

### Added

- 统一展示名为「会话寻踪」，保持调用 ID 与能力契约。

## [0.2.1] - 2026-08-31

- 修正 LovStudio 统一目录安装命令，按 runtime 名 `lov-search-chat` 选择 Skill。

## [0.2.0] - 2026-08-31

- 将用户可见 Skill 名从 `lov-ataru-search` 统一为 `lov-search-chat`。
- 迁移本地真源目录、Profile namespace、相邻索引 Skill 引用与安装入口。
- Ataru 仍是本 Skill 的本地检索后端，运行契约保持不变。
- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.0

- Initial local Skill source.
