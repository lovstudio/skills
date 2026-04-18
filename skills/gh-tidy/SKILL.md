---
name: lovstudio:gh-tidy
category: Developer Tools
tagline: "Triage & clean up GitHub issues, PRs, branches, and labels in one pass."
description: >
  Interactive GitHub repo hygiene skill. Lists all open issues, PRs, stale
  branches, and orphan labels, shows a summary of each with analysis, then
  asks the user how to handle each item (close, merge, comment, delete, keep).
  Executes all chosen actions via gh CLI. Use when the user says "清理 GitHub",
  "tidy repo", "clean up issues", "处理 PR", "repo hygiene", or similar.
license: MIT
compatibility: >
  Requires gh CLI authenticated. Works on any GitHub repo.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: github tidy cleanup issues pr branches hygiene
---

# lovstudio:gh-tidy

Interactive GitHub repo triage — issues, PRs, branches, labels in one pass.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- Current directory is a git repo with a GitHub remote

## Workflow

### Step 1: Scan

Run all of these in parallel to gather repo state:

```bash
# Open issues
gh issue list --state open --limit 100 --json number,title,author,createdAt,labels,comments

# Open PRs
gh pr list --state open --limit 100 --json number,title,author,createdAt,labels,reviewDecision,mergeable,headRefName

# Remote branches (exclude main/master/develop)
git branch -r --no-merged origin/main | grep -v 'HEAD\|main$\|master$\|develop$'

# Labels
gh label list --limit 100 --json name,description,color
```

### Step 2: Summarize

Present a concise table for each category that has items:

**Issues:**
| # | Title | Author | Age | Comments | Labels |
|---|-------|--------|-----|----------|--------|

**PRs:**
| # | Title | Author | Age | Mergeable | Review |
|---|-------|--------|-----|-----------|--------|

**Stale branches** (no commits in 30+ days):
List branch names with last commit date.

**Orphan labels** (not used by any issue/PR):
List label names.

For each item, provide a brief analysis:
- Issues: Is it actionable? Feature request vs bug? Has it been addressed?
- PRs: Are there conflicts? Is the code valuable? What does the diff look like?
- Branches: Is the work merged? Abandoned?

### Step 3: Triage

Use `AskUserQuestion` to ask the user how to handle each item. Group by category.

For issues, offer: Close with thank-you / Close as wontfix / Keep open / Add label
For PRs, offer: Review & merge / Close without merge / Keep open
For branches, offer: Delete / Keep
For labels, offer: Delete / Keep

**Important:** Always show your analysis and reasoning for each item before asking. Don't just present options without context.

### Step 4: Execute

Execute all chosen actions via `gh` CLI:

```bash
# Close issue with comment
gh issue close <N> --comment "message"

# Merge PR (prefer squash)
gh pr merge <N> --squash

# Close PR without merge
gh pr close <N> --comment "message"

# Delete remote branch
git push origin --delete <branch>

# Delete label
gh label delete <name> --yes
```

### Step 5: Report

Show a summary of what was done:

```
GitHub Tidy Report
==================
Issues:  2 closed, 1 kept
PRs:     1 merged, 0 closed
Branches: 3 deleted
Labels:  0 deleted
```

## Rules

- Always show analysis before asking for decisions — explain WHY you suggest an action
- For PR merges with conflicts, resolve conflicts locally first, then push and merge
- When closing issues/PRs from external contributors, always leave a polite thank-you comment
- Never force-push or delete protected branches
- Skip categories with zero items — don't show empty tables
- For large repos (50+ items), batch the triage questions by category
