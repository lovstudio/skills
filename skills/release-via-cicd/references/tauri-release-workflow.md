# Tauri Release Workflow Reference

Use this reference when creating or repairing `.github/workflows/release.yml`
for Tauri projects.

## Required Shape

- Create one draft release first, build all platform assets into that draft, then publish the draft only after all required build jobs pass.
- Dispatch regional mirrors only after publishing. Run mirror synchronization in a separate, independently retryable post-CI workflow so it cannot block platform builds or the public Release.
- Do not rely on workflow success alone. After publishing, download release assets and verify macOS signing/notarization locally.
- Do not add unsigned macOS `xattr` notes when Developer ID signing and notarization are configured.
- Windows fallback is allowed: if WiX MSI or NSIS hangs/fails, build the executable with `tauri build --no-bundle` and upload a zip.

## Apple Signing Preflight

Check local signing identity:

```bash
security find-identity -v -p codesigning | grep "Developer ID Application" || true
```

Check GitHub secrets without printing values:

```bash
for name in \
  APPLE_CERTIFICATE \
  APPLE_CERTIFICATE_PASSWORD \
  APPLE_SIGNING_IDENTITY \
  APPLE_ID \
  APPLE_PASSWORD \
  APPLE_TEAM_ID
do
  gh secret list | awk '{print $1}' | grep -qx "$name" \
    && echo "ok $name" \
    || echo "missing $name"
done
```

`APPLE_PASSWORD` must be an Apple app-specific password. If the local variable is named `APPLE_SPECIFIC_APP_PASSWORD`, store it in GitHub as `APPLE_PASSWORD`.

The p12 used for `APPLE_CERTIFICATE` must contain the Developer ID identity only. If a p12 contains both `Apple Development` and `Developer ID Application`, Tauri can pick the wrong certificate and fail with an identity mismatch.

Developer ID-only export pattern:

```bash
TMP_DIR=$(mktemp -d)
TMP_KEYCHAIN="$TMP_DIR/developer-id.keychain-db"
trap 'security delete-keychain "$TMP_KEYCHAIN" 2>/dev/null || true; rm -rf "$TMP_DIR"' EXIT

security create-keychain -p "$KEYCHAIN_PASSWORD" "$TMP_KEYCHAIN"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$TMP_KEYCHAIN"
security import all-identities.p12 \
  -k "$TMP_KEYCHAIN" \
  -P "$APPLE_CERTIFICATE_PASSWORD" \
  -T /usr/bin/codesign \
  -T /usr/bin/security

security find-certificate -a -c "Apple Development" -Z "$TMP_KEYCHAIN" \
  | awk '/SHA-1 hash:/ {print $3}' \
  | while read -r sha; do
      security delete-certificate -Z "$sha" "$TMP_KEYCHAIN"
    done

security export \
  -k "$TMP_KEYCHAIN" \
  -t identities \
  -f pkcs12 \
  -P "$APPLE_CERTIFICATE_PASSWORD" \
  -o "$TMP_DIR/developer-id-only.p12"

base64 -i "$TMP_DIR/developer-id-only.p12" -o "$TMP_DIR/developer-id-only.p12.base64"
gh secret set APPLE_CERTIFICATE < "$TMP_DIR/developer-id-only.p12.base64"
```

Set the remaining secrets without echoing values:

```bash
gh secret set APPLE_CERTIFICATE_PASSWORD --body "$APPLE_CERTIFICATE_PASSWORD"
gh secret set APPLE_SIGNING_IDENTITY --body "$APPLE_SIGNING_IDENTITY"
gh secret set APPLE_ID --body "$APPLE_ID"
gh secret set APPLE_PASSWORD --body "$APPLE_SPECIFIC_APP_PASSWORD"
gh secret set APPLE_TEAM_ID --body "$APPLE_TEAM_ID"
```

## Release Notes Output

Use a helper that writes valid `$GITHUB_OUTPUT` blocks. Avoid shell variables that contain hand-indented markdown blocks inside YAML because they often produce `unexpected EOF` when copied or reindented.

