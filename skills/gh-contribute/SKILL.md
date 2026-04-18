---
name: lovstudio:gh-contribute
description: >
  Contribute a clean, professional pull request to someone else's GitHub repository:
  fork → clone → branch → commit → push → open PR, with smart splitting into one or
  multiple PRs based on the scope of changes.
  Trigger when the user says "给这个 repo 提 PR"、"贡献代码"、"fork 然后改再 PR"、
  "contribute to this repo", "open a PR to upstream", "submit a PR to <owner>/<repo>".
license: MIT
compatibility: >
  Requires `gh` CLI (authenticated via `gh auth login`) and `git`.
  Targets GitHub repositories only. Cross-platform: macOS, Windows, Linux.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: [github, pr, contribute, fork, open-source]
---

# gh-contribute — Clean PRs to Upstream Repos

Turn local changes into a clean, professional pull request against an upstream repo
you don't own. Handles the full fork → branch → commit → push → PR pipeline, and
splits work into multiple PRs when the changes span unrelated concerns.

## When to Use

- User wants to contribute to an open-source project they don't have write access to
- User already has local edits and needs them shipped as a PR upstream
- User asks to "fork this repo and send a PR"
- User has mixed changes (e.g. docs + feature + refactor) and wants them split properly

## Non-Goals

- Does **not** write code changes — assumes the user (or a prior step) already has
  the desired modifications in the working tree or in their head
- Does **not** review the project's own PRs (see `gh-tidy`)
- Does **not** mirror to GitLab/Gitea — GitHub only

## Workflow (MANDATORY)

Execute steps in order. Do not skip confirmations.

### Step 1: Identify the target repo

Determine the upstream `owner/repo`:

1. If the user pasted a URL or `owner/repo` string → use it
2. Otherwise run `git remote -v` in the current directory and pick the `origin`
   (if origin is already the user's fork, find the upstream via
   `gh repo view --json parent`)

Record three facts:
- `UPSTREAM` — e.g. `ZenMux/zenmux-doc`
- `DEFAULT_BRANCH` — from `gh repo view $UPSTREAM --json defaultBranchRef -q .defaultBranchRef.name`
- `USER_LOGIN` — from `gh api user -q .login`

### Step 2: Read the contribution rules

Fetch `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` from upstream (if present) and
skim for: commit message format, DCO/CLA requirements, branch naming, PR template.
Carry these constraints into subsequent steps.

```bash
gh api repos/$UPSTREAM/contents/CONTRIBUTING.md -q .content 2>/dev/null | base64 -d
```

If the repo has `.github/PULL_REQUEST_TEMPLATE.md`, use it as the PR body skeleton.

### Step 3: Survey the changes

Gather the change set that needs to become PR(s):

```bash
git status --porcelain
git diff --stat $DEFAULT_BRANCH...HEAD        # committed
git diff --stat                                # unstaged
git diff --stat --cached                       # staged
```

Classify files into logical groups. Typical axes:
- **By concern**: docs / feature / bugfix / refactor / test / chore
- **By subsystem**: unrelated top-level directories usually = separate PRs
- **By dependency**: if PR B needs PR A merged first, split and note the dependency

### Step 4: Propose a PR plan and confirm

**Use `AskUserQuestion`** to present the plan. Options must include at least:

- **Single PR** — all changes together. Recommended when changes are cohesive.
- **Split into N PRs** — show the proposed titles and file groupings.
- **Abort** — something is off, let the user redirect.

Show the plan like:

```
PR #1 (docs): Update CLAUDE.md to reflect current scripts
  - CLAUDE.md
PR #2 (feat): Add gh-contribute skill bootstrap
  - scripts/new.ts
  - .prompts/contribute.xml
```

Do not proceed until the user picks an option.

### Step 5: Fork (idempotent)

```bash
gh repo view $USER_LOGIN/$REPO_NAME >/dev/null 2>&1 \
  || gh repo fork $UPSTREAM --clone=false --remote=false
```

Ensure a `fork` remote exists in the local clone:

```bash
git remote get-url fork 2>/dev/null \
  || git remote add fork git@github.com:$USER_LOGIN/$REPO_NAME.git
```

If origin already points at the user's fork, skip the `fork` remote and use `origin`.

### Step 6: Create branches and commits per PR

For each PR in the plan:

1. Start from a clean, up-to-date base:
   ```bash
   git fetch origin $DEFAULT_BRANCH
   git checkout -b $BRANCH_NAME origin/$DEFAULT_BRANCH
   ```
2. Apply only the files belonging to this PR (use `git checkout <sha> -- <paths>`
   or `git stash` + selective `git checkout` from a working branch).
3. Commit with a conventional message. If upstream uses Conventional Commits,
   match: `<type>(<scope>): <subject>`. Otherwise mirror the style of the
   last 10 commits on `$DEFAULT_BRANCH`.
4. Sign off if `CONTRIBUTING.md` requires DCO: `git commit -s ...`.

Branch naming (when upstream doesn't dictate): `<type>/<short-slug>`, e.g.
`docs/update-claude-md`, `feat/add-contribute-skill`.

### Step 7: Push to fork

```bash
git push -u fork $BRANCH_NAME
```

If origin is already the fork, use `origin` instead.

### Step 8: Open the PR

```bash
gh pr create \
  --repo $UPSTREAM \
  --base $DEFAULT_BRANCH \
  --head $USER_LOGIN:$BRANCH_NAME \
  --title "$TITLE" \
  --body "$BODY"
```

PR body template (adapt to PR template if present):

```markdown
## Summary

<1-3 bullets explaining what and why>

## Changes

- <bullet per logical change>

## Test plan

- [ ] <how to verify>

## Related

<!-- Link follow-up PRs if split, e.g. "Depends on #123" or "Part 2 of 3" -->
```

When opening multiple PRs, cross-link them in each body:

```markdown
## Related
- PR 1/3: #<url>
- PR 2/3: (this PR)
- PR 3/3: #<url>
```

### Step 9: Report back

Output a compact summary:

```
Opened 2 PRs against ZenMux/zenmux-doc:
  #201 docs: update CLAUDE.md            → https://github.com/.../pull/201
  #202 feat: add gh-contribute skill      → https://github.com/.../pull/202
```

## Splitting Heuristics

Prefer **one PR** when:
- All changes serve a single user-visible outcome
- Total diff < ~300 lines across ≤ 5 files
- The changes would be awkward to review in isolation

Prefer **multiple PRs** when:
- Docs-only changes sit alongside code changes (docs PR lands fast)
- Refactor + feature — land the refactor first, feature on top
- Unrelated subsystems touched (e.g. `scripts/` + `docs_source/`)
- One change is trivially correct and another needs discussion

When in doubt, ask the user.

## What NOT to Do

- **Never force-push** to a branch that already has a PR with review comments
  unless the user explicitly asks
- **Never edit upstream's default branch** directly — always branch first
- **Never push to upstream** — always to the user's fork
- **Never bypass hooks** (`--no-verify`) or skip signing (`--no-gpg-sign`)
  unless CONTRIBUTING.md says to or the user explicitly says so
- **Never batch unrelated concerns** into one PR just to "ship faster"
- **Never fabricate** a PR body — if you can't describe the change, ask the user

## Dependencies

```bash
# gh CLI (https://cli.github.com/)
brew install gh      # macOS
gh auth login        # one-time
```

No Python dependencies. This skill is pure `gh` + `git` orchestration.
