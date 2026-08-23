---
name: lov-skill-optimizer
category: Meta Skills
tagline: "Audit an Agent Skill, apply focused fixes, bump semver, and verify every distribution layer."
description: >
  Audit and optimize one or more existing Agent Skills from a canonical source
  path, then bump semver, update README/SKILL.md/skill.yaml/CHANGELOG.md, and
  verify installed copies and catalog synchronization. Checks frontmatter,
  trigger quality, CLI hygiene, naming, portability, version drift, dirty
  worktrees, shared Skill feedback policy, and compatibility contracts. Use when the user asks to optimize,
  refine, audit, polish, or update a Skill, or mentions "优化 skill", "skill
  审计", "刷一遍 skill", "skill-optimizer", or "update skill changelog".
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only). Git is optional for linting and required
  for source commit/push verification. Catalog synchronization is discovered
  from explicit paths, environment variables, or nearby checkouts; unavailable
  locations are reported rather than assumed.
metadata:
  author: lovstudio
  version: "0.10.0"
  tags: meta skill-maintenance versioning changelog lint portability sync
---

# skill-optimizer — 自动优化 Agent Skill 并维护版本与分发状态

This is a non-interactive maintenance workflow. It infers the target and
prioritizes issues from the current conversation, then supplements them with a
generic lint pass. When several Skills are named in one request, process them
in the order named and emit a separate result block for each Skill.

## Target and source resolution

Prefer an explicit canonical path whenever the Skill is outside a conventional
skills repository:

```bash
python3 scripts/lint_skill.py --path /absolute/path/to/skill --json
python3 scripts/inspect_layout.py --path /absolute/path/to/skill --json
```

For a name, accept `foo`, `lov-foo`, or `foo-skill`. Resolution may find a
source checkout, an installed copy, or a catalog entry. Before editing:

1. Resolve symlinks and record the actual path.
2. Identify the Git root, branch, and dirty worktree state.
3. Treat a source checkout as canonical. If the target is an installed copy,
   locate a matching source checkout; when no source exists, report that the
   supplied path itself is canonical instead of silently editing another copy.
4. Record every discovered installation and catalog path. A copy is `synced`
   only when its content digest matches the source; a missing location is
   `not_discovered`, never `complete`. A symlink is `synced` only when it
   resolves to the canonical source.

Do not absorb pre-existing edits into a maintenance commit. If a target file is
already dirty, review the overlap before editing it and stage only the exact
files changed by this optimization.

## Workflow (mandatory)

### Step 0: Classify feedback scope

When the optimization is triggered by a user correction, classify it before choosing targets:

- `task-specific`: applies only to the current artifact or one-off value. Do not edit a Skill.
- `skill-specific reusable`: applies to future runs of one domain or platform. Optimize the relevant
  canonical Skill.
- `global reusable`: changes how every Skill should handle feedback, authorization, sequencing, or
  handoff. Update the host's active user-level shared instruction artifact once (for example the
  applicable user-level `AGENTS.md`); do **not** paste the same policy into every domain `SKILL.md`.

If a global policy was previously placed in one domain Skill, move it to the shared layer and remove the
domain duplicate while preserving any genuinely domain-specific rule learned in the same incident. A
shared policy file may be outside the Skill repository; report its path and verification state explicitly
instead of pretending it is part of the Skill package.

Any `reusable` correction invalidates prior terminal approval for the active task. Finish the policy/Skill
optimization and validation first, then apply the correction to the current artifact, report the new state,
and stop for the user's next instruction. Do not continue into publishing, submission, or another external
write using a pre-correction “confirm”, “continue”, or “go ahead”.

### Step 1: Extract targets and context

Normalize every explicitly named Skill and preserve the user's order. Strip the
`lov-` prefix only for lookup; keep the public Skill identifier in reports.
Collect the current-conversation fix list first: broken flags, trigger misses,
wrong paths, confusing output, missing modules, compatibility requirements, or
other concrete symptoms.

### Step 2: Baseline lint

For each target, run the linter against the resolved canonical path:

```bash
python3 scripts/lint_skill.py --path /absolute/path/to/skill --json
```

Prioritize findings in this order:

1. Fixes explicitly mentioned in the conversation;
2. `error` findings;
3. `warn` findings;
4. cheap, low-risk `info` findings.

The baseline must include version-source drift between README.md, SKILL.md
frontmatter, and skill.yaml. Portability findings are high priority for a
reusable Skill: move personal paths to flags, environment variables, or
`references/user-config.md`, or mark a genuinely author-only dependency in
`compatibility`.

### Step 3: Apply focused fixes

Edit only the canonical source. Keep the Skill's public trigger surface,
compatibility aliases, storage contracts, and user-facing semantics explicit.
Use progressive disclosure when SKILL.md grows beyond roughly 500 lines. Add a
script or reference file only when it resolves a concrete audit finding or
conversation issue.

The linter checks:

