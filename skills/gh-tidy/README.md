# lovstudio:gh-tidy

Interactive GitHub repo triage — clean up issues, PRs, stale branches, and orphan labels in one pass.

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:gh-tidy
```

## Prerequisites

- `gh` CLI installed and authenticated
- Current directory is a GitHub repo

## Usage

```
/lovstudio:gh-tidy
```

The skill will:

1. **Scan** — List all open issues, PRs, unmerged remote branches, and labels
2. **Summarize** — Show a table with age, status, and analysis for each item
3. **Triage** — Ask you how to handle each item (close / merge / delete / keep)
4. **Execute** — Run all actions via `gh` CLI
5. **Report** — Show what was done

## Example Output

```
GitHub Tidy Report
==================
Issues:   2 closed, 1 kept
PRs:      1 merged, 0 closed
Branches: 3 deleted
Labels:   0 deleted
```
