# Changelog

## [0.2.3] - 2026-10-31

### Fixed

- compatibility 按 Agent Skills 规范从 metadata 移到 SKILL.md frontmatter 顶层；scripts/validate_skill.py 的 frontmatter 白名单同步加入 compatibility，否则顶层字段会被拒绝
- README 补上 npx skills add lov-ataru-indexing -g -y 安装命令，源码软链接安装保留为备选

## [0.2.2] - 2026-10-31

### Fixed

- 修复「报 ready 但已过期」被当成就绪：status / ensure 按 Ataru 的 previous_entry_matches_source 规则比对 manifest 与会话文件，输出 indexStale、pendingSessions、removedSessions、indexedAt；有漂移时 ensure 执行不带 --force 的 catch-up-build
- needsBuild 改为「不可检索或已过期」；构建后重新比对，剩下的 pendingSessions 是构建期间写入的会话
- 取数范围与 Ataru 0.41.x 一致：Claude 只取项目顶层 *.jsonl（不含 agent-*），Codex 只取 .jsonl；Ataru 无法归属的 Codex 会话不比 manifest 新时不计入漂移

## [0.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.2.0 之上
- 本地改动：统一展示名为「Ataru 索引」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.0

- Initial local Skill source.
