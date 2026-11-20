# Changelog

## [0.1.3] - 2026-11-20

### Fixed

- README 的安装命令改为 `npx lovstudio skills add lovpen-add-wechat-channel-comp -g -y`：不带斜杠的名字会被 `npx skills add` 当作 git 源，报 repository does not exist，装不上。

## [0.1.2] - 2026-09-07

### Added

- 统一展示名为「视频号组件」，保持调用 ID 与能力契约。

## 0.1.1

- Matched the native WeChat Channels card presentation with centered sizing, a visible play control, and an overlaid identity row.
- Prevented the Channels nickname from leaking below the video cover in local HTML previews.

## 0.1.0

- Added deterministic parsing for one native `mp-common-videosnap` DOM or Lovpen DSL.
- Added canonical Markdown and native HTML rendering with exact-marker atomic insertion.
- Added six focused tests, a real user-provided component case, Skill Card, pricing basis, and local distribution records.
