#!/usr/bin/env python3
"""
Initialize a new lovstudio skill with proper directory structure.

Usage:
    python init_skill.py <name>
    python init_skill.py <name> --path /custom/path

Examples:
    python init_skill.py fill-form        → skills/lovstudio-fill-form/
    python init_skill.py any2pptx         → skills/lovstudio-any2pptx/
"""

import sys, os, argparse
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
  version: "1.0.0"
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
python lovstudio-{name}/scripts/TODO.py --help
```

### Step 2: Ask the user

**IMPORTANT: Use `AskUserQuestion` to collect options BEFORE running.**

### Step 3: Execute

```bash
python lovstudio-{name}/scripts/TODO.py --input <path> --output <path>
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

TODO: One-line description.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:{name}
```

Requires: Python 3.8+ and `pip install TODO`

## Usage

```bash
python TODO.py --input file.ext --output result.ext
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | (required) | TODO |
| `--output` | `output.ext` | TODO |

## License

MIT
'''


def main():
    ap = argparse.ArgumentParser(description="Initialize a new lovstudio skill")
    ap.add_argument("name", help="Skill name (without lovstudio- prefix)")
    ap.add_argument("--path", default="", help="Custom base path (default: skills/ in repo root)")
    args = ap.parse_args()

    name = args.name.removeprefix("lovstudio-").removeprefix("lovstudio:")

    # Find repo root (look for CLAUDE.md or .git)
    if args.path:
        base = Path(args.path)
    else:
        cwd = Path.cwd()
        repo_root = cwd
        for parent in [cwd] + list(cwd.parents):
            if (parent / "CLAUDE.md").exists() or (parent / ".git").exists():
                repo_root = parent
                break
        base = repo_root / "skills"

    skill_dir = base / f"lovstudio-{name}"

    if skill_dir.exists():
        print(f"ERROR: {skill_dir} already exists", file=sys.stderr)
        sys.exit(1)

    # Create structure
    skill_dir.mkdir(parents=True)
    (skill_dir / "scripts").mkdir()

    (skill_dir / "SKILL.md").write_text(SKILL_MD.format(name=name).lstrip())
    (skill_dir / "README.md").write_text(README_MD.format(name=name).lstrip())

    print(f"Created skill at {skill_dir}/")
    print(f"  SKILL.md    — edit frontmatter description + workflow")
    print(f"  README.md   — edit for GitHub readers")
    print(f"  scripts/    — add Python CLI scripts")
    print()
    print("Next steps:")
    print(f"  1. Implement scripts in scripts/")
    print(f"  2. Fill in TODO placeholders in SKILL.md and README.md")
    print(f"  3. Update root README.md and CLAUDE.md skills tables")
    print(f"  4. Test: bash dev.sh lovstudio-{name}")


if __name__ == "__main__":
    main()
