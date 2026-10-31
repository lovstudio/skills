# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.5.6] - 2026-10-31

### Fixed

- references/user-config.md 里重复的两行 SKILL_PROFILE_PATH 合并为一行：48d1455 的批量替换把 LOVSTUDIO_SKILLS_BRAND_PROFILE 与 LOVSTUDIO_SKILLS_PROFILE 改成了同一个名字，表里出现两行含义不同的同名变量；合并后写明它指向共享 profile JSON，品牌资产也从中解析

## [0.5.5] - 2026-10-31

### Fixed

- audit 的品牌检测关键词恢复为 lovstudio：48d1455 的去品牌化批量替换把它改成 skill-publisher，AGENTS.md / CLAUDE.md 里写着 Lovstudio 的项目不再被判为已接入 Warm Academic（行为回归）；补回归测试 test_detects_lovstudio_brand_in_local_instructions
- 默认共享 profile 路径恢复为 $HOME/.lovstudio/skills/profile.json（SKILL.md、README、references/user-config.md）：本机实际在用的共享 profile 就在这里，lov-skill-creator 的 profile_store.py 也优先解析它；环境变量名 SKILL_PROFILE_PATH 不变
- 同一次替换留下的品牌措辞按替换前原值恢复：品牌名按 BRAND-08 写作 Lovstudio.AI（含经确认的 Triggers 4 处），Configurable Academic 改回 Warm Academic，Brand scope 选项 brand-logo 改回 LovPen，metadata.tags 与 metadata.author 改回 lovstudio，LICENSE 版权方改回 lovstudio

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
