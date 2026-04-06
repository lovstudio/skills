---
name: lovstudio:skill-creator
description: >
  Create new skills for the lovstudio/skills repo. Fork of the official
  skill-creator with lovstudio conventions: lovstudio: name prefix,
  skills/lovstudio-<name>/ directory structure, mandatory README.md per skill,
  SKILL.md with AskUserQuestion interactive flow, standalone Python CLI scripts,
  CJK text handling, and auto-update of root README + CLAUDE.md.
  Use when the user wants to create a new skill, add a skill to this repo,
  scaffold a skill, or mentions "新建skill", "创建skill", "new skill",
  "add skill", "生成skill".
license: MIT
compatibility: >
  Works within the lovstudio/skills repo. Requires Python 3.8+.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: skill-creator scaffold generator lovstudio
---

# lovstudio:skill-creator

Create new skills for the lovstudio/skills repo. Based on the official
skill-creator methodology with lovstudio-specific conventions layered on top.

## Lovstudio Conventions (Override Official)

These OVERRIDE the official skill-creator defaults:

| Official | Lovstudio Override |
|----------|-------------------|
| `name` only in frontmatter | `name`, `description`, `license`, `compatibility`, `metadata` |
| No README.md | **README.md is REQUIRED** — this repo is on GitHub, humans read it |
| Any directory structure | `skills/lovstudio-<name>/` under repo root |
| Any naming | Name: `lovstudio:<name>`, Dir: `lovstudio-<name>` |
| Packaging with .skill | Publishing via `npx skills add lovstudio/skills` |

## Skill Creation Process

### Step 1: Understand the Skill

Ask the user what the skill should do. Key questions:

- What problem does it solve? What's the input → output?
- Can you give 2-3 concrete usage examples?
- What would a user say that should trigger this skill?
- Does it need a Python script, or is it pure instructions?

Use `AskUserQuestion` — don't dump all questions at once, start with the most important.

### Step 2: Plan Contents

Analyze each example and identify:

1. **Scripts** — deterministic operations that get rewritten every time → `scripts/`
2. **References** — domain knowledge Claude needs while working → `references/`
3. **Assets** — files used in output (templates, fonts, etc.) → `assets/`

Rules for this repo:
- Python scripts must be **standalone single-file CLIs** with `argparse`
- No package structure, no setup.py, no __init__.py
- CJK text handling is a core concern if the skill deals with documents

### Step 3: Initialize

Run the init script:

```bash
python skills/lovstudio-skill-creator/scripts/init_skill.py <name>
```

This creates:

```
skills/lovstudio-<name>/
├── SKILL.md          # Frontmatter + TODO placeholders
├── README.md         # Human-readable docs for GitHub
└── scripts/          # Empty, ready for implementation
```

The script auto-generates:
- SKILL.md with lovstudio frontmatter template
- README.md with install command, usage, options table stubs
- scripts/ directory

### Step 4: Implement

1. **Write scripts** in `scripts/` — test them by running directly
2. **Write SKILL.md** — instructions for AI assistants:
   - Frontmatter `description` is the trigger mechanism — be comprehensive
   - Body contains workflow steps, CLI reference, field mappings
   - Use `AskUserQuestion` for interactive prompts before running scripts
   - Keep SKILL.md under 500 lines; split to `references/` if longer
3. **Write README.md** — docs for humans on GitHub:
   - Install command: `npx skills add lovstudio/skills --skill lovstudio:<name>`
   - Dependencies
   - Usage examples with code blocks
   - Options/arguments table
   - ASCII diagrams for visual explanation (if applicable)

See `references/templates.md` for SKILL.md and README.md templates.

### Step 5: Register

After the skill is complete, update these files:

1. **`CLAUDE.md`** — add row to Skills table:
   ```
   | `<name>` | `skills/lovstudio-<name>/scripts/<script>.py` (<lib>) | `pip install <lib>` |
   ```

2. **Root `README.md`** — add row to Available Skills table:
   ```
   | [<name>](skills/lovstudio-<name>/) | One-line description. |
   ```

### Step 6: Test & Iterate

1. Symlink for live testing: `bash dev.sh lovstudio-<name>`
2. Use the skill in a real conversation
3. Notice struggles → fix SKILL.md or scripts
4. Repeat

## Design Patterns

### Interactive Pre-Execution (MANDATORY for conversion/generation skills)

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

- CHANGELOG.md, INSTALLATION_GUIDE.md — unnecessary clutter
- Test files — scripts are tested by running, not with test frameworks
- __pycache__, .pyc, .DS_Store — add to .gitignore
