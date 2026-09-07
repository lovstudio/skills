# Changelog

## [1.6.2] - 2026-09-07

- 修正 README 的过期状态版本和本地安装路径，补充自然语言调用与官网安装命令。

## [1.6.1] - 2026-09-07

- 将历史 slash command 升级为通用 Skill，补全自然语言触发、显式输入、共享 Profile 与验收边界。
- 保留业务目的，修正宿主耦合和不安全的隐式动作；迁移案例与实际业务验收分别记录。


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

