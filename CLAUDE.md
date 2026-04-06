# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A multi-skill repo publishing AI coding assistant skills via [agentskills.io](https://agentskills.io). Each skill lives in `skills/lovstudio-<name>/` with a `SKILL.md` (frontmatter + usage docs) and a `scripts/` folder containing the Python implementation.

## Repo Layout

```
skills/
  lovstudio-<name>/
    SKILL.md          # Skill definition (frontmatter + instructions for AI assistants)
    scripts/          # Python scripts that do the actual work
    references/       # Optional theme/config docs
    examples/         # Optional example files
scripts/              # Repo-level tooling (preview generation, etc.)
dev.sh                # Symlinks source skills into ~/.claude/skills/ for live development
```

## Skills

| Skill | Script | Deps |
|-------|--------|------|
| `any2pdf` | `skills/lovstudio-any2pdf/scripts/md2pdf.py` (reportlab) | `pip install reportlab` |
| `any2docx` | `skills/lovstudio-any2docx/scripts/md2docx.py` (python-docx) | `pip install python-docx` |
| `fill-form` | `skills/lovstudio-fill-form/scripts/fill_form.py` (python-docx) | `pip install python-docx` |

`any2pdf`/`any2docx` convert Markdown → styled output with CJK/Latin mixed text support, themes, cover pages, TOC, watermarks.
`fill-form` fills Word form templates (.docx with table-based fields) with user-provided data.

## Development

```bash
# Live-link all skills for testing in Claude Code sessions
bash dev.sh

# Link a single skill
bash dev.sh lovstudio-any2pdf

# Run a conversion directly
python skills/lovstudio-any2pdf/scripts/md2pdf.py --input foo.md --output foo.pdf --theme warm-academic
python skills/lovstudio-any2docx/scripts/md2docx.py --input foo.md --output foo.docx --theme warm-academic
```

## Adding a New Skill

1. Create `skills/lovstudio-<name>/` with a `SKILL.md` (follow existing frontmatter format: name, description, license, compatibility, metadata)
2. Add scripts in `skills/lovstudio-<name>/scripts/`
3. Update `README.md` table

## Key Conventions

- Skill names use prefix `lovstudio:` (e.g. `lovstudio:any2pdf`)
- Directory names use prefix `lovstudio-` (e.g. `lovstudio-any2pdf`), all under `skills/`
- Both skills share the same set of 14 color themes (warm-academic, nord-frost, github-light, etc.)
- SKILL.md files must use `AskUserQuestion` to prompt users for options before running conversion — never skip this interactive step
- Python scripts are standalone single-file CLIs with `argparse`; no package structure
- CJK text handling is a core concern — font switching, mixed-text rendering, and line wrapping must work correctly
