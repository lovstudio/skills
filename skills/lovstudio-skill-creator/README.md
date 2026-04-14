# lovstudio:skill-creator

![Version](https://img.shields.io/badge/version-1.1.0-CC785C)

Scaffold new skills for the [lovstudio/skills](https://github.com/lovstudio/skills) repo. Fork of the official [skill-creator](https://github.com/anthropics/agent-skills) with lovstudio conventions baked in.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:skill-creator
```

## What It Does

```
┌──────────────────────────────────────────────────────┐
│  You: "创建一个 any2pptx skill"                       │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  init_skill.py any2pptx                              │
│                                                      │
│  skills/lovstudio-any2pptx/                          │
│  ├── SKILL.md      ← AI reads this (frontmatter +   │
│  │                    workflow + CLI reference)       │
│  ├── README.md     ← Humans read this on GitHub      │
│  └── scripts/      ← Python CLI scripts              │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  Fill in TODOs → implement scripts → test → register │
│  → update root README.md + CLAUDE.md                 │
└──────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Scaffold a new skill
python skills/lovstudio-skill-creator/scripts/init_skill.py any2pptx

# Output:
#   skills/lovstudio-any2pptx/
#   ├── SKILL.md     (with TODO placeholders)
#   ├── README.md    (with TODO placeholders)
#   └── scripts/
```

Then:
1. Implement scripts in `scripts/`
2. Fill in TODOs in `SKILL.md` and `README.md`
3. Add to root `README.md` and `CLAUDE.md`
4. Test: `bash dev.sh lovstudio-any2pptx`

## Differences from Official skill-creator

| | Official | Lovstudio |
|--|----------|-----------|
| **README.md** | Explicitly forbidden | **Required** — repo is on GitHub |
| **Frontmatter** | `name` + `description` only | + `license`, `compatibility`, `metadata` |
| **Naming** | Any | `lovstudio:<name>` / `lovstudio-<name>/` |
| **Directory** | Anywhere | `skills/lovstudio-<name>/` |
| **Scripts** | Any format | Standalone Python CLI with `argparse` |
| **Distribution** | `.skill` package | `npx skills add lovstudio/skills` |
| **Interactive** | Optional | `AskUserQuestion` mandatory for conversion skills |

## License

MIT
