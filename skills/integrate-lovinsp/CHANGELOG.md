# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [1.5.0] - 2026-08-20

### Changed

- 重命名 skill id：`lov-install-lovinsp` → `lov-integrate-lovinsp`
- 补充 build --watch 架构下的启用说明（`LOVINSP=1` 常驻 watch，一次性 build 会让 IDE 桥服务随进程退出而死）

## [1.4.0] - 2026-08-15

### Added

- 允许模型自动调用 lovinsp 集成
- 移除 disable-model-invocation，补全触发语与集成验证步骤

