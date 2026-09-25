# GitHub, Website, Downloads, and Documentation

Read this reference when source publication, GitHub Release, a production
website, public downloads, or release documentation is in scope.

## Changelog and documentation

- Add a dated heading for the exact version.
- Group observable features, fixes, performance, documentation, and distribution
  changes; omit empty groups and internal-only maintenance.
- Update README current version, supported systems, official download/store
  state, changelog link, and detailed release note link.
- Update architecture/status documents only where the shipped behavior changed.
- Update visible website version labels, versioned filenames, structured data,
  and tests that assert download destinations.
- Do not say “available” for a store version that is processing or under review.

## Release commit and tag

Before the release commit:

```bash
git diff --check
git status --short --branch
git rev-list --left-right --count origin/main...main
```

Stage only intended release changes. Create the repository's conventional
release commit, then an annotated tag whose message is the exact changelog
section:

```bash
git commit -m "chore: release v$VERSION"
git tag -a "v$VERSION" -F "$RELEASE_NOTES_FILE"
git push origin main
git push origin "v$VERSION"
```

Verify the tag is annotated with `git cat-file -t` and remote main equals the
release commit.

## GitHub Release

Use notes from the changelog rather than unrelated auto-generated text:

```bash
if gh release view "v$VERSION" >/dev/null 2>&1; then
  gh release edit "v$VERSION" --title "$RELEASE_TITLE" \
    --notes-file "$RELEASE_NOTES_FILE"
else
  gh release create "v$VERSION" $ARTIFACTS --title "$RELEASE_TITLE" \
    --notes-file "$RELEASE_NOTES_FILE" --verify-tag
fi
```

Upload only final signed artifacts and checksum files. Query the Release and
verify asset names, sizes, upload states, and platform-provided digests.

## Production website

Use the repository's existing provider and linked project. Examples include:

```bash
vercel --version
vercel --yes --prod
```

Do not migrate frameworks, runtime, DNS, or providers as part of a routine app
release. When a provider CLI reports a newer compatible version, upgrade it
only when it directly supports the current deployment and then record the
version used.

Confirm the production deployment ID, ready state, target, generated URL, and
custom-domain alias. A provider upload or build log alone is insufficient.

## Public verification

Verify from the public custom domain:

```bash
curl -fsSIL "$PUBLIC_SITE"
curl -fsSIL "$PUBLIC_ARTIFACT_URL"
curl -fsSL "$PUBLIC_ARTIFACT_URL" -o "$TEMP_ARTIFACT"
shasum -a 256 "$TEMP_ARTIFACT"
```

Also fetch the rendered HTML and referenced JavaScript when needed to prove the
new version/download path is actually live. Confirm:

- HTTP success and expected content type;
- content length and immutable/versioned filename;
- remote SHA-256 equals the locally signed artifact;
- canonical/SEO metadata still points at the production domain;
- the previous download link is not the active page destination.

## Final Git hygiene

- Main branch and remote main resolve to the same release commit.
- Worktree is clean except explicitly preserved user files.
- The tag, GitHub Release, production deployment, and public artifacts all map
  to the same marketing version.
- Report public URLs and identifiers, not only local output paths.
