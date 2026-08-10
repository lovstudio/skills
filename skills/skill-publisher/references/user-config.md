# Publisher User Configuration

Publishing needs persistent channel settings, while secrets remain in environment
variables or credential stores.

## First-run initialization

1. Prefill source roots and target accounts from the current request.
2. Read environment variables and the shared profile.
3. Infer safe local output directories.
4. Ask once only for required channel values still missing.
5. Show non-secret values before saving them to the profile.

## Shared profile

```bash
${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}
```

Recommended shape:

```json
{
  "publisher": {
    "github_org": "YOUR_ORG",
    "default_visibility": "private",
    "output_dir": "$HOME/Documents/skill-releases",
    "skill-publisher": {
      "catalog": "$HOME/lovstudio/coding/lovstudio-skills",
      "site_url": "https://example.com/skills"
    },
    "workbuddy": {
      "profile_dir": "$HOME/.skill-publisher/skills/publish/workbuddy"
    }
  }
}
```

## Secret handling

- Use `gh auth` for GitHub credentials.
- Resolve revalidation and platform tokens from environment or a credential store.
- Never print, persist into the shared JSON profile, or copy secrets into source.
- Channel adapters should name the missing environment variable without echoing
  its value.
