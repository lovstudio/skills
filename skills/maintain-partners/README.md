# lovstudio:maintain-partners

![Version](https://img.shields.io/badge/version-0.4.0-CC785C)

Maintain the LovStudio website's "Trusted By" partners section: collect brand
logos through `lovstudio-find-logo`, normalize to the 80px canvas, append
entries with i18n taglines across 4 locales, and audit for dead URLs /
missing assets.

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/maintain-partners-skill ~/.claude/skills/lovstudio-maintain-partners
git clone https://github.com/lovstudio/find-logo-skill ~/.claude/skills/lovstudio-find-logo
pip install Pillow --break-system-packages
brew install librsvg  # for SVG logo sources
```

## What it does

The LovStudio homepage runs a "Trusted By" strip that renders 30+ partner
logos against a `grayscale opacity-60` filter. Maintaining it means three
recurring tasks:

1. **Collecting** — invoking `lovstudio-find-logo` to pull and archive brand logos.
2. **Normalizing** — every logo must trim to its content bbox and resize to
   exactly 80px tall so the strip looks even. White-on-transparent logos must
   be inverted so they show on the light background.
3. **Wiring** — appending the partner to `PARTNERS` in
   `WorkshopDispatch.tsx` and adding a `partner*Tagline` key to all 4 locale
   JSONs (zh-CN / en / ja / th).

Logo discovery is delegated to `lovstudio-find-logo`; this skill does not keep
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
python3 ~/.claude/skills/lovstudio-find-logo/scripts/find_logo.py \
  --name "Example" --url https://example.com --slug example --json

# Normalize: auto-invert white-on-transparent
normalize_logo.py --src ~/.lovstudio/logo-collection/example/logo.png \
                  --dst public/partners/example/logo.png

# Add to PARTNERS + i18n
add_partner.py --name "Example" --href "https://example.com" \
               --logo "/partners/example/logo.png" \
               --key partnerExampleTagline \
               --zh "Example · 一句话定位" \
               --en "Example · one-line positioning" \
               --ja "Example · 一行紹介" \
               --th "Example · บรรยายหนึ่งบรรทัด"

# Audit (use --probe to HTTP-check every URL)
audit_partners.py --probe
```

## Repo layout assumed

```
~/lovstudio/coding/web/
├── app/(main)/(home)/WorkshopDispatch.tsx   ← PARTNERS array
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
