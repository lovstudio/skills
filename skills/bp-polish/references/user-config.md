# User Configuration

This skill follows the portable agent skill profile contract. It must not
assume a private workspace, personal absolute paths, or private brand assets.

## Resolution Order

1. Explicit CLI flags.
2. Environment variables.
3. Shared profile JSON.
4. Safe defaults such as the current working directory or `$HOME/Documents`.
5. Ask the user once for missing required fields.

## Shared Profile

Default profile path:

```bash
${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}
```

Example:

```json
{
  "user": {
    "name": "Your Name",
    "language": "zh-CN",
    "timezone": "Asia/Shanghai"
  },
  "workspace": {
    "root": "$HOME/projects",
    "output_dir": "$HOME/Documents/lov-skill-output"
  },
  "brand": {
    "name": "Your Brand",
    "site": "https://example.com",
    "profile": "$HOME/.skill-publisher/skills/brand.json",
    "design_guide": "$HOME/.skill-publisher/skills/design-guide.md"
  }
}
```

Environment variable overrides:

| Variable | Meaning |
|----------|---------|
| `SKILL_PROFILE_PATH` | Path to the shared profile JSON |
| `SKILLS_CONFIG_DIR` | Shared Skill Publisher skills config/data directory |
| `SKILL_WORKSPACE_ROOT` | User workspace root |
| `SKILL_OUTPUT_DIR` | Default generated output directory |
| `SKILL_PROFILE_PATH` | Brand profile JSON or Markdown |
| `SKILL_DESIGN_GUIDE` | Design guide path |

BP-specific overrides take precedence over shared values:

| Variable | Meaning |
|----------|---------|
| `SKILL_BP_OUTPUT_DIR` | Default output directory for BP workspaces |
| `SKILL_BP_BRAND_PROFILE` | Brand profile used by the deck |
| `SKILL_BP_DESIGN_GUIDE` | Visual design guide used by the deck |

If none are set, use an explicit `--output` path or a project-local
`business-plan/` directory. Never assume an author's private workspace.

## Implementation Notes

- Store source descriptions in `evidence-ledger.md`; do not copy secrets into the
  BP workspace.
- Prefer relative paths inside the workspace so it can be moved or shared.
- Brand files remain user-owned inputs. The public Yoda assets are an example, not
  a default theme.

- Scripts should accept explicit paths via CLI flags.
- Missing profile fields should produce actionable errors.
- Skill Publisher maintainer defaults belong in an optional profile, not in the workflow.
