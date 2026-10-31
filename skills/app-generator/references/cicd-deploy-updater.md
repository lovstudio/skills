# CI/CD, Deploy, and Auto Update

Read this reference at Step 7 of the workflow: for every new app, and for upgrades
that add or change workflows, deploy wiring, or the Tauri updater.

## Web-only apps

Default GitHub Actions surface:

- `check.yml`: install, typecheck, lint/build if present.
- Deploy wiring for the selected target: Vercel, Netlify, Cloudflare Pages,
  GitHub Pages, self-hosted static output, or a clearly documented manual
  deploy path.
- Environment variable placeholders only when the app actually needs them.

## Tauri apps

Default GitHub Actions surface:

- `check.yml`: install, typecheck, lint/build if present.
- `release.yml`: Tauri build for target platforms, draft or publish GitHub
  Release, attach artifacts.
- Tauri updater wiring: plugin dependency, updater config, signing key env
  placeholders, and documented release process.
- For Tauri v2, `plugins.updater.pubkey` is required at runtime. Do not leave
  it out even during early scaffolding: a missing `pubkey` causes the app to
  panic during updater plugin initialization. Use a clear placeholder such as
  `PLACEHOLDER_REPLACE_WITH_TAURI_SIGNER_PUBLIC_KEY` until the real public key
  is generated with `pnpm tauri signer generate`.

## Secrets

Do not invent secrets. Use placeholder names and document where the user must
set them:

- `TAURI_SIGNING_PRIVATE_KEY`
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`
- platform signing/notarization secrets as required by the target app
