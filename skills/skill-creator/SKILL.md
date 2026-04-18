---
name: lovstudio:skill-creator
category: Meta Skills
tagline: "Scaffold new lovstudio skills as independent repos under lovstudio/{name}-skill."
description: >
  Create new skills for the lovstudio ecosystem. Each skill is its own
  independent GitHub repo at lovstudio/{name}-skill, scaffolded locally at
  ~/lovstudio/coding/skills/{name}-skill/, symlinked to ~/.claude/skills/
  for immediate use, and registered in the central index at
  ~/lovstudio/coding/skills/index/ (skills.yaml + README.md).
  Lovstudio conventions: `lovstudio:{name}` frontmatter, mandatory README.md
  per skill, AskUserQuestion interactive flow, standalone Python CLI scripts
  with argparse, CJK text handling.
  Use when the user wants to create a new skill, add a skill to the lovstudio
  ecosystem, scaffold a skill, or mentions "新建skill", "创建skill", "封装成skill",
  "new skill", "add skill", "scaffold skill", "生成skill".
license: MIT
compatibility: >
  Scaffolds into ~/lovstudio/coding/skills/. Requires Python 3.8+, git, and gh CLI.
metadata:
  author: lovstudio
  version: "2.0.0"
  tags: skill-creator scaffold generator lovstudio
---

# lovstudio:skill-creator

Scaffold a new lovstudio skill as an **independent GitHub repo** under
`lovstudio/{name}-skill`. The lovstudio ecosystem is no longer a monorepo —
each skill is its own repo, and a central index at
`~/lovstudio/coding/skills/index/` tracks them.

## Architecture

```
~/lovstudio/coding/skills/
├── index/                     ← central catalog (lovstudio/skills repo)
│   ├── skills.yaml            ← machine-readable manifest (paid flag lives here)
│   └── README.md              ← human-readable catalog
├── {name}-skill/              ← each skill is an independent repo
│   ├── SKILL.md
│   ├── README.md
│   ├── CHANGELOG.md           ← managed by skill-optimizer
│   ├── scripts/               ← standalone Python CLI scripts
│   └── references/            ← optional progressive-disclosure docs
└── ...

~/.claude/skills/lovstudio-{name}  ← symlink → ~/.agents/skills/lovstudio-{name}
                                                 → ~/lovstudio/coding/skills/{name}-skill/
```

Key facts:
- GitHub repo name: `lovstudio/{name}-skill` (with `-skill` suffix)
- Local source path: `~/lovstudio/coding/skills/{name}-skill/` (no `lovstudio-` prefix)
- Claude Code reads: `~/.claude/skills/lovstudio-{name}/` (with `lovstudio-` prefix, via symlink)
- Frontmatter `name`: `lovstudio:{name}` (with `:` separator)
- `paid: true/false` lives **only** in `index/skills.yaml`, never in SKILL.md

## Skill Creation Process

### Step 1: Understand the Skill

Ask the user what the skill should do. Start with the most important question
via `AskUserQuestion` — don't dump everything at once.

Key questions:
- What problem does it solve? What's the input → output?
- 2-3 concrete usage examples?
- What user phrases should trigger this skill (中文 + English)?
- Pure-instruction skill, or does it need a Python script?
- Free (public repo) or paid (private repo)?

### Step 2: Plan Contents

Analyze the examples and identify:

1. **Scripts** — deterministic operations → `scripts/`
2. **References** — domain knowledge Claude needs while working → `references/`
3. **Assets** — files used in output (templates, fonts, etc.) → `assets/`

Rules:
- Python scripts must be **standalone single-file CLIs** with `argparse`
- No package structure, no `setup.py`, no `__init__.py`
- CJK text handling is a core concern if the skill deals with documents

### Step 3: Initialize

Run the init script (it auto-detects the target directory):

```bash
python3 ~/.claude/skills/lovstudio-skill-creator/scripts/init_skill.py <name>
```

This creates `~/lovstudio/coding/skills/{name}-skill/` with:

```
{name}-skill/
├── SKILL.md          ← frontmatter + TODO workflow
├── README.md         ← human-readable docs with version badge
└── scripts/          ← empty, ready for implementation
```

Pass `--paid` if this is a paid skill (adjusts README + metadata hints).

### Step 4: Implement

1. **Write scripts** in `scripts/` — test by running directly
2. **Write SKILL.md** — instructions for AI assistants:
   - Frontmatter `description` is the trigger mechanism — cover what + when +
     concrete trigger phrases (中文 + English)
   - Body contains workflow steps, CLI reference, field mappings
   - Use `AskUserQuestion` for interactive prompts before running scripts
   - Keep SKILL.md under 500 lines; split to `references/` if longer
3. **Write README.md** — docs for humans on GitHub:
   - Version badge (source of truth for version)
   - Install command: `git clone https://github.com/lovstudio/{name}-skill ~/.claude/skills/lovstudio-{name}`
   - Dependencies
   - Usage examples, options table
   - ASCII diagrams if useful

