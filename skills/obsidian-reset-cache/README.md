# lov-obsidian-reset-cache

![Version](https://img.shields.io/badge/version-1.1.0-CC785C)

Reset Obsidian cache to fix "Loading cache..." hang issue.

Part of [skill-publisher/skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add obsidian-reset-cache -g -y
```

No dependencies required (shell commands only).

## Usage

Say any of these to trigger:

- "obsidian 卡住了"
- "obsidian loading cache"
- "重置 obsidian 缓存"

## What It Does

1. Checks if Obsidian is running (prompts to close if so)
2. Deletes `~/Library/Application Support/obsidian/IndexedDB/`
3. Optionally creates `.obsidianignore` to prevent future issues

## Platform

macOS only.

## Safe Operations

- Does NOT delete notes, plugins, or settings
- Only removes the index cache (will be rebuilt on next launch)

## License

MIT
