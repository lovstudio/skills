# User Configuration

Reusable app generation must not assume a maintainer's local workspace or
brand directory.

Resolve settings in this order:

1. Explicit paths supplied in the current request.
2. Skill-specific or shared environment variables.
3. The shared profile JSON.
4. Safe defaults that do not require private files.
5. Ask once when a required value remains missing.

## Environment variables

| Variable | Meaning |
|---|---|
| `LOVSTUDIO_APP_GENERATOR_SKILL_DIR` | Installed skill directory |
| `LOVSTUDIO_SKILLS_BRAND_PROFILE` | Brand asset directory or profile file |
| `LOVSTUDIO_SKILLS_DESIGN_GUIDE` | Design guide path |
| `LOVSTUDIO_SKILLS_PROFILE` | Shared LovStudio skills profile JSON |

The default shared profile is
`$HOME/.lovstudio/skills/profile.json`. Paths inside it may use `$HOME` and
must be expanded at runtime.