See `references/templates.md` for SKILL.md / README.md templates.

### Step 5: Publish

#### 5a. Initialize & push the skill's own repo

```bash
cd ~/lovstudio/coding/skills/<name>-skill
git init
git add -A
git commit -m "feat: initial release of <name> skill"

# Free skill (public):
gh repo create lovstudio/<name>-skill --public --source=. --push

# Paid skill (private):
gh repo create lovstudio/<name>-skill --private --source=. --push
```

#### 5b. Register in the central index

Edit `~/lovstudio/coding/skills/index/skills.yaml` — append under the right
category (category order in the yaml determines display order on the website):

```yaml
  - name: <name>
    repo: lovstudio/<name>-skill
    paid: false                         # or true for paid skills
    category: "<Category>"              # must match an existing category heading
    version: "0.1.0"
    description: "<One-line description matching SKILL.md tagline>"
```

Also add a row to `~/lovstudio/coding/skills/index/README.md` under the matching
category section. Then PR against `lovstudio/skills`:

```bash
cd ~/lovstudio/coding/skills/index
git checkout -b add/<name>
git add skills.yaml README.md
git commit -m "add: <name> skill"
git push -u origin HEAD
gh pr create --fill
```

#### 5c. Symlink for local availability

Make the skill immediately usable in Claude Code:

```bash
# Layer 1: source → .agents
ln -s ~/lovstudio/coding/skills/<name>-skill \
      ~/.agents/skills/lovstudio-<name>

# Layer 2: .agents → .claude/skills (where Claude Code reads)
ln -s ../../.agents/skills/lovstudio-<name> \
      ~/.claude/skills/lovstudio-<name>
```

Verify: `ls ~/.claude/skills/lovstudio-<name>/SKILL.md` resolves.

#### 5d. Trigger lovstudio.ai cache refresh (optional)

After the skill is indexed in `skills.yaml`, the lovstudio.ai `/agent` page caches
the index for 1 hour (Next.js ISR). Trigger on-demand revalidation so the new
skill appears immediately:

```bash
if [ -n "$LOVSTUDIO_REVALIDATE_SECRET" ]; then
  curl -sfX POST https://lovstudio.ai/api/revalidate \
    -H "x-revalidate-secret: $LOVSTUDIO_REVALIDATE_SECRET" \
    -H "content-type: application/json" \
    -d '{"tags":["skills-index"]}' \
    && echo "✓ cache refreshed" \
    || echo "⚠ revalidate failed (will appear within 1h)"
fi
```

Known tags (see `lovstudio/web:src/data/skills.ts`):
- `skills-index` — the yaml index (invalidates all list pages)
- `skill:<id>` — detail for a single skill
- `skill-cases:<id>` — cases.json for a skill

### Step 6: Test & Iterate

1. In a new conversation, invoke `/lovstudio:<name>` — confirm it triggers
2. Notice struggles → edit SKILL.md / scripts in the source repo
3. Commit & push (the symlink chain means no local copy to sync)

## Design Patterns

### Interactive Pre-Execution (MANDATORY for generation/conversion skills)

```markdown
**IMPORTANT: Use `AskUserQuestion` to collect options BEFORE running.**

Use `AskUserQuestion` with the following template:
[options list]

### Mapping User Choices to CLI Args
[table mapping choices to --flags]
```

### Progressive Disclosure

Keep SKILL.md lean. Split to references when:
- Multiple themes/variants → `references/themes.md`
- Complex API docs → `references/api.md`
- Large examples → `references/examples.md`

Reference from SKILL.md: "For theme details, see `references/themes.md`"

### Context-Aware Pre-Fill

For skills that fill or generate content:
1. Check user memory and conversation context first
2. Pre-fill what you can
3. Only ask for fields you truly don't know

## What NOT to Include

- `INSTALLATION_GUIDE.md` — clutter; install instructions go in README.md
- Test files — scripts are tested by running, not with test frameworks
- `__pycache__/`, `*.pyc`, `.DS_Store` — add to `.gitignore`
- `paid` field in frontmatter — it lives only in `index/skills.yaml`

## Migration Note (2026-04)

The ecosystem was refactored from a monorepo (`lovstudio/skills` containing
`skills/lovstudio-<name>/`) + mirror (`lovstudio/pro-skills`) into independent
per-skill repos + central index. The old `lovstudio/pro-skills` was archived.
If working on a legacy skill still in the old structure, migrate it first:

```bash
# 1. Extract from monorepo subdirectory
cp -r ~/projects/lovstudio-skills/skills/lovstudio-<name> \
      ~/lovstudio/coding/skills/<name>-skill
cd ~/lovstudio/coding/skills/<name>-skill
# (remove the lovstudio- prefix from the directory by creating fresh)

# 2. Fresh git history
rm -rf .git
git init && git add -A && git commit -m "import: <name> from monorepo"

# 3. Create independent repo
gh repo create lovstudio/<name>-skill --public --source=. --push
```
