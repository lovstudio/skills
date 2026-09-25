# 终端快捷指令 · Shell Shortcuts

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

Add a zsh alias / function to `~/.zshrc` idempotently. Supports ASCII
names (`zxsd`, `gs`) and 中文 function names (`中信书店`).

Part of [skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add zsh-alias -g -y
```

Requires: Python 3.8+ (stdlib only). zsh.

## Usage

Add a 中文 trigger that runs `claude` with a prompt, plus an English shortcut:

```bash
python3 scripts/add_alias.py \
  --name 中信书店 \
  --also-as zxsd \
  --cmd 'claude "用一句温暖、具体、不肉麻的话让我开心，20字以内"' \
  --comment '中信书店 → 启动 claude 说一句开心话'

source ~/.zshrc
```

Then either `中信书店<Enter>` or `zxsd<Enter>` triggers it.

Add a simple ASCII alias:

```bash
python3 .../add_alias.py --name gs --cmd 'git status' --simple
```

Remove an entry:

```bash
python3 .../add_alias.py --name 中信书店 --cmd unused --remove
```

## How it works

Each entry is wrapped in sentinel markers. Re-running with the same
`--name` updates in place — no duplicates:

```
# >>> lov-zsh-alias >>> 中信书店
# 中信书店 → 启动 claude 说一句开心话
中信书店() { claude "..." }
zxsd() { 中信书店 "$@" }
# <<< lov-zsh-alias <<< 中信书店
```

zsh supports CJK function names natively, no quoting tricks needed.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--name` | (required) | Trigger name; ASCII or 中文 |
| `--cmd` | (required) | Shell command to run |
| `--also-as` | none | Extra alias names (repeatable) |
| `--comment` | empty | Comment line above the block |
| `--simple` | off | `alias=` form (ASCII only) |
| `--rcfile` | `~/.zshrc` | Target rc file |
| `--dry-run` | off | Print, don't write |
| `--remove` | off | Remove the entry for `--name` |

## Heads-up

Shell aliases require pressing **Enter**. If you want a trigger that fires
the moment you finish typing a word (no Enter), you need an input-method
shortcut or Hammerspoon — not this skill.

## User Configuration

Set `SKILL_ZSH_ALIAS_RCFILE` to change the default rc file. `--rcfile`
still takes precedence.

## License

MIT
