# lov-cc-mv (skill)

Claude Code skill that moves a project folder and migrates all its CC state in one shot — session store, prompt-up-arrow history, and running-session records — so `claude --resume` keeps working after the move.

Invoked as `/lov-cc-mv` (or auto-triggered on matching phrases). Wraps `@lovstudio/cc-mv` (the npm CLI).

## Install

Symlink this directory into `~/.claude/skills/`:

```bash
ln -s ~/lovstudio/coding/cc-mv/skill/lov-cc-mv \
      ~/.claude/skills/lov-cc-mv
```

Then restart Claude Code.

## Trigger phrases

Prospective move (we do the mv for you):
- 把这个项目移到 /new/path
- 把项目从 /a 搬到 /b
- rename this folder to /new/path
- mv this repo to /new/path

Post-move recovery (folder already moved; use `--no-mv`):
- 项目已经迁移到 /new/path
- 这个项目原来在 /old/path
- this project used to be at /old/path
- claude --resume 找不到历史

## What it does

1. Parses FROM and TO from the conversation (asks if ambiguous)
2. Runs `npx @lovstudio/cc-mv <FROM> <TO> --dry-run --json` to preview
3. Shows affected slug count (including sub-dirs with their own CC history)
4. On confirmation, runs with `--yes --json`:
   - `fs.renameSync(FROM, TO)` (or shell `mv` for EXDEV)
   - Rewrites `~/.claude/projects/<slug>/*.jsonl` for every affected slug
   - Rewrites `~/.claude/history.jsonl` and `~/.claude/sessions/*.json`
5. Prints `cd <TO> && claude --resume` for you to run

See `SKILL.md` for the full workflow and CLI reference.
