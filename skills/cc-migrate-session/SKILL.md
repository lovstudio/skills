---
name: lov-cc-mv
description: Move a project folder AND migrate all its Claude Code state in one shot — session store, prompt-up-arrow history, running-session records. Supports both directory-level moves AND session-level cherry-picking (by id, regex on first user prompt, or interactive picker). Use whenever the user wants to rename/move a project directory and keep `claude --resume` working, or wants to move a subset of chats from one project to another. 移动/重命名项目目录并迁移所有 CC 历史，或按 session 粒度把某个话题的对话搬到另一个项目。
when_to_use: |
  Directory-level — move/rename a project folder AND keep CC history working:
  - "把这个项目移到 X" / "把项目从 A 搬到 B" / "rename this folder to X" / "mv this repo to X"
  - "本项目之前是在 X" / "这个项目原来在 X" (post-move recovery — use --no-mv or the cc-migrate-session alias)
  - "claude --resume 找不到" / "cc --resume 找不到历史" / "恢复旧会话"

  Session-level — migrate only SOME chats from FROM to TO (not the whole dir):
  - "把 A 里关于 X 话题的 session 搬到 B" / "只搬这几个会话" / "migrate only the chats about ..."
  - "A 里的 session 我只想要其中几个" / "split these sessions out into a new project"
  - User names a specific session id or describes session content to filter by

  NOT for file/function/branch renames — only project root dir moves.
license: MIT
compatibility: claude-code
metadata:
  version: "0.3.0"
---

# lov-cc-mv

Two modes in one tool:

**Directory-level** (default) — four things in one shot:

1. `mv FROM TO` on disk (fs.renameSync — instant, preserves everything)
2. Rewrites `~/.claude/projects/<slug>/*.jsonl` session store — including every sub-directory slug
3. Rewrites `~/.claude/history.jsonl` (prompt up-arrow recall)
4. Rewrites `~/.claude/sessions/*.json` (running-session records)

**Session-level** (opt-in, via `--session`/`--grep`/`--pick`) — migrate a subset of chats:

1. Copies only the selected `.jsonl` files from FROM's slug dir into TO's
2. Rewrites each file's `cwd` from FROM → TO
3. Rewrites only the matching running-session records
4. Does **not** touch `history.jsonl` or `fs mv` (project itself isn't being moved)
5. Sub-dir slugs are ignored (root only by design)

Old slug dirs and source sessions are left intact unless `--delete-source` is passed.

## When to Trigger

**YES — directory-level** when:
- User wants to move/rename a project folder (prospective move — we do the mv)
- User already moved the folder externally and CC lost history (post-move recovery — use `--no-mv` or the `cc-migrate-session` alias)
- Sub-dir sessions under FROM should come along (handled automatically)

**YES — session-level** when:
- User wants to migrate only *some* sessions from FROM to TO — identified by id, topic/content, or to be picked interactively
- User said "只搬这几个" / "those chats about X" / "not all of them"
- User needs to split one project's chat history across two projects

**NO** — don't invoke when:
- Renaming a file, function, variable, or branch (not the project root)
- General question about CC's storage model (explain, don't migrate)
- Paths are ambiguous — ask first

## Workflow

### Step 1 — Gather FROM and TO

| User said | FROM | TO |
|-----------|------|----|
| "把 /a 搬到 /b" / "mv /a to /b" | /a | /b |
| "rename ~/foo to ~/bar" | ~/foo | ~/bar |
| "this project used to be at /old" (cwd is the new location) | /old | `process.cwd()` |
| "本项目已迁移到 /new" (cwd is the old location) | `process.cwd()` | /new |

If either side is ambiguous, **ask once** with `AskUserQuestion`. Don't guess.

Always expand `~` and resolve to absolute paths before running the CLI.

### Step 2 — Decide directory-level vs session-level

