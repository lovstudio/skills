# lovstudio:cc-migrate-session (skill)

Claude Code skill that detects "project folder moved" situations and runs `@lovstudio/cc-migrate-session` (the npm CLI) to relocate the session history so `claude --resume` keeps working.

Invoked as `/lovstudio:cc-migrate-session` (or auto-triggered on matching phrases).

## Install

Symlink this directory into `~/.claude/skills/` (note: directory name must be `lovstudio-cc-migrate-session`):

```bash
ln -s ~/lovstudio/coding/cc-migrate-session/skill/lovstudio-cc-migrate-session \
      ~/.claude/skills/lovstudio-cc-migrate-session
```

Then restart Claude Code. The skill will be auto-triggered whenever you mention a project move.

## Trigger phrases

Chinese:
- 项目已经迁移到 /new/path
- 我把这个项目搬到了 /new/path
- 这个项目原来在 /old/path
- 换到 /new/path 了

English:
- this project moved to /new/path
- I relocated the repo to /new/path
- this project used to be at /old/path
- I renamed the folder from foo to bar

## What it does

1. Parses FROM and TO paths from the conversation (asks if ambiguous)
2. Runs `npx @lovstudio/cc-migrate-session <FROM> <TO> --dry-run --json` to preview
3. Shows you N sessions that will be migrated
4. On confirmation, runs with `--yes --json`, which copies the slug dir and rewrites every `"cwd"` line in the jsonl files
5. Prints `cd <TO> && claude --resume` for you to run

See `SKILL.md` for the full workflow and CLI reference.
