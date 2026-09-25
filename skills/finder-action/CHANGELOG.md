# Changelog

## [0.4.3] - 2026-09-25

### Fixed

- 恢复缺失的 `references/automator-template.xml`：单个 Run Shell Script action（`inputMethod=1` 经 `"$@"` 传参、`/bin/bash`、fileSystemObject 输入、servicesMenu、`presentationMode=15`、无输出）；`AMAccepts` 按系统 action 定义对齐为 `com.apple.cocoa.string`。
- 新增 `references/automator-info-template.xml`（`NSServices`），使 `pbs -update` 无需打开 Automator 即可注册服务。
- 新增「Quick Action 安装」流程：staging 目录内用 `plutil -replace` 注入脚本与菜单名，`plutil -lint` 与往返 diff 校验后 `mv -n` 安装并 `pbs -update`；保留不覆盖同名、不 `killall Finder`、不自动打开 Automator，并给出回退路径。
- Workflow Step 2 的模板引用改为 Markdown 链接，模板缺失会被 `validate_skill.py` 拦截。
- 同步 `skill-card.md` / `skill-card.yaml` 版本；`skill-composition.md` 注明 `lov-skill-publisher` 的安装别名 `lov-skill-publish`。

## [0.4.2] - 2026-09-07

### Added

- 统一展示名为「Finder 快捷动作」，保持调用 ID 与能力契约。

## [0.4.1] - 2026-09-07

- 将历史 slash command 升级为通用 Skill，补全自然语言触发、显式输入、共享 Profile 与验收边界。
- 保留业务目的，修正宿主耦合和不安全的隐式动作；迁移案例与实际业务验收分别记录。


## [0.3.0] - 2026-04-15

### Added

- Add helper app pattern to bypass sandbox restrictions
- Document NSMenuItem.target requirement
- Document NSHomeDirectory() sandbox behavior
- Document Bundle ID naming restrictions
- Update example to OpenCC with helper app

## [0.2.1] - 2026-04-14

### Fixed

- Fix sandbox entitlements: use temporary-exception.files.absolute-path.read-write instead of files.user-selected.read-write
- Document sandbox-must-be-on requirement in SKILL.md and known limitations
- Update xcodegen-template.yml with correct entitlements

## 0.2.0 — 2026-04-13

- Added Mode B: Finder Sync Extension for blank-space right-click menus (Swift + xcodegen)
- Auto mode detection based on keywords (空白处/background → Extension, otherwise → Quick Action)
- Added xcodegen template, FinderSync.swift template, AppDelegate template
- Full build-install-register pipeline (xcodegen → xcodebuild → pluginkit)
- Documented known limitation: menu item position controlled by system

## 0.1.0 — 2025-01-01

- Initial release: Automator Quick Action mode for file/folder context menus
