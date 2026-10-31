# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.5.4] - 2026-10-31

### Fixed

- CI 自 48d1455 起每次失败且 0 个 job（7 次运行）：validate.yml 调用的 skill-publisher/dev-skills 可复用工作流并不存在，同一工作流里的 audit 单测也随之未执行。改为在本仓库内运行 lov-skill-creator 的 validate_skill.py（固定到 976fb61），再跑 audit 单测
- README 安装命令改为 npx skills add lov-app-generator -g -y，插件市场改为 lovstudio/skills 的 dev-tools@lovstudio，移除已归档的 dev-skills 聚合包与 example.com 占位链接

### Changed

- 补齐 validate_skill.py 要求的 Skill 结构：description 精简到 200 字符内；Triggers 加中文触发语；新增 references/skill-composition.md；skill.yaml 的 context.profile 补全 schema、source、read、persist
- SKILL.md 压到 500 行以内：Step 7 的 CI/CD、部署与自动更新细节移到 references/cicd-deploy-updater.md（Tauri v2 updater pubkey 与不编造密钥两条规则仍留在正文）；User Configuration 改为指向 references/user-config.md；删去 Dependencies 里与 CLI Reference 重复的 --help 命令

## [0.5.3] - 2026-09-12

### Added

- UI 规则：所有面向用户的报错文本必须可选中、完整换行并提供一键复制，即使应用全局禁用了文本选择。来自 Lovshrink 视频库探测报错被截断且不可复制的反馈。

## [0.5.2] - 2026-09-07

### Added

- 统一展示名为「应用工坊」，保持调用 ID 与能力契约。

## [0.5.1] - 2026-09-06

### Fixed

- declare required Skill integrations with existing conditional workflow boundaries

## [0.5.0] - 2026-08-25

### Added

- add native macOS Finder Quick Action workflow
- distinguish Finder Quick Actions from Services and audit the Action Extension target, activation rule, presentation, and embedding

## [0.4.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.3.2] - 2026-08-14

### Changed

- make `lov-integrate-lovinsp` a mandatory default step for every frontend app
- require idempotent Lovinsp upgrades and supported `code-inspector` migration
- strengthen the audit to validate Vite plugin ordering and legacy dependency removal
- add regression tests for correct, misordered, and legacy Lovinsp configurations

## [0.3.0] - 2026-05-25

### Added

- add web-only app generation path
- add app-type audit profile for auto, web, and tauri checks
- document case-by-case framework selection for Vite, Next.js, PWA, and Tauri
- publish the skill from an independent source repository
- replace author-specific brand paths with portable user configuration

## [0.2.0] - 2026-05-24

### Added

- capture Tauri updater, lovinsp dev, and macOS icon lessons
- audit helper now checks updater pubkey and lovinsp plugin configuration
- brand rules now require padded Tauri icon sources for macOS visual alignment
