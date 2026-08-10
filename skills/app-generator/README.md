# sgc-app-generator

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

Generate or standardize Lovstudio apps, choosing web-only, PWA, or Tauri
desktop case-by-case, with React/Vite or Next.js, shadcn/ui, TanStack Query
when useful, Lovstudio branding, CI/CD/deploy, optional auto update, and
lovinsp.

Independent source repository, also distributed through [lovstudio dev-skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/app-generator-skill --all -g
```

The aggregate bundle remains available:

```bash
npx skills add lovstudio/skills --all -g
```

Or through Claude Code plugin marketplace:

```text
/plugin marketplace add lovstudio/skills
/plugin install dev-tools@sgc-dev
```

Requires: Python 3.8+ for the audit helper. No Python packages are required.

## Usage

```bash
# Ask the assistant:
生成一个 Lovstudio Tauri App，品牌用 Lovstudio，包含 shadcn、TanStack Query、CI/CD、自动更新和 lovinsp

# Or create web-only when desktop packaging is not needed:
生成一个只创建 web 的 Lovstudio App，按需求判断用 Vite 还是 Next.js，包含 Warm Academic、shadcn 和 lovinsp

# Or audit an existing app:
python3 "${LOVSTUDIO_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/sgc-app-generator}/scripts/audit_app_project.py" --root . --app-type auto --format markdown
```

## What It Does

1. Collects the app brief: name, slug, app type, platform, screens, backend, and release/deploy channel.
2. Audits the target project for Lovstudio app requirements.
3. Chooses web-only, PWA, or Tauri desktop from the brief instead of forcing desktop packaging.
4. Guides new app scaffolding or incremental upgrade.
5. Applies the Warm Academic UI system and Lovstudio brand asset paths.
6. Coordinates related Lovstudio skills:
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
| `LOVSTUDIO_APP_GENERATOR_SKILL_DIR` | Installed `sgc-app-generator` skill directory |
| `LOVSTUDIO_SKILLS_DESIGN_GUIDE` | Warm Academic design guide path |
| `LOVSTUDIO_SKILLS_BRAND_PROFILE` | Lovstudio brand asset root or profile |

## Brand Configuration

No personal path is built into this repository. Resolve brand assets through
explicit paths, `LOVSTUDIO_SKILLS_BRAND_PROFILE`,
`LOVSTUDIO_SKILLS_DESIGN_GUIDE`, or the shared profile at
`${LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}`.

See `references/user-config.md` for the complete resolution order.

## Audit Helper

```bash
python3 "${LOVSTUDIO_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/sgc-app-generator}/scripts/audit_app_project.py" --root /path/to/app --app-type auto
python3 "${LOVSTUDIO_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/sgc-app-generator}/scripts/audit_app_project.py" --root /path/to/app --app-type web --format json
python3 "${LOVSTUDIO_APP_GENERATOR_SKILL_DIR:-$HOME/.claude/skills/sgc-app-generator}/scripts/audit_app_project.py" --root /path/to/app --app-type tauri --format markdown
```

## License

MIT
