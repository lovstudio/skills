# Changelog

## [0.3.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.2.0] - 2026-08-22

### Added

- add first-class bypass publishing alongside OIDC trusted publishing
- add --auth-mode auto/oidc/bypass; treat local granular NPM_TOKEN (bypass) and GitHub Actions OIDC as equal first-class publish modes; rename lov-npm-auto-publish to lov-npm-publisher and fold in lov-npm-config-oidc

## 0.1.0

- Added registry-aware planning for new and existing npm packages.
- Added conservative GitHub Actions OIDC workflow generation.
- Documented the one-time bootstrap, trusted-publisher, release-gate, and exact
  registry-readback boundaries.
- Added the shared Profile contract, real user case, Skill Card, pricing basis,
  composition record, and explicit distribution states.
