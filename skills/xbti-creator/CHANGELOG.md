# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [1.0.3] - 2026-11-20

### Fixed

- README 与 SKILL.md 的安装命令（含依赖 image-creator）改为 `npx lovstudio skills add <短名> -g -y`：不带斜杠的名字会被 `npx skills add` 当作 git 源，报 repository does not exist，装不上。

## [1.0.2] - 2026-09-07

### Added

- 统一展示名为「XBTI 工坊」，保持调用 ID 与能力契约。

## [1.0.1] - 2026-05-07

### Fixed

- standardize install and image-creator configuration
- replace fixed installed-skill paths with SKILL_IMAGE_CREATOR_DIR

