# User Configuration

This skill can maintain any site that follows the same partner-strip shape as
the Skill Publisher website. It should not require Mark's local path.

## Website Root

Resolve the website repo root in this order:

1. `--repo <path>` on `add_partner.py` or `audit_partners.py`.
2. `SKILL_MAINTAIN_PARTNERS_SITE_ROOT`.
3. Shared profile JSON at
   `${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}`.
4. Fallback to `$HOME/skill-publisher/coding/web` only if that repo exists.

`SKILL_WEB_ROOT` and `PARTNERS_SITE_ROOT` are accepted as legacy aliases.

Resolve the partners TSX file in this order:

1. `--partners-file <path>` on `add_partner.py` or `audit_partners.py`.
2. `SKILL_MAINTAIN_PARTNERS_FILE`.
3. Shared profile keys `sites.partners_file`, `skill-publisher.partners_file`,
   `partners.file`, or `workspace.partners_file`.
4. `app/(main)/(home)/PartnersGrid.tsx`, then legacy
   `app/(main)/(home)/WorkshopDispatch.tsx`.

`SKILL_PARTNERS_FILE` and `PARTNERS_FILE` are accepted as legacy aliases.

Supported profile keys:

```json
{
  "sites": {
    "skill-publisher_web": "$HOME/skill-publisher/coding/web",
    "partners_file": "app/(main)/(home)/PartnersGrid.tsx"
  },
  "skill-publisher": {
    "web_root": "$HOME/skill-publisher/coding/web",
    "partners_file": "app/(main)/(home)/PartnersGrid.tsx"
  },
  "workspace": {
    "web_root": "$HOME/skill-publisher/coding/web",
    "website_root": "$HOME/skill-publisher/coding/web",
    "partners_file": "app/(main)/(home)/PartnersGrid.tsx"
  }
}
```

## Required Site Shape

```text
<web-root>/
├── app/(main)/(home)/PartnersGrid.tsx       # PARTNERS array
├── public/partners/<slug>/logo.png          # logo files
└── src/i18n/messages/
    ├── zh-CN.json
    ├── en.json
    ├── ja.json
    └── th.json
```

If a user's site uses different file names or locale paths, do not edit blindly.
Ask for the equivalent paths and add explicit CLI flags before proceeding.
