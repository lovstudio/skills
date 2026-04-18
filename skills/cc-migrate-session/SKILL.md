---
name: lovstudio:cc-migrate-session
description: Recover Claude Code session history lost after a project folder moved or was renamed. 项目迁移后 claude --resume / cc --resume 找不到历史会话时用此 skill 迁移 session 存储。
when_to_use: |
  User mentions project moved/renamed AND old or new absolute path. Examples:
  - "本项目之前是在 X" / "这个项目原来在 X" / "我把项目搬到了 X" / "项目迁移到了 X"
  - "this project used to be at X" / "moved the repo to X" / "renamed the folder"
  - "claude --resume 找不到" / "cc --resume 找不到历史" / "恢复旧会话"
  NOT for file/function/branch renames — only project root dir moves.
license: MIT
compatibility: claude-code
---

# lovstudio:cc-migrate-session

Moves the session store `~/.claude/projects/<slug>/` from the old path-slug to the new one and rewrites every `"cwd"` field inside the jsonl files. After this, `claude --resume` from the new directory will see all prior sessions.

## When to Trigger

**YES** — invoke this skill when:
- User says the project folder moved / was renamed at the filesystem level
- User mentions both FROM and TO paths, OR mentions one and the current cwd implies the other
- User complains that `claude --resume` no longer shows history after moving a folder
- User wants to "recover" sessions from a path they used to work in

**NO** — don't invoke when:
- User is renaming a file, function, variable, or branch (not the project root)
- User is asking a general question about CC's storage model (just explain, don't migrate)
- Paths are ambiguous — ask first

## Workflow

### Step 1 — Gather FROM and TO

Infer from the conversation first. Typical patterns:

| User said | FROM | TO |
|-----------|------|----|
| "我把项目从 /a 搬到了 /b" | /a | /b |
| "this project used to be at /old" (in new cwd) | /old | `process.cwd()` (current) |
| "本项目已迁移到 /new" (in old cwd) | `process.cwd()` (current) | /new |
| "I renamed ~/foo to ~/bar" | ~/foo | ~/bar |

If either side is ambiguous, **ask once** with `AskUserQuestion`. Don't guess.

**Always** expand `~` and resolve to absolute paths before running the CLI.

### Step 2 — Run dry-run + json to preview

```bash
npx -y @lovstudio/cc-migrate-session <FROM> <TO> --dry-run --json
```

Parse the JSON. Tell the user:
- How many sessions were found
- Total size
- Warn if `toDirExists` is true (destination slug dir already exists — merge risk)
- Show the FROM and TO slugs so the user can sanity-check the path mapping

If `sessionCount === 0`, stop. Tell the user either (a) the FROM path is wrong, or (b) CC never ran there. Do NOT proceed.

### Step 3 — Confirm with user

Use `AskUserQuestion` (or inline yes/no) asking: "Migrate N sessions from <FROM> to <TO>?"

Only proceed on explicit yes.

### Step 4 — Execute

```bash
npx -y @lovstudio/cc-migrate-session <FROM> <TO> --yes --json
```

Parse `phase: "done"` output. Extract:
- `rewrites` (total cwd lines changed)
- `restartHint.cd` and `restartHint.command`

### Step 5 — Tell user to restart CC

Output something like:

```
✓ Migrated N session(s), rewrote M cwd lines.

To load them, restart Claude Code in the new location:

  cd <TO>
  claude --resume

(The original session dir at ~/.claude/projects/<old-slug>/ is untouched —
you can delete it after verifying the new location works.)
```

**IMPORTANT**: The CURRENT Claude Code session (the one running this skill) cannot "switch" its own cwd mid-session. The user must exit and re-invoke `claude` from the new directory. State this clearly.

## CLI Reference

`npx -y @lovstudio/cc-migrate-session <FROM> <TO> [options]`

| Option | Purpose |
|--------|---------|
| `-y`, `--yes` | Skip confirmation prompt |
| `--dry-run` | Show plan, don't write |
| `--json` | Machine-readable output (use this from the skill) |
| `--projects-dir <dir>` | Override CC projects dir (default `~/.claude/projects`) |

## Slug Rule (FYI)

CC computes the slug by replacing every non-alphanumeric character with `-`. So:
- `/Users/mark/my-project` → `-Users-mark-my-project`
- `/Users/mark/.claude` → `-Users-mark--claude` (double `-` because `.` is non-alnum)
- `/Users/mark/@手工川` → `-Users-mark-----` (one per `@` and each CJK char)

The CLI handles this automatically — don't try to hand-compute it.

## Safety

- The old dir is NEVER deleted by this skill. It's a copy-then-rewrite, not a move.
- Tell the user to verify `claude --resume` works in the new location before rm'ing the old slug dir.
- If destination slug dir already exists, the CLI merges (overwriting conflicting jsonls). Warn the user.
