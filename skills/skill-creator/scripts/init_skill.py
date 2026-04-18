#!/usr/bin/env python3
"""
Initialize a new lovstudio skill as an independent repo scaffold.

Usage:
    python3 init_skill.py <name>
    python3 init_skill.py <name> --paid
    python3 init_skill.py <name> --path /custom/path

Creates ~/lovstudio/coding/skills/<name>-skill/ by default.

Examples:
    python3 init_skill.py fill-form   → ~/lovstudio/coding/skills/fill-form-skill/
    python3 init_skill.py any2pptx    → ~/lovstudio/coding/skills/any2pptx-skill/
"""

import sys, argparse
from pathlib import Path

SKILL_MD = '''---
name: lovstudio:{name}
description: >
  TODO: What this skill does (1-2 sentences).
  TODO: When to trigger — specific scenarios, file types, user phrases.
  Also trigger when the user mentions "TODO_CN", "TODO_EN".
license: MIT
compatibility: >
  TODO: Requires Python 3.8+ and <library> (`pip install <library>`).
  Cross-platform: macOS, Windows, Linux.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: TODO
---

# {name} — TODO: Short Title

TODO: 1-2 sentence overview.

## When to Use

- TODO: Scenario 1
- TODO: Scenario 2

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: TODO

```bash
python3 ~/.claude/skills/lovstudio-{name}/scripts/TODO.py --help
```

### Step 2: Ask the user

**IMPORTANT: Use `AskUserQuestion` to collect options BEFORE running.**

### Step 3: Execute

```bash
python3 ~/.claude/skills/lovstudio-{name}/scripts/TODO.py --input <path> --output <path>
```

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | TODO |
| `--output` | `output.ext` | TODO |

## Dependencies

```bash
pip install TODO --break-system-packages
```
'''

README_MD = '''# lovstudio:{name}

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

TODO: One-line description.

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/{name}-skill ~/.claude/skills/lovstudio-{name}
```

Requires: Python 3.8+ and `pip install TODO`

## Usage

```bash
python3 ~/.claude/skills/lovstudio-{name}/scripts/TODO.py --input file.ext --output result.ext
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | (required) | TODO |
| `--output` | `output.ext` | TODO |

## License

MIT
'''

GITIGNORE = '''__pycache__/
*.pyc
*.pyo
.DS_Store
.venv/
venv/
node_modules/
.env
.env.local
'''


def main():
    ap = argparse.ArgumentParser(description="Initialize a new lovstudio skill")
    ap.add_argument("name", help="Skill short name (no prefix / no -skill suffix)")
    ap.add_argument("--path", default="", help="Custom base directory (default: ~/lovstudio/coding/skills/)")
    ap.add_argument("--paid", action="store_true", help="Mark as paid in hints (actual paid flag lives in index/skills.yaml)")
    args = ap.parse_args()

    # Normalize: strip common prefixes / suffix users might paste
    name = args.name
    for pfx in ("lovstudio:", "lovstudio-"):
        if name.startswith(pfx):
            name = name[len(pfx):]
    if name.endswith("-skill"):
        name = name[: -len("-skill")]

    base = Path(args.path) if args.path else (Path.home() / "lovstudio" / "coding" / "skills")
    base.mkdir(parents=True, exist_ok=True)
    skill_dir = base / f"{name}-skill"

    if skill_dir.exists():
        print(f"ERROR: {skill_dir} already exists", file=sys.stderr)
        sys.exit(1)

    skill_dir.mkdir()
    (skill_dir / "scripts").mkdir()

    (skill_dir / "SKILL.md").write_text(SKILL_MD.format(name=name))
    (skill_dir / "README.md").write_text(README_MD.format(name=name))
    (skill_dir / ".gitignore").write_text(GITIGNORE)

    print(f"✓ Created {skill_dir}/")
    print(f"  SKILL.md      — AI-facing frontmatter + workflow")
    print(f"  README.md     — human-facing GitHub docs")
    print(f"  scripts/      — add Python CLI scripts here")
    print(f"  .gitignore")
    print()
    print("Next steps:")
    print(f"  1. cd {skill_dir}")
    print(f"  2. Implement scripts/ and fill TODO placeholders in SKILL.md / README.md")
    print(f"  3. git init && git add -A && git commit -m 'feat: initial release of {name} skill'")
    visibility = "--private" if args.paid else "--public"
    print(f"  4. gh repo create lovstudio/{name}-skill {visibility} --source=. --push")
    print(f"  5. Symlink:")
    print(f"       ln -s {skill_dir} ~/.agents/skills/lovstudio-{name}")
    print(f"       ln -s ../../.agents/skills/lovstudio-{name} ~/.claude/skills/lovstudio-{name}")
    paid_flag = "true" if args.paid else "false"
    print(f"  6. Register in ~/lovstudio/coding/skills/index/skills.yaml (paid: {paid_flag})")


if __name__ == "__main__":
    main()
