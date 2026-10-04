# Publishing to Skill Publisher

This adapter turns validated local source into a GitHub-backed Skill Publisher release,
catalog entry, and verified live detail page.

## Inputs

- Local Skill source path.
- GitHub organization and desired repository visibility.
- The current `lov-skill-pricing` Pricing Card, including free/paid status,
  public CNY price or free-entry decision, confidence, and review trigger.
- Unified `lovstudio/skills` catalog checkout.
- Expected version and a release-specific visible marker.
- Revalidation secret resolved as `LOVSTUDIO_REVALIDATE_SECRET` without printing it.

## Source repository and release

From the validated source directory:

```bash
python3 scripts/validate_skill.py .
git init -b main                         # only when source has no repository
git add -A
git commit -m "feat: initial release"
gh repo create ORG/NAME-skill --VISIBILITY --source=. --push
git tag vVERSION
git push origin vVERSION
gh release create vVERSION --generate-notes
```

For an existing repository, preserve its branch and history, update from the
remote first, commit only intended changes, then tag from the verified commit.

## Paid delivery contract

Paid Skills are not encrypted. Paying only controls who can download a Skill:

- Keep the paid source repository private and tag the release as `v{version}`.
  The website download prefers that tag and falls back to the default branch.
- Set `skill_path` in the catalog when SKILL.md is not at the repository root.
- Commit everything the Skill needs at runtime. The installed copy is the
  repository content at that ref; there is no build or packing step.
- Never mirror a paid Skill into `lovstudio/skills/skills/`, and do not add
  `encrypted_bundle` or `public_source` (the catalog validator rejects them).
- `POST https://lovstudio.ai/api/skills/download` returns a short-lived archive
  URL only to accounts that own the Skill (Credits redemption or a license bound
  to the account); `npx lovstudio skills add <name>` installs it as plain files.

## License entitlement contract

- `global` and `all` mean a dynamic license scope: while the license is active,
  they include every Skill that is currently listed in the canonical catalog.
- A new Skill becomes available to existing global licenses during catalog sync;
  no per-license grant row, Credits balance, or repurchase is required.
- A delisted Skill leaves the dynamic global scope. Explicit historical
  per-Skill purchases remain fixed unless their own license is revoked.
- Never implement `global` by materializing the current catalog into a fixed
  list of Skill IDs. Catalog sync must maintain the listed/delisted state that
  the entitlement resolver reads.
- Publication verification for a new paid Skill must cover three paths: a
  dynamic global license installs without Credits, an explicit owner installs
  without duplicate Credits, and an unentitled account reaches the purchase
  confirmation before source download.

## Catalog registration

Use the unified `lovstudio/skills` catalog; the former split General and Dev
catalogs are archived. Choose the entry category from product policy, not source
location. Transform the current Pricing Card's public fields into the catalog
manifest; do not independently invent or revise a price in this adapter. Add the
repository, version, category, description, and paid status, then run the
catalog's official mirror/render/validation scripts. Merge the catalog change
into its `main` branch before live revalidation.

For a paid Skill, add only metadata: `repo`, `version`, `skill_path` when needed,
and the pricing block. Paid entries never get a `skills/<name>/` mirror.

For generated aggregate catalogs, update metadata and run their official sync
and render scripts. Do not hand-edit generated mirror directories.

## Revalidate

Replace `NAME` and the site URL with configured values:

```bash
test -n "$LOVSTUDIO_REVALIDATE_SECRET"

curl -fsS -X POST "SITE_URL/api/revalidate" \
  -H "x-revalidate-secret: $LOVSTUDIO_REVALIDATE_SECRET" \
  -H "content-type: application/json" \
  -d '{
    "tags":[
      "skills-index",
      "skills-index:lovstudio",
      "skills-updates",
      "skill:NAME",
      "skill-cases:NAME"
    ],
    "paths":["/skills","/skills/NAME","/agent"]
  }'
```

## Verify the visible result

```bash
curl -fsS -o /tmp/lov-skill-page.html \
  -w '%{http_code}\n' "SITE_URL/skills/NAME"
rg -n 'Version|EXPECTED_VERSION|EXPECTED_MARKER' \
  /tmp/lov-skill-page.html
```

Completion requires the intended catalog to list the Skill, the detail page to
return HTTP 200, the visible version plus marker to match the release, and the
exact catalog install command to pass from a clean isolated directory. For a paid
Skill, verify with an account that already owns it: the install must download the
tagged source and put plain files on disk without a duplicate purchase.

### Install verification must not touch the maintainer's install root

`npx lovstudio skills add <name>` installs **globally** by default and writes a real
copy into `~/.agents/skills/<name>/`. On a maintainer machine that path is often a
symlink into the development checkout, so a default install silently replaces the
symlink (and any dependency it pulls) with a copy of the released version.

Verify with the project-local mode from a throwaway directory instead:

```bash
tmp=$(mktemp -d /tmp/skill-install-XXXX) && cd "$tmp" \
  && npx -y lovstudio skills add NAME --project \
  && grep -m1 'version' "./.agents/skills/lov-NAME/skill.yaml"
```

Then confirm the delivered payload, not just the exit code: the version matches the
release, a release-specific file exists, and the skill's own CLI or script starts.
If the receipt shows `→ ~/.agents/skills/...`, stop and restore the previous state
from a backup before continuing.
