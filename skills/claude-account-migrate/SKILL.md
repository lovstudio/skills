---
name: lov-claude-account-migrate
description: >
  Claude 桌面版换号后，把旧账号的 Code 与 Cowork 会话复制到当前账号继续使用，并防止记录被 30 天清理；
  Use when switching Claude accounts, “换号后找回 session”, or to migrate Claude sessions.
license: MIT
compatibility: "Python 3.9+ standard library. Verified with the Claude desktop app on macOS; other platforms need --data-dir."
metadata:
  author: skill-publisher
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  display_name_zh: "Claude 换号搬家"
  display_name_en: "Claude Account Mover"
  tags:
    - claude
    - session
    - account
    - migration
---

# Claude 换号搬家 · Claude Account Mover

换了 Claude 账号后，把旧账号在本机留下的 Code 会话和 Cowork 会话复制到当前
账号的侧边栏里，点开即可继续；同时识别已经丢失对话记录的空壳会话，并把记录
保留期调到足够长，避免再被自动清理。

## Triggers

### Activate when

- “换了 Claude 账号，之前的 session 都不见了”“把旧账号的会话搬到新账号”。
- “切换账号但不要丢历史会话”“旧账号不用了，数据和 session 要继续用”。
- "I switched Claude accounts and lost my sessions", "help me move the sessions from my old Claude account to the new one".
- 用户问 Cowork 会话或 Code 会话的记录为什么会过期、如何延长保留期。

### Do not activate when

- 只想临时切回旧账号查看：直接退出再用旧账号登录即可，会话按账号保存，不会丢。
- 搬迁或重命名项目目录、让 `claude --resume` 跟着新路径走：交给 `lov-cc-mv`。
- 切换 API 供应商、代理或第三方模型：属于 CC Switch 一类供应商切换工具，与账号会话无关。
- 迁移 claude.ai 网页聊天、Projects、connector 授权或云端会话：这些存在服务器上，本 Skill 无法搬运。

## Background the agent must know

- 桌面版按「账号 UUID / 组织 UUID」分目录保存侧边栏索引：Code 会话在
  `claude-code-sessions/`，Cowork 会话在 `local-agent-mode-sessions/`。换号只是换了
  读取的目录，旧会话仍在磁盘上。细节见 [`references/desktop-storage.md`](references/desktop-storage.md)。
- Code 会话的完整对话记录在 Claude Code 配置目录的 `projects/` 下，所有账号共用；
  Cowork 会话的对话记录在各自会话目录里的 `.claude/`，跟着会话目录走。
- Claude Code 默认只保留 30 天对话记录（`cleanupPeriodDays`）。被清掉的会话在侧边栏
  只剩标题，无法恢复；Cowork 会话使用独立配置，不继承用户全局设置。

## User Profile (cross-session)

Read `skill.yaml` and the shared `user-profile/v1` Profile at the start of every
run, including `skills.lov-claude-account-migrate.records`. Supported records:

- `records.retention_days` — preferred `cleanupPeriodDays` for migrated Cowork sessions.
- `records.include_orphans` — whether title-only sessions should also be copied.

When the user directly states one of these as a lasting preference, save it with
`scripts/profile_store.py record ... --confirm` and report the saved path. Never
store emails, account UUIDs, tokens, or credentials in the Profile. See
`references/user-profile.md`.

## Skill Group Composition

Read `references/skill-composition.md` before routing to an adjacent capability.
`lov-cc-mv` and session analysis Skills are optional, separate handoffs.

## Workflow (MANDATORY)

### Step 0: Resolve the script and context

```bash
export SKILL_DIR="${SKILL_DIR:-<installed lov-claude-account-migrate directory>}"
# A function, not a string variable: zsh does not word-split an unquoted $CAM.
CAM() { python3 "$SKILL_DIR/scripts/claude_account_migrate.py" "$@"; }
```

The script defaults to the macOS desktop data directory and to `$CLAUDE_CONFIG_DIR`
or the home `.claude` directory for transcripts. On other platforms pass
`--data-dir`; if the store is missing, stop and report the expected path.

### Step 1: Scan accounts (read-only)

```bash
CAM scan
```

Report per account: whether it is current, the activity date range, Code session
count with how many still have transcripts, Cowork session count, and archived
count. Emails are shown only when unambiguous; otherwise identify the old account
by date range, counts, and a few session titles. Ask one focused question only if
the source account remains ambiguous.

### Step 2: Plan the migration (read-only)

```bash
CAM migrate --from <old account uuid | prefix | email>
```

`--to` defaults to the desktop app's current account. Explain the plan in plain
terms: how many sessions will be copied, how many are already present, and how
many are title-only orphans. Orphans are skipped by default because they cannot
be opened or resumed; copy them only when the user wants the titles, using
`--include-orphans`.

### Step 3: Apply

```bash
CAM migrate --from <old account> --apply
```

The copy is additive: existing target files are never overwritten, the source
account folder is never modified, and credentials or app configuration are never
touched. No backup is needed for this step. Repeat Step 2 and Step 3 for each old
account the user wants to keep.

### Step 4: Verify in the app

- The desktop app rescans its session folders within minutes; a restart is not
  normally required. If the host offers session-management tools, list or fetch
  a migrated session to confirm it is visible; otherwise ask the user to check the
  sidebar. Only if sessions are still missing, ask the user to quit with Cmd+Q
  and reopen.
- Re-run the Step 2 plan: it must report `to copy 0` for every org.
- The app rebuilds `archived-sessions.idx` from each session's `isArchived`
  flag, so archived state survives.

### Step 5: Protect transcripts

- If the plan warns that the CLI `cleanupPeriodDays` is unset or 30 days or less,
  tell the user that older transcripts will be deleted and recommend raising it in
  the user's Claude Code `settings.json`; change it only with the user's consent.
- `migrate` already sets `cleanupPeriodDays` (default 3650) inside every copied
  Cowork session. For Cowork sessions that already belong to an account:

```bash
CAM retention --account current          # plan
CAM retention --account current --apply  # write
```

### Step 6: Report

State, per source account: sessions copied, already present, orphans skipped or
copied, Cowork retention updates, and whether the app shows them. Also state:

- The source account folder must stay if the plan reported Cowork sessions that
  still write outputs there.
- Scheduled tasks, claude.ai chats, Projects, connector authorizations, and
  cloud sessions are not migrated.
- Title-only sessions cannot be recovered without an external backup.

## Dependencies

None beyond Python 3.9+ standard library. `scripts/profile_store.py` is the
standard Profile helper.

## Validation

```bash
python3 scripts/validate_skill.py .
```
