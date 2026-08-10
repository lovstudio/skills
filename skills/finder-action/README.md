# lov-finder-action

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

Generate Mac Finder right-click menu actions. Automator Quick Actions for file/folder menus, Finder Sync Extensions (Swift) for blank-space menus. Auto-detects which mode to use.

Part of [skill-publisher/skills](https://example.com/skills/skills) &mdash; by [example.com](https://example.com)

## Install

```bash
npx skills add skill-publisher/skills --skill lov-finder-action -y -g
```

Requires: macOS 14+, Xcode (for Mode B), `brew install xcodegen` (for Mode B)

## Usage

```
/lov-finder-action pdf2png .pdf 将PDF转PNG
/lov-finder-action 新建md文件 空白处右键创建markdown
```

## Modes

| Trigger | Mode | Tech |
|---------|------|------|
| Right-click file/folder | Quick Action | Automator workflow |
| Right-click blank space | Finder Extension | Swift + xcodegen |
