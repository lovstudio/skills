---
name: lov-gh-tidy
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
  author: contributors
  version: "0.2.0"
  tags: github tidy cleanup issues pr branches hygiene
---

# lov-gh-tidy

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
