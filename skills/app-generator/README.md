# lov-app-generator

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

Generate or standardize Skill Publisher apps, choosing web-only, PWA, or Tauri
desktop case-by-case, with React/Vite or Next.js, shadcn/ui, TanStack Query
when useful, Skill Publisher branding, CI/CD/deploy, optional auto update, and
lovinsp.

Independent source repository, also distributed through [skill-publisher dev-skills](https://example.com/skills/dev-skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add skill-publisher/app-generator-skill --all -g
```

The aggregate bundle remains available:

```bash
npx skills add skill-publisher/dev-skills --all -g
```

Or through Claude Code plugin marketplace:

```text
/plugin marketplace add skill-publisher/dev-skills
/plugin install dev-tools@lov-dev
```

Requires: Python 3.8+ for the audit helper. No Python packages are required.

## Usage

```bash
# Ask the assistant:
生成一个 Skill Publisher Tauri App，品牌用 Skill Publisher，包含 shadcn、TanStack Query、CI/CD、自动更新和 lovinsp

# Or create web-only when desktop packaging is not needed:
生成一个只创建 web 的 Skill Publisher App，按需求判断用 Vite 还是 Next.js，包含 Configurable Academic、shadcn 和 lovinsp

# Or audit an existing app:
python3 "${SKILL_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/lov-app-generator}/scripts/audit_app_project.py" --root . --app-type auto --format markdown
```

## What It Does

1. Collects the app brief: name, slug, app type, platform, screens, backend, and release/deploy channel.
2. Audits the target project for Skill Publisher app requirements.
3. Chooses web-only, PWA, or Tauri desktop from the brief instead of forcing desktop packaging.
4. Guides new app scaffolding or incremental upgrade.
5. Applies the Configurable Academic UI system and Skill Publisher brand asset paths.
6. Coordinates related Skill Publisher skills:
   `install-shadcn-ui`, `install-tanstack-query`, `install-tauri-logo`,
   `install-lovinsp`, and `project-port`.
7. Adds or checks CI/CD, web deploy wiring, and Tauri updater wiring when applicable.
8. Runs the lightest reliable verification commands available in the project.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--root` | `.` | Target app root to inspect |
| `--app-type` | `auto` | Audit profile: `auto`, `web`, or `tauri` |
| `--format` | `markdown` | Output format: `markdown` or `json` |
| `--output` | stdout | Optional path to write the audit report |

## User Configuration

Prefer environment variables when local paths differ:

| Variable | Usage |
|---|---|
| `SKILL_APP_GENERATOR_SKILL_DIR` | Installed `lov-app-generator` skill directory |
| `SKILL_DESIGN_GUIDE` | Configurable Academic design guide path |
| `SKILL_PROFILE_PATH` | Skill Publisher brand asset root or profile |

## Brand Configuration

No personal path is built into this repository. Resolve brand assets through
explicit paths, `SKILL_PROFILE_PATH`,
`SKILL_DESIGN_GUIDE`, or the shared profile at
`${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}`.

See `references/user-config.md` for the complete resolution order.

## Audit Helper

```bash
python3 "${SKILL_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/lov-app-generator}/scripts/audit_app_project.py" --root /path/to/app --app-type auto
python3 "${SKILL_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/lov-app-generator}/scripts/audit_app_project.py" --root /path/to/app --app-type web --format json
python3 "${SKILL_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/lov-app-generator}/scripts/audit_app_project.py" --root /path/to/app --app-type tauri --format markdown
```

## License

MIT
