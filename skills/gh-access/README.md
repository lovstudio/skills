# lovstudio:gh-access

Grant, revoke, and audit collaborator access on **private** GitHub repos — by
GitHub username **or** email address — with read-only as the safe default.

Use when you want to share a private repo with a client or contractor
without making the repo public.

## Install

```bash
npx skills add lovstudio/gh-access-skill
```

Or clone directly:

```bash
git clone https://github.com/lovstudio/gh-access-skill \
          ~/.claude/skills/lovstudio-gh-access
```

## Prerequisites

- [`gh`](https://cli.github.com) CLI authenticated (`gh auth status`)
- Token scopes: `repo` (always), `admin:org` (for org-owned repos)
- You must be a repo admin (personal repo) or org owner / repo admin (org repo)

## What it does

```
                 ┌──────────────────────────────────────────────┐
  Client input:  │  alice                                       │
  "give these    │  bob@example.com                             │
  folks access"  │  carol@startup.io                            │
                 │  typo-user                                   │
                 └──────────────────┬───────────────────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │  Resolve each identifier      │
                    │  • username → verify exists   │
                    │  • email → search by email    │
                    │           → org invite fallback│
                    └───────────────┬───────────────┘
                                    ▼
                ┌───────────────────────────────────────────┐
                │  Show resolution table, confirm           │
                └───────────────────┬───────────────────────┘
                                    ▼
                ┌───────────────────────────────────────────┐
                │  PUT /repos/{owner}/{repo}/collaborators  │
                │  (permission=pull by default)             │
                └───────────────────┬───────────────────────┘
                                    ▼
                          Invitation emails sent
```

## Subcommands

| Mode | What it does |
|---|---|
| **grant** | Invite one or more people as collaborators with a chosen permission. |
| **revoke** | Remove collaborators (idempotent — safe to re-run). |
| **list** | Show active collaborators + pending invitations for the repo. |

## Permission levels

| Level | Effect | When to use |
|---|---|---|
| `pull` *(default)* | Read code, clone, open/comment on issues and PRs | Clients, reviewers, most external access |
| `triage` | `pull` + manage issues/PRs (label, close) | Trusted external collaborators |
| `push` | Write to non-protected branches | Contractors actively contributing code |
| `maintain` | `push` + manage repo settings (except destructive) | Senior contractors |
| `admin` | Full control | Rare — requires explicit confirmation |

**The skill defaults to `pull` and requires an explicit request to escalate.**

## Usage examples

### Invite one client by email (org repo)

```
User: 把 acme/internal-dashboard 开给 client@acme.com，只读
→ Skill resolves client@acme.com:
    - If they have a GitHub account with that email → invite by username
    - If not → send org invite by email (pending until they create / link account)
→ Permission: pull
```

### Batch invite mixed list

```
User: 给这几个人开 lovstudio/handoff-bundle 的权限:
      alice
      bob@startup.io
      carol-github

→ Skill resolves all three, shows a table, asks to confirm,
  then issues 3 PUT calls with permission=pull.
```

### List who has access

```
User: 谁现在能访问 lovstudio/handoff-bundle?
→ Skill shows:
    Active:    alice (pull), carol-github (push)
    Pending:   bob@startup.io (pull, invited 2d ago)
```

### Revoke

```
User: 把 alice 从 lovstudio/handoff-bundle 踢出去
→ Skill confirms, then DELETEs the collaborator.
```

## Resolution statuses

When processing a mixed list, each identifier ends up in one of these buckets:

| Status | Meaning | Action |
|---|---|---|
| `user_ok` | Username verified on GitHub | Invite directly |
| `email_to_user` | Email resolved to a public GitHub account | Invite that username |
| `email_invited` | Email had no public account, org invite sent | Recipient accepts via email |
| `email_no_account` | Email, no GitHub account, **personal repo** | Skip — ask user for username |
| `user_not_found` | Username doesn't exist (typo?) | Skip, report |

## Safety defaults

- Read-only (`pull`) unless explicitly overridden
- Always show a resolution table before writing
- Ask to confirm before batch revokes
- Escalation to `admin` / `maintain` requires explicit secondary confirmation
- Writes are sequential so partial failures are legible in the report

## License

MIT
