# npm Publishing Contract

Last fact-checked: 2026-08-22. Recheck the linked primary sources before acting
when npm authentication policy, supported CI providers, or announced dates may
have changed.

## Publish Modes

This Skill treats two authentication paths as first-class and equal:

- **oidc** — GitHub Actions trusted publishing, exchanging the CI's OIDC identity
  for a short-lived credential. Best for GitHub-repository continuous releases.
- **bypass** — a local granular `npm_` token (Bypass-2FA) passed to
  `npm publish` directly. Best for local, CI-less, or new-package publication.

`--auth-mode auto` selects `oidc` when a GitHub repository resolves and `bypass`
otherwise; an explicit `--auth-mode` overrides the inference.

## Trusted Publishing

- npm Trusted Publishing exchanges a CI provider's OIDC identity for a short-lived
  publish credential. It avoids a stored long-lived npm publish token.
- npm's current documentation requires npm CLI 11.5.1+ and Node.js 22.14.0+ for
  trusted publishing. The generated workflow uses Node 24 as the safe default.
- GitHub Actions needs `permissions: id-token: write`; the runner must be
  GitHub-hosted. Self-hosted runners are not currently supported.
- The package's `repository.url` must match the GitHub repository used in the
  trusted publisher binding.
- Trusted publishing authenticates `npm publish` and supported stage operations;
  it does not authenticate unrelated commands or private dependency installation.
- A package currently supports one trusted publisher configuration at a time.

Primary source: [Trusted publishing for npm packages](https://docs.npmjs.com/trusted-publishers/).

## First-Publish Boundary

The target package must already exist before `npm trust` can configure its trusted
publisher. Therefore a brand-new package name needs a one-time authenticated first
publish before later versions can use OIDC.

The `npm trust` management command currently requires npm 11.15.0+, account-level
2FA, write permission on the existing package, and an interactive authentication
method. A Granular Access Token with Bypass 2FA cannot configure trust.

Primary source: [`npm trust` CLI documentation](https://docs.npmjs.com/cli/v11/commands/npm-trust/).

## Token Boundary

Only Granular Access Tokens remain supported. As of August 2026, Bypass-2FA tokens
cannot perform sensitive identity, governance, maintainer, or trusted-publisher
management actions, but they can still publish packages directly — including brand
new names — which makes them the local `bypass` publish credential. GitHub
announced a target of January 2027 for removing direct publish from Bypass-2FA
tokens; this is an announced future target, not a fact to assume unchanged without
rechecking.

Primary sources:

- [About npm access tokens](https://docs.npmjs.com/about-access-tokens/)
- [GitHub changelog: restricting npm bypass-2FA granular access tokens](https://github.blog/changelog/2026-07-31-restricting-npm-bypass-2fa-granular-access-tokens/)

## Acceptance Boundary

Treat these as separate facts:

1. workflow exists locally (oidc) or a publish command resolved (bypass);
2. trusted publisher is registered (oidc) or a granular token is present (bypass);
3. CI accepted the request (oidc) or the local publish completed (bypass);
4. the publish completed (`npm publish` in CI, or the local command);
5. the exact immutable package version is readable from npm;
6. provenance is present when the repository/package combination supports it.

Only step 5 establishes `verified-live`. A root endpoint `404` right after a
successful publish can be CDN lag; re-read the specific version endpoint
(`/<scope>%2f<pkg>/<version>`) before concluding failure.
