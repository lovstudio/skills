# lovstudio:skill-creator

![Version](https://img.shields.io/badge/version-2.0.0-CC785C)

Scaffold new skills for the lovstudio ecosystem. Each skill is an **independent
GitHub repo** at `lovstudio/{name}-skill`, registered in the central index at
[`lovstudio/skills`](https://github.com/lovstudio/skills).

Part of [lovstudio skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/skill-creator-skill ~/.claude/skills/lovstudio-skill-creator
```

## What It Does

```
┌────────────────────────────────────────────────────────────┐
│  You: "封装成 wcx skill"                                    │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│  init_skill.py wcx                                          │
│                                                             │
│  ~/lovstudio/coding/skills/wcx-skill/                       │
│  ├── SKILL.md      ← AI reads this                          │
│  ├── README.md     ← Humans read this on GitHub             │
│  ├── .gitignore                                             │
│  └── scripts/      ← Python CLI scripts                     │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│  Implement → gh repo create lovstudio/wcx-skill --push      │
│           → PR into index/skills.yaml + index/README.md     │
│           → symlink to ~/.claude/skills/lovstudio-wcx       │
└────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Scaffold
python3 ~/.claude/skills/lovstudio-skill-creator/scripts/init_skill.py wcx

# → ~/lovstudio/coding/skills/wcx-skill/
#     ├── SKILL.md       (TODO placeholders)
#     ├── README.md      (version badge + install stub)
#     ├── .gitignore
#     └── scripts/
```

Then:

1. Implement `scripts/` and fill the TODOs in `SKILL.md` / `README.md`
2. `cd ~/lovstudio/coding/skills/wcx-skill && git init && git add -A && git commit -m "feat: initial release"`
3. `gh repo create lovstudio/wcx-skill --public --source=. --push`
4. Add an entry to `~/lovstudio/coding/skills/index/skills.yaml` + a row to its `README.md`, then PR
5. Symlink into `~/.claude/skills/lovstudio-wcx` for local use

## Architecture

The lovstudio skill ecosystem (2026-04-16 refactor):

| Layer | Location | Purpose |
|-------|----------|---------|
| Central index | `lovstudio/skills` repo & `~/lovstudio/coding/skills/index/` | `skills.yaml` + human README; consumed by agentskills.io & lovstudio.ai/agent |
| Per-skill repo | `lovstudio/{name}-skill` & `~/lovstudio/coding/skills/{name}-skill/` | All skill code + SKILL.md + README.md + CHANGELOG.md |
| Local Claude Code | `~/.claude/skills/lovstudio-{name}/` | Symlink chain into the per-skill repo |

`paid: true/false` lives **only** in `index/skills.yaml` — never in SKILL.md.

## Differences from Official skill-creator

| | Official | Lovstudio |
|--|----------|-----------|
| **README.md** | Explicitly forbidden | **Required** — repos are on GitHub |
| **Frontmatter** | `name` + `description` | + `license`, `compatibility`, `metadata.version`, `tags` |
| **Naming** | Any | `lovstudio:{name}` (frontmatter) / `{name}-skill/` (directory & repo) |
| **Scripts** | Any format | Standalone Python CLI with `argparse` |
| **Distribution** | `.skill` package | `git clone` each skill repo into `~/.claude/skills/lovstudio-{name}` |
| **Interactive** | Optional | `AskUserQuestion` mandatory for generation/conversion skills |
| **Central catalog** | — | `skills.yaml` + `README.md` in `lovstudio/skills` |

## License

MIT
