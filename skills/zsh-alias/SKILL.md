---
name: lov-zsh-alias
description: >
  Add a zsh alias / function to the user's ~/.zshrc, idempotently and safely.
  Supports both ASCII names (e.g. `gs`, `zxsd`) and 中文 function names
  (e.g. `中信书店`) — zsh fully supports CJK function identifiers.
  Trigger when the user says: "加个 alias", "加一个别名", "做个快捷命令",
  "我想输入 X 就执行 Y", "alias for X", "shortcut for X", "shell alias",
  or asks to wrap a command behind a single trigger word.
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only). zsh on macOS / Linux.
  Uses SKILL_ZSH_ALIAS_RCFILE or ~/.zshrc by default; pass --rcfile for
  other shells' rc.
metadata:
  author: contributors
  version: "0.2.1"
  tags: [zsh, alias, shell, productivity]
---

# 终端快捷指令 · Shell Shortcuts

Append a zsh alias or function to `~/.zshrc` behind sentinel markers, so
re-running updates the entry in place instead of duplicating it. Works for
both English (`zxsd`) and 中文 (`中信书店`) trigger names.

## When to Use

- User wants to bind a trigger word to a shell command ("我输入 X 就跑 Y")
- User wants a 中文 trigger ("输入'中信书店'就启动 claude 说一句开心话")
- User wants multiple aliases pointing to the same command
- User wants to remove a previously-added alias

Do NOT use for:
- System-level shortcuts that need to fire without pressing Enter — that's
  an input-method or Hammerspoon job, not a shell alias. Tell the user.
- Non-zsh shells unless they explicitly pass `--rcfile`.

## Workflow (MANDATORY)

### Step 1: Ask the user (only what's missing)

Use `AskUserQuestion` to collect anything not already obvious from context.
Typical fields:

- **Trigger name(s)**: the word(s) the user types. Multiple OK.
- **Command**: the shell command to run. Quote carefully.
- **Style**:
  - `function` (default) — supports CJK names, supports passing args via `"$@"`
  - `simple alias` — only for ASCII names; uses `alias name='cmd'` form

If the user already gave the trigger + command in plain language ("中信书店
→ 启动 claude 说一句开心话"), skip the question and proceed.

### Step 2: Dry-run preview

```bash
python3 scripts/add_alias.py \
  --name <trigger> \
  --cmd '<shell command>' \
  --comment '<one-line explanation>' \
  [--also-as <other-trigger>] \
  --dry-run
```

Show the rendered block to the user.

### Step 3: Apply

Re-run without `--dry-run`. The script writes a sentinel-wrapped block to
`~/.zshrc`. Re-running with the same `--name` updates in place.

### Step 4: Tell the user to reload

```bash
source ~/.zshrc
```

Then they can type the trigger + Enter.

### Removing an alias

```bash
python3 scripts/add_alias.py \
  --name <trigger> --cmd unused --remove
```

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--name` | (required) | Trigger word; ASCII or 中文 |
| `--cmd` | (required) | Shell command to run |
| `--also-as` | none | Extra alias name(s); repeatable |
| `--comment` | empty | Comment line above the block |
| `--simple` | off | Use `alias=` form (ASCII names only) |
| `--rcfile` | `~/.zshrc` | Target rc file |
| `--dry-run` | off | Print, don't write |
| `--remove` | off | Remove the entry for `--name` |

## Block Format

Each entry is wrapped in sentinel markers so the script can find and update
it on re-run:

```
# >>> lov-zsh-alias >>> <name>
# <comment>
<name>() { <cmd> }
<also-as>() { <name> "$@" }
# <<< lov-zsh-alias <<< <name>
```

## Notes for Claude

- zsh supports CJK function names natively — no quoting trickery needed.
- shell aliases ALWAYS require pressing Enter. If the user expects "auto
  fire on typing", clarify upfront — they need an input method shortcut or
  Hammerspoon, not this skill.
- Don't `--simple` for CJK names; the script will reject it.
- The user must `source ~/.zshrc` (or open a new terminal) to pick up the
  new alias. Always say so after writing.

## User Configuration

Set `SKILL_ZSH_ALIAS_RCFILE` to change the default rc file. `--rcfile`
still takes precedence.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
