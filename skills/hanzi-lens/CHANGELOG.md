# Changelog

## [0.2.2] - 2026-10-31

### Fixed

- 恢复 2026-08-09 去品牌化误改的配置解析：默认 profile 从字面量 `${SKILLS_CONFIG_DIR}/profile.json` 回到 `~/.lovstudio/skills/profile.json`；共享安装目录变量从 `SKILL_SKILLS_INSTALL_DIR` 回到 `LOVSTUDIO_SKILLS_INSTALL_DIR`（替换前原值见 d0f62e0^，与 lov-skill-creator 4.6.8 一致）
- SKILL.md、README 安装命令与 user-config 的变量名、profile 路径同步恢复
- 新增 tests/test_config_resolution.py

## [0.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.2.0 之上
- 本地改动：统一展示名为「汉字镜」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.0 — 2026-07-28

- Initial public release.
- Added Unicode and IVS validation.
- Added deterministic font-coverage checks with fontTools.
- Added portable research-project scaffolding.
- Added source-linkage, character-scope, and release audits.
- Added delegated professional infographic scaffold, render, and audit flow.
- Added the audited “翕” reference case.
