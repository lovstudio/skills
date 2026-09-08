# Skill composition

## Nearby Skills Inspected

- `lov-skill-add-case` owns accepted-result qualification, public text and image
  packaging, exact-content consent, API submission and live readback.
- The website `GET /api/cases` supplies the active contract. Its
  authenticated POST owns source selection, Session ownership checks, image and
  JSON persistence, concurrency, idempotency and cache refresh.
- The package bundles the MIT LovStudio auth adapter adapted from
  `lov-share-session` 0.4.1, retaining cache and device/refresh contracts. No
  transcript functions are bundled. This avoids an unpublished sibling dependency
  on new installations. Explicit auth overrides remain supported.
- `lov-branding-consistency` reviews authored titles, summaries and instructions;
  it does not rewrite original prompts or evidence.
- Manual handoff ends with the submission file and verified form URL. The user
  owns login and publication in the editor. Agent handoff proceeds through account
  login, dry-run, exact-content consent and POST.

## Atomic Handoffs

For the website route, this Skill hands public JSON to the user or authenticated
API as one record with `case.skillIds`, then receives a source commit and URL for independent readback. No source
checkout or publisher handoff is required.

Only an explicitly requested maintainer update uses `add_case_with_session.py`,
composed transcript upload through `lov-share-session`, local registry mutation
and a case-only `lov-skill-publisher` handoff. Its paid contract and required
GitHub permissions remain separate from ordinary website contribution.

`lov-skill-creator` may supply the existing local Skill. `lov-skill-pricing` is not
part of case submission: clients never choose a price. `lov-skill-optimizer`
maintains the Skill itself, not individual case records.

## Overlap Decisions

This Skill owns the accepted-case outcome and distributes the small login adapter
it needs. Share Session owns transcript upload; Publisher owns explicit maintainer
publication. No transcript implementation is copied into ordinary submission.

## Composition Decision

The API confirms the source commit, not rendering. This Skill owns final public
readback of source JSON, the collection, all related Skill pages and the canonical case page, images and optional Session access.
Missing source visibility is partial verification, never a reason to export
repository credentials.