```bash
append_output_block() {
  local name="$1"
  local delimiter="EOF_${name}_$(date +%s)"
  {
    printf '%s<<%s\n' "$name" "$delimiter"
    cat
    printf '%s\n' "$delimiter"
  } >> "$GITHUB_OUTPUT"
}
```

Unsigned warning is conditional:

```bash
if [ "$HAS_APPLE_SIGNING" != "true" ]; then
  {
    printf '\n---\n\n'
    printf '**macOS 用户注意**: 本应用暂未签名，首次运行需授权：\n\n'
    printf '```bash\n'
    printf 'sudo xattr -dr com.apple.quarantine /Applications/%s.app\n' "$APP_NAME"
    printf '```\n'
  } >> notes.md
fi
```

## Workflow Template

```yaml
name: Release
on:
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag (e.g. v0.1.0)'
        required: true

permissions:
  contents: write

jobs:
  create-release:
    runs-on: ubuntu-latest
    outputs:
      release_id: ${{ steps.create.outputs.id }}
      tag: ${{ github.event.inputs.tag }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.tag }}

      - name: Extract release notes
        id: notes
        shell: bash
        env:
          APP_NAME: ${{ github.event.repository.name }}
          HAS_APPLE_SIGNING: ${{ secrets.APPLE_CERTIFICATE != '' && secrets.APPLE_CERTIFICATE_PASSWORD != '' && secrets.APPLE_SIGNING_IDENTITY != '' && secrets.APPLE_ID != '' && secrets.APPLE_PASSWORD != '' && secrets.APPLE_TEAM_ID != '' }}
        run: |
          set -euo pipefail
          VERSION="${{ github.event.inputs.tag }}"
          VERSION_NUM="${VERSION#v}"

          awk -v ver="$VERSION_NUM" '
            /^## / { if (found) exit; if ($2 == ver) { found=1; next } }
            found { print }
          ' CHANGELOG.md > notes.md || true

          if [ ! -s notes.md ]; then
            printf 'Release %s\n' "$VERSION" > notes.md
          fi

          if [ "$HAS_APPLE_SIGNING" != "true" ]; then
            {
              printf '\n---\n\n'
              printf '**macOS 用户注意**: 本应用暂未签名，首次运行需授权：\n\n'
              printf '```bash\n'
              printf 'sudo xattr -dr com.apple.quarantine /Applications/%s.app\n' "$APP_NAME"
              printf '```\n'
            } >> notes.md
          fi

          delimiter="EOF_notes_$(date +%s)"
          {
            printf 'notes<<%s\n' "$delimiter"
            cat notes.md
            printf '%s\n' "$delimiter"
          } >> "$GITHUB_OUTPUT"

      - id: create
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ github.event.inputs.tag }}
          draft: true
          body: ${{ steps.notes.outputs.notes }}

  build-tauri:
    needs: create-release
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: macos-latest
            label: macos-aarch64
            args: --target aarch64-apple-darwin
          - platform: macos-latest
            label: macos-x86_64
            args: --target x86_64-apple-darwin
          - platform: ubuntu-22.04
            label: linux-x86_64
            args: ''
          - platform: windows-latest
            label: windows-x86_64
            args: ''
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.tag }}

      - name: Detect package manager
        id: pm
        shell: bash
        run: |
          PM=$(node -p "const p=require('./package.json').packageManager||''; p.split('@')[0] || (require('fs').existsSync('bun.lock') || require('fs').existsSync('bun.lockb') ? 'bun' : require('fs').existsSync('pnpm-lock.yaml') ? 'pnpm' : require('fs').existsSync('yarn.lock') ? 'yarn' : 'npm')")
          echo "manager=$PM" >> "$GITHUB_OUTPUT"

      - if: steps.pm.outputs.manager == 'bun'
        uses: oven-sh/setup-bun@v2

      - if: steps.pm.outputs.manager == 'pnpm'
        uses: pnpm/action-setup@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.platform == 'macos-latest' && 'aarch64-apple-darwin,x86_64-apple-darwin' || '' }}

      - if: matrix.platform == 'ubuntu-22.04'
        run: sudo apt-get update && sudo apt-get install -y libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf

      - uses: swatinem/rust-cache@v2
        with:
          workspaces: './src-tauri -> target'

      - name: Install dependencies
        shell: bash
        run: |
          case "${{ steps.pm.outputs.manager }}" in
            bun) bun install --frozen-lockfile ;;
            pnpm) pnpm install --frozen-lockfile ;;
            yarn) yarn install --frozen-lockfile ;;
            npm) npm ci ;;
            *) echo "Unknown package manager" >&2; exit 1 ;;
          esac

      - name: Build Tauri bundles
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          APPLE_CERTIFICATE: ${{ matrix.platform == 'macos-latest' && secrets.APPLE_CERTIFICATE || '' }}
          APPLE_CERTIFICATE_PASSWORD: ${{ matrix.platform == 'macos-latest' && secrets.APPLE_CERTIFICATE_PASSWORD || '' }}
          APPLE_SIGNING_IDENTITY: ${{ matrix.platform == 'macos-latest' && secrets.APPLE_SIGNING_IDENTITY || '' }}
          APPLE_ID: ${{ matrix.platform == 'macos-latest' && secrets.APPLE_ID || '' }}
          APPLE_PASSWORD: ${{ matrix.platform == 'macos-latest' && secrets.APPLE_PASSWORD || '' }}
          APPLE_TEAM_ID: ${{ matrix.platform == 'macos-latest' && secrets.APPLE_TEAM_ID || '' }}
        with:
          releaseId: ${{ needs.create-release.outputs.release_id }}
          args: ${{ matrix.args }}

  windows-zip-fallback:
    needs: create-release
    runs-on: windows-latest
    if: false
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.tag }}
      - uses: oven-sh/setup-bun@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - uses: dtolnay/rust-toolchain@stable
      - name: Build exe without bundle
        shell: pwsh
        run: |
          bun install --frozen-lockfile
          bun tauri build --no-bundle
          $tag = "${{ github.event.inputs.tag }}"
          $project = "${{ github.event.repository.name }}"
          $exe = Get-ChildItem "src-tauri\target\release" -Filter "*.exe" | Select-Object -First 1
          if (-not $exe) { throw "No exe found" }
          $zip = "$project-$tag-windows-x64.zip"
          Compress-Archive -Path $exe.FullName -DestinationPath $zip -Force
          gh release upload $tag $zip --repo ${{ github.repository }} --clobber
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  publish-release:
    needs: [create-release, build-tauri]
    runs-on: ubuntu-latest
    permissions:
      actions: write
      contents: write
    steps:
      - name: Publish release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release edit "${{ needs.create-release.outputs.tag }}" \
            --repo "${{ github.repository }}" \
            --draft=false

      - name: Dispatch regional mirror post-CI
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          tag="${{ needs.create-release.outputs.tag }}"
          if ! gh workflow run release-mirror.yml --repo "${{ github.repository }}" -f tag="$tag"; then
            echo "::warning::Mirror dispatch failed; the canonical release remains successful."
          fi
```

`windows-zip-fallback` is intentionally disabled in the template. Enable it only after a real WiX/NSIS failure, and then make `publish-release.needs` depend on the fallback job instead of the failed bundling job.

When a mirror is configured, create the separately dispatched workflow from `references/general-release-playbooks.md`. Make it download canonical assets by tag instead of reusing build-job files.

## Failed Draft Recovery

For a failed workflow that created a draft release:

```bash
gh release delete vX.Y.Z --yes
gh workflow run release.yml -f tag=vX.Y.Z
```

Do not add `--cleanup-tag` unless the task is explicitly to delete the tag. If the tag must move before the release was published, force-push only for a just-created failed tag; otherwise bump patch and publish a new version.

## Verification

Workflow success is not enough. Download the macOS asset and verify:

```bash
codesign -dv --verbose=4 "/Applications/App Name.app" 2>&1 | grep -E 'Authority=Developer ID Application|TeamIdentifier'
codesign --verify --deep --strict --verbose=2 "/Applications/App Name.app"
spctl -a -vv -t exec "/Applications/App Name.app"
```

Expected output includes:

- `Authority=Developer ID Application`
- `TeamIdentifier=<team id>`
- `Notarization Ticket=stapled`
- `source=Notarized Developer ID`
