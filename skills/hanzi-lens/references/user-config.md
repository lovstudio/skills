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
${LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}
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
    "output_dir": "$HOME/Documents/sgc-skill-output"
  },
  "brand": {
    "name": "Your Brand",
    "site": "https://example.com",
    "profile": "$HOME/.lovstudio/skills/brand.json",
    "design_guide": "$HOME/.lovstudio/skills/design-guide.md"
  }
}
```

Environment variable overrides:

| Variable | Meaning |
|----------|---------|
| `LOVSTUDIO_SKILLS_PROFILE` | Path to the shared profile JSON |
| `LOVSTUDIO_SKILLS_HOME` | Shared LovStudio skills config/data directory |
| `LOVSTUDIO_SKILLS_WORKSPACE_ROOT` | User workspace root |
| `LOVSTUDIO_SKILLS_OUTPUT_DIR` | Default generated output directory |
| `LOVSTUDIO_SKILLS_BRAND_PROFILE` | Brand profile JSON or Markdown |
| `LOVSTUDIO_SKILLS_DESIGN_GUIDE` | Design guide path |

Skill-specific overrides:

| Variable | Meaning |
|----------|---------|
| `LOVSTUDIO_HANZI_LENS_OUTPUT_DIR` | Hanzi Lens output root |
| `LOVSTUDIO_HANZI_LENS_INFOGRAPHIC_SKILL_DIR` | Installed `sgc-professional-infographic` directory |
| `LOVSTUDIO_SKILLS_INSTALL_DIR` | Shared Agent Skills installation directory |

## Implementation Notes

- Scripts should accept explicit paths via CLI flags.
- Missing profile fields should produce actionable errors.
- LovStudio maintainer defaults belong in an optional profile, not in the workflow.
