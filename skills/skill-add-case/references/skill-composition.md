# Skill composition

## Nearby Skills Inspected

- `lov-skill-add-case` owns accepted-result qualification, public text and image
  packaging, exact-content consent, API submission and live readback.
- The website `GET /api/skills/<id>/cases` supplies the active contract. Its
  authenticated POST owns source selection, Session ownership checks, image and
  JSON persistence, concurrency, idempotency and cache refresh.
- `lov-share-session` is the shared-auth dependency. The client imports its cache,
  refresh and device-login functions without invoking transcript discovery or
  upload. Offline preparation does not resolve this dependency or authenticate.
- `lov-branding-consistency` reviews authored titles, summaries and instructions;
  it does not rewrite original prompts or evidence.
- Manual handoff ends with the submission file and verified form URL. The user
  owns login and publication in the editor. Agent handoff proceeds through account
  login, dry-run, exact-content consent and POST.

## Atomic Handoffs

For the website route, this Skill hands public JSON to the user or authenticated
API, then receives a source commit and URL for independent readback. No source
checkout or publisher handoff is required.

Only an explicitly requested maintainer update uses `add_case_with_session.py`,
composed transcript upload through `lov-share-session`, local registry mutation
and a case-only `lov-skill-publisher` handoff. Its paid contract and required
GitHub permissions remain separate from ordinary website contribution.

`lov-skill-creator` may supply the existing local Skill. `lov-skill-pricing` is not
part of case submission: clients never choose a price. `lov-skill-optimizer`
maintains the Skill itself, not individual case records.

## Overlap Decisions

This Skill owns the accepted-case outcome. Share Session owns authentication and
transcript upload; Publisher owns explicit maintainer publication. Reuse shared
auth without coupling ordinary case submission to transcript upload.

## Composition Decision

The API confirms the source commit, not rendering. This Skill owns final public
readback of source JSON, parent and case pages, images and optional Session access.
Missing source visibility is partial verification, never a reason to export
repository credentials.
