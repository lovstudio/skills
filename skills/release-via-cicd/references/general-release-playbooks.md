# General Release Playbooks

Use this file for non-Tauri templates and operational checklists. Keep the main
`SKILL.md` focused on decision rules.

## Shell Project Workflow

```yaml
name: Release
on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag (e.g. v1.0.0)'
        required: true
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Get tag
        id: tag
        run: echo "tag=${{ github.event.inputs.tag || github.ref_name }}" >> "$GITHUB_OUTPUT"
      - name: Extract release notes
        id: notes
        run: |
          VERSION="${{ steps.tag.outputs.tag }}"
          VERSION_NUM="${VERSION#v}"
          if [ -f CHANGELOG.md ]; then
            NOTES=$(awk -v ver="$VERSION_NUM" '
              /^## / { if (found) exit; if ($2 == ver) { found=1; next } }
              found { print }
            ' CHANGELOG.md)
          fi
          if [ -z "$NOTES" ]; then NOTES="Release $VERSION"; fi
          {
            echo 'notes<<EOF'
            echo "$NOTES"
            echo 'EOF'
          } >> "$GITHUB_OUTPUT"
      - uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.tag.outputs.tag }}
          body: ${{ steps.notes.outputs.notes }}
          files: |
            *.sh
```

## Vite Frontend Workflow

Use package-manager detection from the main skill. The artifact name must be
`{project}-{tag}.zip`.

```yaml
name: Release
on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag (e.g. v1.0.0)'
        required: true
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.tag || github.ref_name }}
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - name: Package dist
        run: |
          TAG="${{ github.event.inputs.tag || github.ref_name }}"
          zip -r "${PROJECT_NAME}-${TAG}.zip" dist
        env:
          PROJECT_NAME: myproject
      - name: Get tag
        id: tag
        run: echo "tag=${{ github.event.inputs.tag || github.ref_name }}" >> "$GITHUB_OUTPUT"
      - name: Extract release notes
        id: notes
        run: |
          VERSION="${{ steps.tag.outputs.tag }}"
          VERSION_NUM="${VERSION#v}"
          if [ -f CHANGELOG.md ]; then
            NOTES=$(awk -v ver="$VERSION_NUM" '
              /^## / { if (found) exit; if ($2 == ver) { found=1; next } }
              found { print }
            ' CHANGELOG.md)
          fi
          if [ -z "$NOTES" ]; then NOTES="Release $VERSION"; fi
          {
            echo 'notes<<EOF'
            echo "$NOTES"
            echo 'EOF'
          } >> "$GITHUB_OUTPUT"
      - uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.tag.outputs.tag }}
          body: ${{ steps.notes.outputs.notes }}
          files: ${{ env.PROJECT_NAME }}-${{ steps.tag.outputs.tag }}.zip
        env:
          PROJECT_NAME: myproject
```

## Monorepo Changesets Workflow

```yaml
name: Release
on:
  push:
    branches: [main]
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
          registry-url: 'https://registry.npmjs.org'
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - run: echo "//registry.npmjs.org/:_authToken=${{ secrets.NPM_TOKEN }}" >> ~/.npmrc
      - uses: changesets/action@v1
        id: changesets
        with:
          version: pnpm changeset version
          publish: pnpm release
          title: 'chore: release packages'
          commit: 'chore: release packages'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
      - name: Pack npm packages
        if: steps.changesets.outputs.published == 'true'
        run: |
          mkdir -p release-assets
          for pkg in packages/*/; do
            if [ -f "$pkg/package.json" ]; then
              cd "$pkg"
              npm pack --pack-destination ../../release-assets
              cd ../..
            fi
          done
      - name: Create GitHub Release
        if: steps.changesets.outputs.published == 'true'
        run: |
          VERSION=$(node -p "require('./packages/core/package.json').version")
          NOTES=$(awk -v ver="$VERSION" '
            /^## / { if (found) exit; if ($2 == ver) { found=1; next } }
            found { print }
          ' packages/core/CHANGELOG.md)
          gh release create "v${VERSION}" \
            --title "v${VERSION}" \
            --notes "${NOTES:-Release v${VERSION}}" \
            --latest \
            release-assets/*.tgz
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Workflow Monitor

Always wait for workflow completion. `gh run view` can fail with transient API
EOF; retry before treating the run as unknown.

```bash
RUN_ID=$(gh run list -w release.yml -L 1 --json databaseId -q '.[0].databaseId')
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Workflow: https://github.com/$REPO/actions/runs/$RUN_ID"

