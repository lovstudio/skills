# Publishing to Skill Publisher

This adapter turns validated local source into a GitHub-backed Skill Publisher release,
catalog entry, and verified live detail page.

## Inputs

- Local Skill source path.
- GitHub organization and desired repository visibility.
- Free/paid catalog status and existing catalog category.
- General or Dev catalog checkout.
- Expected version and a release-specific visible marker.
- Revalidation secret resolved from environment without printing it.

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

## Catalog registration

Choose the catalog from Skill category and product policy, not from source
location. Add the repository, version, category, description, and paid status to
the catalog manifest and human README. Merge the catalog change into its `main`
branch before live revalidation.

For generated aggregate catalogs, update metadata and run their official sync
and render scripts. Do not hand-edit generated mirror directories.

## Revalidate

Replace `CATALOG`, `NAME`, and the site URL with configured values:

```bash
test -n "$SKILL_REVALIDATE_SECRET"

curl -fsS -X POST "SITE_URL/api/revalidate" \
  -H "x-revalidate-secret: $SKILL_REVALIDATE_SECRET" \
  -H "content-type: application/json" \
  -d '{
    "tags":[
      "skills-index",
      "skills-index:CATALOG",
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
return HTTP 200, and the visible version plus marker to match the release.
