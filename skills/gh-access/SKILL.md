---
name: lov-gh-access
category: Developer Tools
tagline: "Grant / revoke / list collaborator access on private GitHub repos by username or email."
description: >
  Open a private GitHub repo to external clients or contractors without making
  it public. Accepts a mixed list of GitHub usernames and/or email addresses,
  resolves each to a GitHub account (falling back to an email invitation when
  the user has no discoverable account yet), and invites them as collaborators
  with a chosen permission level (default: read-only, sufficient for pulling
  code and filing issues / PRs). Also supports revoking access and listing
  current collaborators. Use when the user says "给客户开权限", "share private
  repo", "invite collaborator", "邀请外部协作者", "grant repo access", "客户要看代码",
  "revoke access", "撤销访问", "list collaborators", or similar.
license: MIT
compatibility: >
  Requires gh CLI authenticated with a token that has `repo` + `admin:org` scope
  (for org-owned repos, the caller must be a repo admin or org owner).
metadata:
  author: contributors
  version: "0.2.0"
  tags: github collaborator access invite private-repo permissions
---

# lov-gh-access

Grant, revoke, and audit collaborator access on private GitHub repos — by
username **or** email, with read-only as the safe default.

## Prerequisites

- `gh` CLI authenticated (`gh auth status`) with a token that has:
  - `repo` scope (always)
  - `admin:org` scope (if the target repo is org-owned; caller must be org owner or repo admin)
- The target repo exists and is accessible to the caller.

## Subcommands

This skill has three modes. Pick based on the user's intent:

| User intent | Subcommand |
|---|---|
| "开权限 / share / invite / grant" | **grant** |
| "撤销 / remove / revoke / 踢出" | **revoke** |
| "谁有权限 / who has access / list" | **list** |

If intent is unclear, use `AskUserQuestion` to disambiguate.

## Workflow

### Step 0: Collect inputs via AskUserQuestion

**ALWAYS** collect the following BEFORE touching the API:

1. **Target repo** — `<owner>/<repo>` (e.g. `skill-publisher/private-demo`). If the
   user is inside a git repo, pre-fill from `gh repo view --json nameWithOwner -q .nameWithOwner`.
2. **Subcommand** — grant / revoke / list.
3. **(grant/revoke only) Identifiers** — a whitespace- or comma-separated list
   of GitHub usernames and/or email addresses. Mixed is fine.
4. **(grant only) Permission level** — default `pull` (read-only). Offer:
   - `pull` — read + issues + PRs (recommended default)
   - `triage` — read + can label/close issues & PRs, no code write
   - `push` — write access (⚠ confirm explicitly)
   - `maintain` / `admin` — block unless user explicitly insists

Never silently escalate. If the user just says "给他权限" without specifying
level, default to `pull` and state that clearly.

### Step 1: Resolve identifiers → GitHub usernames

For each identifier in the list, follow this resolution chain and record the
outcome per identifier (for the final summary report):

```
identifier → classify → resolve
```

**Classification rule:** an identifier containing `@` is treated as an email,
otherwise as a GitHub username.

#### Case A — looks like a username

1. Verify the account exists:
   ```bash
   gh api "users/<login>" --jq '.login' 2>/dev/null
   ```