gh_view_json() {
  local run_id="$1"
  local json="$2"
  local query="$3"
  local attempt=1
  while [ "$attempt" -le 5 ]; do
    if gh run view "$run_id" --json "$json" -q "$query"; then
      return 0
    fi
    sleep $((attempt * 2))
    attempt=$((attempt + 1))
  done
  return 1
}

DELAY=5
MAX_DELAY=60
while true; do
  STATUS=$(gh_view_json "$RUN_ID" status '.status') || {
    echo "GitHub API still unavailable; next poll in ${DELAY}s..."
    sleep "$DELAY"
    DELAY=$((DELAY * 2 > MAX_DELAY ? MAX_DELAY : DELAY * 2))
    continue
  }
  if [ "$STATUS" = "completed" ]; then
    CONCLUSION=$(gh_view_json "$RUN_ID" conclusion '.conclusion' || echo "unknown")
    echo "Workflow $CONCLUSION"
    [ "$CONCLUSION" = "success" ] || gh_view_json "$RUN_ID" jobs '.jobs[] | select(.conclusion != "success") | "  \(.name): \(.conclusion)"' || true
    break
  fi
  sleep "$DELAY"
  DELAY=$((DELAY * 2 > MAX_DELAY ? MAX_DELAY : DELAY * 2))
done
```

## Post-release Mirror Separation

Treat regional and community mirrors as derived distribution surfaces. Keep them outside the primary release DAG:

```text
draft release -> build/sign/notarize -> upload canonical assets -> publish release
                                                               -> dispatch mirror workflow
```

Never upload a mirror from platform build jobs and never make `publish-release` depend on mirror completion. Dispatch a separate workflow after the canonical release becomes public:

```yaml
permissions:
  actions: write
  contents: write

jobs:
  publish-release:
    steps:
      - name: Publish release
        env:
          GH_TOKEN: ${{ github.token }}
        run: gh release edit "$RELEASE_TAG" -R "$GITHUB_REPOSITORY" --draft=false --latest

      - name: Dispatch regional mirror post-CI
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          if ! gh workflow run release-mirror.yml -R "$GITHUB_REPOSITORY" -f tag="$RELEASE_TAG"; then
            echo "::warning::Mirror dispatch failed; the canonical release remains successful."
          fi
```

Make the mirror workflow manually retryable and source every file from the immutable published tag:

```yaml
name: Release Post-CI (Mirror)
on:
  workflow_dispatch:
    inputs:
      tag:
        required: true
permissions:
  contents: read
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.tag }}
      - name: Download canonical assets
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          mkdir -p release
          gh release download "${{ inputs.tag }}" -R "$GITHUB_REPOSITORY" --dir release --clobber
      - name: Upload mirror
        run: ./scripts/upload-mirror.sh release
```

For large multi-platform releases, fan the post-CI workflow out by platform. Download and upload only that platform's assets in each job, set `fail-fast: false`, and keep mirror retries independent from the canonical release.

Wait for and verify the canonical workflow first. Monitor the mirror workflow separately; report its failure without redefining the already-published canonical Release as failed.

## README And Vercel Audits

After workflow success, compare the released version with README versions:

```bash
NEW_VERSION=$(node -p "require('./package.json').version" 2>/dev/null \
  || git tag -l 'v*' | sort -V | tail -1 | sed 's/^v//')
README_LATEST=$(grep -oE 'v?[0-9]+\.[0-9]+\.[0-9]+' README.md 2>/dev/null \
  | sed 's/^v//' | sort -V | tail -1)
test -z "$README_LATEST" || test "$README_LATEST" = "$NEW_VERSION" || echo "README stale"
```

For Vercel projects, check `.vercel/` after push, wait briefly for Git
Integration, and run `vercel --prod` only if no fresh deployment appears.

## Failure Recovery Notes

| Trap | Recovery |
|------|----------|
| Tag pushed but build does not trigger | Use `gh workflow run release.yml -f tag=vX.Y.Z` |
| Draft release left by failed run | `gh release delete vX.Y.Z --yes`, then rerun |
| Need to delete tag too | Add `--cleanup-tag` only when explicitly deleting the tag |
| Release notes show `%0A` or shell EOF | Use `$GITHUB_OUTPUT` block writes, not fragile multiline shell assignments |
| Release notes are blank or commit-only | Maintain `CHANGELOG.md`; do not use `generate_release_notes` |
| Bun project changed to pnpm | Preserve `packageManager`; use `oven-sh/setup-bun@v2` |
| User edits during workflow | Keep release tied to tag commit; new dirty work goes to next version |
| macOS asset might be unsigned | Download and verify with `codesign` and `spctl` |

## Branch And Issue Automation

Recognize issue numbers from `issue-123`, `123-feature`, and
`feature/issue-123`. After a successful release, comment with the release URL
and close only if the issue is still open.
