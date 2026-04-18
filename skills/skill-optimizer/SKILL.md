---
name: lovstudio:skill-optimizer
category: Meta Skills
tagline: "Audit + auto-fix an existing skill, bump semver, and append a CHANGELOG entry."
description: >
  Audit and automatically optimize a lovstudio skill against repo conventions
  and official Anthropic skill-creator best practices, then bump the semver
  version and append a CHANGELOG entry. Checks SKILL.md frontmatter/trigger
  quality, script CLI hygiene, directory naming, README badge, and progressive
  disclosure structure. Prioritizes issues raised in the current conversation
  (e.g. bugs the user just hit) over a generic sweep. Use when the user asks
  to "optimize", "refine", "audit", or "polish" an existing skill, or when they
  say "bump version", "update changelog", or "fix this skill". Also trigger
  when the user mentions "优化 skill", "skill 审计", "刷一遍 skill",
  "skill-optimizer", "bump skill version", "update skill changelog".
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only, no external dependencies).
  Must be run inside the lovstudio-skills repo (auto-detects repo root).
metadata:
  author: lovstudio
  version: "0.3.0"
  tags: meta skill-maintenance versioning changelog lint
---

# skill-optimizer — 自动优化 lovstudio skill 并维护版本与 changelog

Runs a lint → fix → bump → changelog pipeline on an existing skill in this
repo. Fully automatic — no interactive prompts. Every run produces a concrete
version bump and a new CHANGELOG.md entry so optimization history is traceable.

## When to Use

- User mentioned a concrete problem with an existing skill in this conversation
  (wrong trigger phrases, stale CLI flags, missing README badge, etc.) and
  wants it fixed.
- User asks to "audit", "polish", "refine", "刷一遍" an existing skill.
- User explicitly asks to bump a skill's version or update its changelog.
- Proactively after another skill has been modified meaningfully — run this to
  record the change with a version bump.

## Workflow (MANDATORY, fully automatic)

**Do not ask the user for options. Infer everything from (a) the target skill
name and (b) any optimization notes mentioned in the current conversation.**

### Step 1: Identify target & context

From the user's message, extract:

1. **Target skill name** — e.g. `any2pdf`, `lovstudio-any2pdf`, or `lovstudio:any2pdf`.
   Normalize to the bare name (strip prefix). If the user did not name a skill
   explicitly, infer it from recent conversation context (the skill they were
   just working on). If still ambiguous, ask one targeted question.
2. **Context-driven fix list** — scan the current conversation for issues the
   user raised about this skill: wrong flags, trigger misfires, broken CJK
   rendering, missing options, confusing README, etc. This list is the
   **primary driver**. The generic lint only supplements it.

### Step 2: Lint

```bash
python3 skills/lovstudio-skill-optimizer/scripts/lint_skill.py <name> --json
```

Parse the JSON findings. Combine with the context-driven fix list from Step 1.
Prioritize in this order:

1. Fixes the user explicitly mentioned in conversation (highest priority)
2. Lint `error` findings
3. Lint `warn` findings
4. Lint `info` findings — apply only if cheap and safe

### Step 3: Apply fixes directly

Edit `SKILL.md`, `README.md`, `scripts/*.py` with the `Edit` tool based on the
prioritized fix list. Guidelines:

- **SKILL.md frontmatter description**: make sure it covers what + when +
  concrete trigger phrases (中文 + English). Don't bloat it; keep under ~800 chars.
- **CLI args in scripts**: if the user hit a bug with a specific flag, fix the
  root cause — don't paper over it.
- **Progressive disclosure**: if SKILL.md body > 500 lines, split the largest
  section to `references/<topic>.md`.
- **Don't write tests or docs that weren't asked for.** The CHANGELOG entry IS
  the documentation of the change.
- **Don't add emojis** unless the original file already uses them consistently.

### Step 4: Decide bump type

Choose semver bump based on the fixes applied:

| Bump    | Use when                                                           |
|---------|--------------------------------------------------------------------|
| `patch` | bug fix, wording fix, frontmatter tweak, CJK rendering fix         |
| `minor` | new CLI flag, new option, new reference doc, expanded scope        |
| `major` | breaking CLI change, removed option, renamed skill                 |

Stay in 0.x unless explicitly told otherwise — per repo release conventions.

### Step 5: Bump version + write changelog

```bash
python3 skills/lovstudio-skill-optimizer/scripts/bump_version.py <name> \
  --type <patch|minor|major> \
  --message "<one-line summary of the biggest change>" \
  --change "<additional bullet>" \
  --change "<additional bullet>"
```

This updates:
- `README.md` version badge (source of truth)
- `SKILL.md` frontmatter `metadata.version` (kept in sync if present)
- `CHANGELOG.md` — prepends a new entry with today's date (creates the file if missing)

### Step 6: Re-lint & report

```bash
python3 skills/lovstudio-skill-optimizer/scripts/lint_skill.py <name>
```

Report to the user, in this exact shape and nothing more:

```
optimized: lovstudio-<name>
version:   <old> → <new>
fixes:
  - <bullet 1>
  - <bullet 2>
remaining lint warnings: <count>  (or "none")
```

**Do not** print a trailing summary, self-congratulation, or next-step suggestions.
The diff speaks for itself.

### Step 7: Commit, push & sync all locations

Skills live in three locations that must stay in sync:

```
source (edit here):  ~/projects/lovstudio-skills/        → lovstudio/skills
claude reads from:   ~/.claude/skills/*                   → symlinks to source
distribution repo:   ~/projects/lovstudio-pro-skills/     → lovstudio/pro-skills
```

**7a. Commit & push to source repo:**

```bash
cd ~/projects/lovstudio-skills
git add skills/lovstudio-<name>/
git commit -m "fix(<name>): <one-line summary>"
git push
```

- Commit message follows repo convention: `fix|feat|docs(<skill-name>): <summary>`
- Use `fix` for patch, `feat` for minor, `feat!` for major

**7b. Sync to pro-skills distribution repo:**

The two repos have independent git histories (not forkable), so sync via
file copy:

```bash
SRC=~/projects/lovstudio-skills/skills/lovstudio-<name>
DST=~/projects/lovstudio-pro-skills/skills/lovstudio-<name>
rsync -av --delete "$SRC/" "$DST/"
cd ~/projects/lovstudio-pro-skills
git add skills/lovstudio-<name>/
git commit -m "sync(<name>): <version> from lovstudio/skills"
git push origin main
```

`~/.claude/skills/` is already up-to-date via symlinks — no action needed.

**If any step fails**, report the sync state to the user rather than silently
skipping. A partial sync (source updated but pro-skills stale) is the exact
problem this step exists to prevent.

## CLI Reference

### `lint_skill.py`

| Argument | Default | Description |
|----------|---------|-------------|
| `<name>` | — | Skill name (with or without `lovstudio-` prefix) |
| `--path` | — | Absolute path to skill dir (overrides name) |
| `--json` | off | Emit findings as JSON |

Exit code: `2` if any `error`-severity finding, `0` otherwise.

### `bump_version.py`

| Argument | Default | Description |
|----------|---------|-------------|
| `<name>` | — | Skill name |
| `--path` | — | Absolute path to skill dir (overrides name) |
| `--type` | — | `patch` \| `minor` \| `major` (mutually exclusive with `--set`) |
| `--set` | — | Explicit version e.g. `0.2.0` |
| `--message`, `-m` | required | Primary changelog bullet |
| `--change`, `-c` | — | Additional bullet (repeatable) |
| `--dry-run` | off | Show what would change without writing |

## Dependencies

Python 3.8+ (stdlib only, no `pip install` needed).
