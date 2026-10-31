# Changelog

## [0.4.3] - 2026-10-31

### Fixed

- 恢复 2026-08-09 去品牌化误改的共享 profile 路径：`media_config.py` 默认读写 `~/.lovstudio/skills/profile.json`（替换前原值见 d74b1e9^）
- 切换前已核对：~/.skill-publisher/skills/profile.json 的 media_fetch 多出的 7 个键都等于代码默认值，两份解析结果相同；该文件保留不动
- 新增 scripts/test_media_config.py，覆盖默认路径与 init --write 只改 media_fetch 段

## [0.4.2] - 2026-09-07

### Added

- 统一展示名为「影视寻宝」，保持调用 ID 与能力契约。

## [0.4.1] - 2026-09-07

### Fixed

- 统一展示名称为「媒体检索下载」，保留原有调用 ID 与能力边界。

## [0.4.0] - 2026-08-26

### Added

- make aria2 the primary transport backend
- treat qBittorrent as an optional search, queue-management, and seeding adapter
- support direct HTTP inputs, opaque output names, RPC progress, and job-specific ports in aria2 acquisition
- detect RPC-resident completion through aria2.tellStopped and terminate the worker cleanly
- migrate legacy transport preferences and document the aria2-first workflow

## [0.3.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.2.0

- Added an aria2 fallback runner with DHT, PeX, LSD, bounded trackers, `.aria2`
  continuation state, bounded restarts, and structured transport events.
- Separated advertised source health from live probe evidence and final verification.
- Added a Simplified Chinese subtitle handoff with exact-release matching, UTF-8 SRT
  preservation, and explicit opt-in boundaries for learning gloss and ASS output.
- Added the LovStudio Skill Card, pricing card, sanitized evidence bundle, and the
  《指环王》三部曲 user case.

## 0.1.0

- Added a four-module discovery, selection, acquisition, and verification Skill Kit.
- Added portable media preferences and a default download destination.
- Added qBittorrent search, ranking, capacity preflight, parallel probing, stall recovery, and media verification helpers.
