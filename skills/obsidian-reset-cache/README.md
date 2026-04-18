# lovstudio:obsidian-reset-cache

Reset Obsidian cache to fix "Loading cache..." hang issue.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:obsidian-reset-cache
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
