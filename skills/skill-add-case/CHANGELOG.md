# Changelog

## 0.2.2 - 2026-08-29

- Verify every public `cover` and `gallery` asset returns non-empty image content.
- Require the rendered LovStudio detail page to reference each published case
  image before reporting `live-verified`.

## 0.2.1 - 2026-08-29

- Require every primarily visual accepted case to include its final artifact as
  `cover`, with additional accepted variants in `gallery`.
- Add `evidence.artifact_type` validation so image-producing case workflows fail
  before publication when visual evidence is missing.
- Document public asset hosting for paid or private target repositories.

## 0.2.0 - 2026-08-27

- Add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill.
- Compose `lov-share-session` as a declared dependency for every new case.
- Upload the redacted full conversation as a paid Session priced by the server at
  `ceil(target Skill Credits price / 10)` before mutating the case registry.
- Require structured Session metadata in new cases and verify the unauthenticated
  paywall, title, and Credits price during public readback.
- Keep the case file unchanged when the target Skill is free, unlisted, unpriced,
  or the paid Session upload fails.

## 0.1.0 - 2026-08-23

- Add an explicit user-acceptance gate for case collection.
- Add privacy-safe, duplicate-aware, atomic `cases/cases.json` mutation.
- Add canonical SHA-256 and public raw JSON plus LovStudio page verification.
- Document the optional `lov-skill-publisher` case-only synchronization handoff.