Directory-level if:
- User said "move the whole project" / "rename the folder"
- User wants `fs mv` (the folder itself is moving on disk)
- User wants ALL sessions (including any sub-dir sessions) migrated

Session-level if:
- User said "only the sessions about X" / "just these chats" / "not all of them"
- User referenced sessions by content/topic or explicit id
- The folder itself should stay put (only CC state for a subset is moving)

### Step 3 — Session-level: resolve the session set

The key design point: **AI should auto-filter whenever possible, only prompt the user when ambiguous.**

1. Run:

   ```bash
   npx -y @lovstudio/cc-mv <FROM> --list-sessions --json
   ```

   Parse `sessions[*]` — each has `sessionId`, `firstUserPrompt`, `mtime`, `sizeBytes`, `messageCount`.

2. Match the user's intent against `firstUserPrompt` yourself:
   - If the topic is unambiguous (e.g. "about command vs skill" + exactly one session's prompt obviously matches) → pick it directly, proceed to Step 4 with `--session <id>` flags.
   - If a regex captures it cleanly (e.g. topic = "slash command") → use `--grep '<pattern>'` instead of passing ids.
   - If multiple sessions could match and you can't disambiguate from `firstUserPrompt` alone → show the user the shortlist and ask which ones.
   - If the user asked for interactive picking explicitly → run with `--pick` and let the CLI do the UX.

3. Exclude the current running CC session from the selection — it's the one the user is talking to you from right now, migrating it mid-conversation will break things. (Its `sessionId` matches the session file that was written to most recently; safer signal: ask the user to confirm if ambiguous.)

### Step 4a — Dry-run + json to preview (directory-level)

```bash
npx -y @lovstudio/cc-mv <FROM> <TO> --dry-run --json
```

Parse the JSON. Tell the user:
- Total sessions and affected slug count (`pairs[*]` with `sessionCount > 0`)
- If `pairs.length > 1`: flag that sub-directories also have CC history
- If `toDirExistsOnDisk` and FROM also exists: warn — CLI will refuse the fs mv
- If any `pairs[i].toSlugDirExists`: warn — destination slug dir will be merged

If `totalSessions === 0` AND the user wanted post-move recovery (FROM path doesn't exist): stop, tell them either (a) FROM path is wrong, or (b) CC never ran there.

### Step 4b — Dry-run + json to preview (session-level)

```bash
npx -y @lovstudio/cc-mv <FROM> <TO> --session <id> --session <id> --dry-run --json
# or
npx -y @lovstudio/cc-mv <FROM> <TO> --grep '<pattern>' --dry-run --json
```

The JSON's `sessionLevel: true`, `resolvedSessionIds: [...]`, and `pairs[0].sessionFilter: [...]` confirm which sessions will move.

Summarize for the user: "Will migrate N session(s): <first-prompt-excerpt of each>". Get confirmation before executing.

### Step 5 — Confirm

For directory-level with sub-dirs: ask "Found N sub-dir(s) with CC history. Migrate everything? [Y/n]" — default yes.

For session-level: always summarize the selected sessions (by first-prompt excerpt) and ask "Migrate these N session(s)?" — especially if you resolved them from a regex or topic match, so the user can catch false positives.

Also ask about `--delete-source` if the user said anything like "move" (vs "copy") — default to keeping source as safety net, only pass `--delete-source` when the user explicitly wants it.

### Step 6 — Execute

Directory-level:

```bash
npx -y @lovstudio/cc-mv <FROM> <TO> --yes --json
```

For post-move recovery (FROM already moved externally):

```bash
npx -y @lovstudio/cc-mv <FROM> <TO> --yes --no-mv --json
# OR equivalently:
npx -y @lovstudio/cc-migrate-session <FROM> <TO> --yes --json
```

Session-level:

```bash
npx -y @lovstudio/cc-mv <FROM> <TO> --session <id1> --session <id2> --yes --json
# or with regex:
npx -y @lovstudio/cc-mv <FROM> <TO> --grep '<pattern>' --yes --json
# optionally add --delete-source
```

Parse `phase: "done"`:
- `result.slugsMigrated`, `result.jsonlFilesWritten`, `result.cwdRewrites`
- `result.historyRewrites` (0 in session-level mode — expected)
- `result.runningSessionRewrites`
- `result.sourceSessionsDeleted` (only non-zero with `--delete-source`)
- `fsMvMethod`: `"rename"`, `"shell-mv"`, or `null` (session-level / --no-mv)
- `restartHint.cd` + `restartHint.command`

### Step 7 — Tell user to restart CC

Directory-level:

```
✓ Moved FROM → TO and migrated N session(s) across M slug dir(s).
✓ Also rewrote prompt history and running-session records.

Restart Claude Code in the new location:

  cd <TO>
  claude --resume

(The old slug dirs at ~/.claude/projects/<old-slug>* are untouched — delete
them once you've verified --resume works.)
```

Session-level:

```
✓ Migrated N session(s) from FROM to TO.
✓ Source sessions {kept as safety net | deleted}.

To resume one of the migrated sessions:

  cd <TO>
  claude --resume <session-id>
```

**IMPORTANT**: The CURRENT Claude Code session cannot "switch" its own cwd mid-session. The user must exit and re-invoke `claude` from the new directory. State this clearly.

## CLI Reference

`npx -y @lovstudio/cc-mv <FROM> <TO> [options]`
`npx -y @lovstudio/cc-mv <FROM> [<TO>] --list-sessions [--json]`

| Option | Purpose |
|--------|---------|
| `-y`, `--yes` | Skip confirmation prompt |
| `--dry-run` | Show plan, don't write |
| `--no-mv` | Skip the filesystem mv (only migrate CC state — post-move recovery) |
| `--json` | Machine-readable output (use this from the skill) |
| `--projects-dir <dir>` | Override CC projects dir (default `~/.claude/projects`) |
| `--session <id>` | Session-level: migrate only this id (repeatable) |
| `--grep <pattern>` | Session-level: migrate sessions whose first user prompt matches the regex (case-insensitive) |
| `--pick` | Session-level: interactive numbered picker |
| `--list-sessions` | Print session summaries and exit (pair with `--json` for scripting) |
| `--delete-source` | Delete migrated source sessions after copy+rewrite (default keeps them) |

### Backwards-compatible alias

`npx -y @lovstudio/cc-migrate-session <FROM> <TO>` — same tool, but defaults to `--no-mv` (only migrates CC state, doesn't touch the filesystem). Use when the user already moved the folder externally.

## Sub-directory Discovery (directory-level only)

CC's slug rule is: replace every non-`[A-Za-z0-9]` with `-`. So `FROM/sub` slugifies to `<fromSlug>-<subSlug>`.

The CLI lists `~/.claude/projects/` and takes every slug matching `slug === fromSlug || slug.startsWith(fromSlug + "-")`. That catches FROM and all descendants in one readdir. It then reads each slug's first jsonl to recover the original absolute sub-path (since slug → path isn't reversible), builds the migration pair, and proceeds.

Session-level mode **deliberately ignores** sub-dir slugs — the user is cherry-picking sessions, not moving the whole project.

## Safety

- **Old slug dirs are never deleted** in directory-level mode. Copy-then-rewrite. Old state survives.
- **Source session files are kept by default** in session-level mode. Pass `--delete-source` explicitly to remove them.
- fs mv refuses if TO already exists on disk (avoid overwrite).
- Slug-dir merging is default when dest slug dir exists — conflicting jsonls overwritten.
- Session-level + `--mv` is rejected (doesn't make sense — the folder itself isn't moving).
- Malformed jsonl lines are passed through unchanged.

Tell the user to verify `claude --resume` works at TO before `rm -rf` of old slug dirs.

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
