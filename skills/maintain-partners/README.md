# lov-maintain-partners

![Version](https://img.shields.io/badge/version-0.10.0-CC785C)

Maintain the Skill Publisher website's "Trusted By" partners section: collect brand
logos through `lov-find-logo`, normalize to the 80px canvas, append
entries with i18n taglines across 4 locales, and audit for dead URLs /
missing assets.

Part of [skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
SKILLS_DIR="${SKILL_SKILLS_INSTALL_DIR:?Set SKILL_SKILLS_INSTALL_DIR}"
git clone https://example.com/skills/maintain-partners-skill "$SKILLS_DIR/lov-maintain-partners"
git clone https://example.com/skills/find-logo-skill "$SKILLS_DIR/lov-find-logo"
python3 -m pip install Pillow
brew install librsvg  # for SVG logo sources
```

## Configuration

Set the website repo root with `--repo`, `SKILL_MAINTAIN_PARTNERS_SITE_ROOT`, or the shared
profile at `${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}`.
`SKILL_WEB_ROOT` and `PARTNERS_SITE_ROOT` remain accepted as legacy aliases.

Set the PARTNERS TSX file with `--partners-file`, `SKILL_MAINTAIN_PARTNERS_FILE`, or profile
keys. The default checks `app/(main)/(home)/PartnersGrid.tsx` first, then
legacy `app/(main)/(home)/WorkshopDispatch.tsx`.
`SKILL_PARTNERS_FILE` and `PARTNERS_FILE` remain accepted as legacy aliases.

Supported profile keys:

```json
{
  "sites": {
    "skill-publisher_web": "$HOME/projects/my-site",
    "partners_file": "app/(main)/(home)/PartnersGrid.tsx"
  },
  "skill-publisher": {
    "web_root": "$HOME/projects/my-site",
    "partners_file": "app/(main)/(home)/PartnersGrid.tsx"
  },
  "workspace": {
    "web_root": "$HOME/projects/my-site",
    "partners_file": "app/(main)/(home)/PartnersGrid.tsx"
  }
}
```

## What it does

The Skill Publisher homepage runs a "Trusted By" strip that renders 30+ partner
logos against a `grayscale opacity-60` filter. Maintaining it means three
recurring tasks:

1. **Collecting** — invoking `lov-find-logo` to pull and archive brand logos.
2. **Normalizing** — every logo must trim to its content bbox and resize to
   exactly 80px tall so the strip looks even. White-on-transparent logos must
   be inverted so they show on the light background.
3. **Wiring** — appending the partner to `PARTNERS` in the configured partners
   TSX file and adding a `partner*Tagline` key to all 4 locale JSONs
   (zh-CN / en / ja / th).

Logo discovery is delegated to `lov-find-logo`; this skill does not keep
its own homepage crawler or fallback scraper.

This skill is three single-file Python CLIs plus an AI workflow that orchestrates them.

## Scripts

```text
normalize_logo.py   Trim, optional inversion, resize to 80px, write PNG
add_partner.py      Append to PARTNERS array + i18n JSONs (idempotent)
audit_partners.py   Walk PARTNERS; report missing logos / i18n keys / dead URLs
```

## Quick examples

```bash
# Collect a logo through the required find-logo skill
SKILL_ROOT="${SKILL_SKILLS_INSTALL_DIR:?Set SKILL_SKILLS_INSTALL_DIR}"
WEB_ROOT="${SKILL_MAINTAIN_PARTNERS_SITE_ROOT:?Set this or pass --repo}"
PARTNERS_TSX="${SKILL_MAINTAIN_PARTNERS_FILE:-app/(main)/(home)/PartnersGrid.tsx}"

python3 "$SKILL_ROOT/lov-find-logo/scripts/find_logo.py" \
  --name "Example" --url https://example.com --slug example --json

# Normalize: auto-invert white-on-transparent
normalize_logo.py --src ~/.skill-publisher/logo-collection/example/logo.png \
                  --dst "$WEB_ROOT/public/partners/example/logo.png"

# Add to PARTNERS + i18n
add_partner.py --repo "$WEB_ROOT" \
               --partners-file "$PARTNERS_TSX" \
               --name "Example" --href "https://example.com" \
               --logo "/partners/example/logo.png" \
               --key partnerExampleTagline \
               --category community \
               --zh "Example · 一句话定位" \
               --en "Example · one-line positioning" \
               --ja "Example · 一行紹介" \
               --th "Example · บรรยายหนึ่งบรรทัด"

# Audit (use --probe to HTTP-check every URL)
audit_partners.py --repo "$WEB_ROOT" --partners-file "$PARTNERS_TSX" --probe
```

## Repo layout assumed

```
<web-root>/
├── app/(main)/(home)/PartnersGrid.tsx       ← PARTNERS array
├── public/partners/<slug>/logo.png          ← logo files
└── src/i18n/messages/
    ├── zh-CN.json    ← dispatch.partner*Tagline
    ├── en.json
    ├── ja.json
    └── th.json
```

If you fork this for another site, edit the constants at the top of each script.

## License

MIT
