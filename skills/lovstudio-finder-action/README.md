# lovstudio:finder-action

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

Generate Mac Finder right-click menu actions. Automator Quick Actions for file/folder menus, Finder Sync Extensions (Swift) for blank-space menus. Auto-detects which mode to use.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:finder-action
```

Requires: macOS 14+, Xcode (for Mode B), `brew install xcodegen` (for Mode B)

## Usage

```
/lovstudio:finder-action pdf2png .pdf 将PDF转PNG
/lovstudio:finder-action 新建md文件 空白处右键创建markdown
```

## Modes

| Trigger | Mode | Tech |
|---------|------|------|
| Right-click file/folder | Quick Action | Automator workflow |
| Right-click blank space | Finder Extension | Swift + xcodegen |
