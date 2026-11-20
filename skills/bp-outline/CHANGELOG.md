# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.2.2] - 2026-11-20

### Fixed

- description 压到 200 字符以内（原 365），原有触发词全部保留；新增 `## Triggers` 小节并写明不触发条件；`metadata.tags` 改为列表；补 `compatibility`
- README 安装命令恢复为 `npx lovstudio skills add bp-outline -g -y`

## [0.2.1] - 2026-11-20

### Added

- 新增 `references/fa-content-triage.md`；定页序前先做内容取舍：主稿只放决定下一次见面的内容，支撑细节进附录，尽调记录、交易机制与估值依据不进 BP，并在 `outline.md` 末尾列出移走或未上页的内容

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill
