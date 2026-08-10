# Automatic User Initialization

Add this layer only when a Skill needs persistent workspace, identity, brand,
locale, output, model, provider, or integration settings across runs.

## Decision rule

Use `--user-config` when at least one required value should persist beyond the
current invocation. Omit it when explicit inputs and the current directory are
sufficient. Infer this from the Skill's behavior; do not ask users to choose a
configuration mode.

Every generated Skill remains portable. LovStudio and other brands use the same
fields with different values; there is no internal-only variant.

## First-run flow

1. Prefill from the current request and project.
2. Apply explicit CLI and environment values.
3. Read the shared profile.
4. Infer safe defaults.
5. Ask once only for required user-facing values that remain unknown.
6. Show what will be saved and persist it with the user's knowledge.

## Resolution order

1. Explicit CLI flags or current request.
2. Skill-specific environment variables.
3. Shared profile JSON.
4. Safe defaults such as the current directory or `$HOME/Documents`.
5. One focused question for a remaining required value.

Default profile:

```bash
${LOVSTUDIO_SKILLS_PROFILE:-$HOME/.lovstudio/skills/profile.json}
```

Recommended portable fields:

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
    "profile": "$HOME/.lovstudio/skills/brand.json",
    "design_guide": "$HOME/.lovstudio/skills/design-guide.md"
  }
}
```

Do not commit resolved personal values, private absolute paths, credentials, or
provider tokens into reusable Skill source.
