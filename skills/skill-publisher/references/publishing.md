# Publishing to Skill Publisher

This adapter turns validated local source into a GitHub-backed Skill Publisher release,
catalog entry, and verified live detail page.

## Inputs

- Local Skill source path.
- GitHub organization and desired repository visibility.
- The current `lov-skill-pricing` Pricing Card, including free/paid status,
  public CNY price or free-entry decision, confidence, and review trigger.
- The intended delivery mode for a paid Skill: protected encrypted bundle or
  explicitly public source.
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

Resolve paid delivery before changing the catalog:

- **Protected delivery:** set `encrypted_bundle: true`; generate and locally
  decrypt the current-version bundle; register its server-side version manifest
  and key; copy the placeholder, `MANIFEST.enc.json`, and ciphertext into the
  catalog mirror. Never print or commit the decryption key.
- **Public-source delivery:** use only when the user explicitly keeps the paid
  Skill's source public. Set `public_source: true`, keep the repository public,
  and let the CLI install from the catalog-declared `repo` after its normal
  account ownership or Credits check. This mode provides no source secrecy and
  must not be described as encrypted protection.

Block publication when `paid: true` has neither a complete encrypted bundle nor
explicit `public_source: true`. A paid card, synced Credits price, or live detail
page is not delivery evidence.

## Catalog registration

Use the unified `lovstudio/skills` catalog; the former split General and Dev
catalogs are archived. Choose the entry category from product policy, not source
location. Transform the current Pricing Card's public fields into the catalog
manifest; do not independently invent or revise a price in this adapter. Add the
repository, version, category, description, and paid status, then run the
catalog's official mirror/render/validation scripts. Merge the catalog change
into its `main` branch before live revalidation.

For a public-source paid Skill, add `public_source: true` and keep it out of the
aggregate plaintext mirror; the CLI installs the declared source repository
directly after entitlement. For a protected paid Skill, add
`encrypted_bundle: true` only after the committed encrypted files and registered
server version are both ready.

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
exact catalog install command to pass from a clean isolated directory. For paid
delivery, verify with an already-owned test account so the run proves source
selection without a duplicate purchase.
