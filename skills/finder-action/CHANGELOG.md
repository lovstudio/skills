# Changelog

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