- Agent Skills-compatible frontmatter and trigger phrases;
- README version badge and installation command;
- `metadata.version`, README badge, and `skill.yaml` version consistency;
- CLI use of argparse and obvious script hygiene;
- TODO placeholders and oversized instruction bodies;
- personal paths, fixed runtime paths, and missing user configuration;
- source/install/catalog layout evidence.

### Step 4: Bump semver and changelog

Use the path-aware version tool so all version surfaces move together:

```bash
python3 scripts/bump_version.py \
  --path /absolute/path/to/skill \
  --type minor \
  --message "add guarded project rename workflow" \
  --change "report source, installation, and catalog synchronization state"
```

Choose `patch` for bug, wording, frontmatter, or lint fixes; `minor` for a new
flag, reference, module, or expanded workflow; `major` for a breaking CLI or
removed behavior. Stay in `0.x` unless the user explicitly requests otherwise.
The tool updates README.md, SKILL.md, skill.yaml, and CHANGELOG.md and refuses
to duplicate an existing changelog version.

### Step 5: Re-lint and inspect layout

```bash
python3 scripts/lint_skill.py --path /absolute/path/to/skill --json
python3 scripts/inspect_layout.py --path /absolute/path/to/skill --json
```

Do not report `remaining lint warnings: none` unless the final JSON was read.
Do not report synchronization as complete unless every discovered distribution
copy and required catalog check has been verified after the source change. Keep
`distribution_state`, `catalog_state`, and the aggregate `sync_state` separate:
an installed copy can be `complete` while an undiscovered catalog keeps the
aggregate state `partial`. A discovered catalog is `complete` only when its
matching Skill payload digest is `synced`.

### Step 6: Synchronize discovered distributions

`inspect_layout.py` checks conventional and configured installation roots:
`AGENT_SKILLS_DIR`, `CLAUDE_SKILLS_DIR`, `CODEX_SKILLS_DIR`, `SKILLS_DIR`,
plus the host's agent-managed fallback roots. It also checks explicit
`--install-root` and `--catalog-root` values plus nearby `general-skills` and
`dev-skills` checkouts. Use an environment variable or explicit flag when the
installation root is outside the conventional layout.

For a non-symlink installation copy, first run a read-only sync plan:

```bash
python3 scripts/sync_installation.py \
  --source /absolute/path/to/canonical-skill \
  --target /absolute/path/to/installed-skill \
  --json
```

After reviewing `missing`, `changed`, and `extra`, apply the exact copy with:

```bash
python3 scripts/sync_installation.py \
  --source /absolute/path/to/canonical-skill \
  --target /absolute/path/to/installed-skill \
  --apply --json
```

Use `--prune` only when removing extra files from the installation copy is
explicitly part of the task. Symlink installations are verified, not copied.
For a catalog, use its own scripts only when they are actually present:

```bash
python3 scripts/sync-skills.py
python3 scripts/render-marketplace.py
python3 scripts/render-readme.py
python3 scripts/validate_deps.py
```

Run only the commands that exist in that catalog checkout. If no catalog is
discovered, report `not_discovered`; if source and installation are updated but
the catalog is stale or unavailable, report `partial`. Never invent a catalog
path or claim a live-site update from a local source commit.

### Step 7: Commit and push exact source changes

Inspect `git diff --check`, then stage the listed changed files explicitly:

```bash
git add -- SKILL.md README.md CHANGELOG.md skill.yaml scripts references
git diff --cached --name-only
git commit -m "fix(<skill-name>): <one-line summary>"
git push origin HEAD
```

Use `feat` for a minor feature and `feat!` for a breaking change. If the source
checkout has no remote, commit on its current branch and report `push:
not_configured`; do not imply that a remote release happened. If a catalog is a
separate repository, commit and push it independently after its own validation.

## Final report contract

Return one block per optimized target, with no trailing summary:

```
optimized: lov-<name>
version:   <old> → <new>
source:    <canonical path> (<clean|dirty>)
distribution:
  - <path>: <synced|drifted|not_discovered>
catalog:
  - <path>: <synced|partial|not_discovered>
fixes:
  - <bullet 1>
  - <bullet 2>
remaining lint warnings: <count>  (or "none")
sync state: <complete|partial|not_discovered>
```

The keys stay stable for machine parsing; the values and fix bullets follow the
user's language. A failed or skipped push, installation sync, or catalog sync
must appear in the relevant state rather than being omitted.

## Runtime context

Read this Skill's `skill.yaml` when the host supplies `skill-runtime/v1`.
Use only fields declared there. Profile data is for public identity facts and
preferences are for output language/timezone; neither replaces the canonical
source, installation, or catalog evidence collected by this workflow.

## CLI reference

```bash
python3 scripts/lint_skill.py --path PATH [--json]
python3 scripts/lint_skill.py --all --root PATH [--json]
python3 scripts/bump_version.py --path PATH --type patch|minor|major -m MESSAGE
python3 scripts/inspect_layout.py --path PATH [--install-root PATH] [--catalog-root PATH] [--json]
python3 scripts/sync_installation.py --source PATH --target PATH [--apply] [--prune] [--json]
```

All bundled tools use Python's standard library only.

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