2. If it returns the login → resolved as `login`, status `user_ok`.
3. If the call 404s → status `user_not_found`. Do NOT fall back to email invite
   (we don't have an email). Report and skip.

#### Case B — looks like an email

1. Search by email:
   ```bash
   gh api "search/users?q=<email>+in:email" --jq '.total_count, .items[0].login'
   ```
2. If `total_count >= 1` and a login is returned → resolved as `login`,
   status `email_to_user`.
3. If `total_count == 0` → fall back to **email invite** path:
   - For org repos: `gh api -X POST "orgs/<org>/invitations" -f email=<email> -f role=direct_member` then add the pending member as an outside collaborator on the repo once they accept. **Note**: inviting directly-to-repo by email is not supported by the REST API for non-org personal repos — if the target is a personal repo, report `email_no_account` and ask the user to obtain the recipient's GitHub username.
   - Status: `email_invited` (org) or `email_no_account` (personal repo).

Show the resolution table to the user **before** performing writes:

| Input | Type | Resolved | Status |
|---|---|---|---|
| `alice` | username | `alice` | user_ok |
| `bob@example.com` | email | `bobhub` | email_to_user |
| `carol@startup.io` | email | — | email_invited (or email_no_account) |
| `typo-user` | username | — | user_not_found |

Ask the user to confirm before proceeding with writes. Skip `user_not_found`
and `email_no_account` entries by default.

### Step 2: Execute

#### grant

For each resolved username, issue a repo invitation:

```bash
gh api -X PUT "repos/<owner>/<repo>/collaborators/<login>" \
       -f permission=<pull|triage|push|maintain|admin>
```

- Response `201` = invitation sent (pending until recipient accepts).
- Response `204` = already a collaborator; permission was updated.
- Response `422` = user not found or already pending; inspect and report.

For org-repo email invites that resolved to `email_invited` above, no
additional call is needed — the org invitation covers repo access once the
user accepts. Tell the user to remind the recipient to check their email.

#### revoke

```bash
gh api -X DELETE "repos/<owner>/<repo>/collaborators/<login>"
```

- Response `204` = removed (or was never a collaborator — idempotent).
- For email-only identifiers with no resolved login: use
  `gh api -X DELETE "orgs/<org>/memberships/<login>"` only if the user
  explicitly wants to remove from the whole org; otherwise skip and report.

Before executing revokes, **show the list of logins that will be removed and
ask for a final confirmation** (revokes are visible to the recipient and can
be socially awkward to reverse).

#### list

```bash
gh api "repos/<owner>/<repo>/collaborators?affiliation=all" \
       --jq '.[] | {login, permissions}' \
       --paginate
```

Also list pending invitations:

```bash
gh api "repos/<owner>/<repo>/invitations" --paginate \
       --jq '.[] | {invitee: .invitee.login, email, permissions, created_at}'
```

Present as two tables: **Active collaborators** and **Pending invitations**.

### Step 3: Report

Show a final summary table for grant/revoke operations:

```
gh-access report — <owner>/<repo>
=================================
Granted (pull): alice, bobhub
Invited via email: carol@startup.io (pending org invite)
Skipped: typo-user (user_not_found)
```

Include the invitation URL the user can share manually if helpful:
`https://github.com/<owner>/<repo>/invitations`

## Rules

- **Default to `pull` (read-only)** unless the user explicitly names a higher
  permission. State the chosen level clearly before executing.
- **Never escalate to `admin`/`maintain`** without an explicit, unambiguous
  request — ask a confirming `AskUserQuestion` even if the user seemed to ask.
- **Show the resolution table before writes.** Clients mistyping a username is
  common; showing the resolved login prevents inviting the wrong person.
- **Idempotent revokes.** A `204` on a non-collaborator is fine — don't panic.
- **Batch-friendly.** A single invocation can process a long mixed list;
  execute resolution in parallel where possible, but keep writes sequential so
  partial failures are easy to report.
- **Email invites only work cleanly for org repos.** For personal repos
  without a resolved username, stop and ask the user to obtain a GitHub
  username from the recipient.
- **Private repos only are the typical case**, but this skill works on public
  repos too — no need to refuse.

## Common gh CLI quick reference

```bash
# Who am I? What scopes do I have?
gh auth status

# Is this a repo I can admin?
gh api "repos/<owner>/<repo>" --jq '.permissions'

# Cancel a pending invitation
gh api -X DELETE "repos/<owner>/<repo>/invitations/<invitation_id>"

# Show org membership of a user
gh api "orgs/<org>/memberships/<login>" --jq '.role, .state'
```

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
