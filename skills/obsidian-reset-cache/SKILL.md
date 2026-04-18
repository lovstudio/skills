---
name: lovstudio:obsidian-reset-cache
category: Dev Tools
tagline: "重置 Obsidian 缓存，解决卡在 Loading cache 的问题。"
description: >
  重置 Obsidian 缓存，解决卡在 "Loading cache..." 的问题。
  当用户说 "obsidian 卡住"、"loading cache"、"obsidian 打不开"、"重置 obsidian 缓存" 时触发。
license: MIT
compatibility: >
  macOS only. Obsidian stores cache in ~/Library/Application Support/obsidian/.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: obsidian, cache, troubleshooting
---

# obsidian-reset-cache — 重置 Obsidian 缓存

解决 Obsidian 卡在 "Loading cache..." 无法启动的问题。

## When to Use

- Obsidian 启动时卡在 "Loading cache..." 不动
- Vault 文件数量多、有大量非 markdown 文件（如 node_modules）
- 怀疑缓存损坏

## Workflow

### Step 1: 确认 Obsidian 已关闭

```bash
pgrep -x Obsidian && echo "Obsidian 正在运行，请先关闭" || echo "OK: Obsidian 未运行"
```

如果 Obsidian 正在运行，提示用户先关闭。

### Step 2: 清除 IndexedDB 缓存

```bash
rm -rf ~/Library/Application\ Support/obsidian/IndexedDB/
```

### Step 3: 提示用户重新打开 Obsidian

告知用户：
1. 缓存已清除
2. 重新打开 Obsidian，首次加载会稍慢（重建索引）
3. 如果 vault 里有 node_modules 等大量非 markdown 文件，建议创建 `.obsidianignore` 文件排除

## Optional: 创建 .obsidianignore

如果用户的 vault 包含 node_modules 或其他应忽略的目录，帮用户在 vault 根目录创建：

```
node_modules
.git
.output
dist
build
```

## Notes

- 此操作仅影响 macOS
- 清除的是全局缓存，会影响所有 vault 的索引
- 不会删除用户数据、笔记、插件配置
