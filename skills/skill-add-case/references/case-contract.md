# Case contract

`scripts/add_case.py` accepts one JSON object. The target's canonical
`cases/cases.json` remains a JSON array.

## Required public fields

```json
{
  "id": "stable-kebab-case-id",
  "type": "case",
  "title": "Short result-led title",
  "description": "What was needed, what changed, and why it mattered.",
  "input": {"items": ["Real, public-safe starting artifact or state"]},
  "prompt": "The minimum real prompt or brief.",
  "output": {"items": ["Real result or reviewable artifact"]},
  "session": {
    "url": "https://lovstudio.ai/yoda/session/yss_<43-char-token>?detail=concise",
    "access": "paid",
    "priceCredits": 140,
    "pricingRule": "ceil(target-skill-price/10)",
    "targetSkill": "lov-target-skill"
  },
  "evidence": {
    "acceptance": "user-confirmed",
    "verified_at": "2026-08-23",
    "method": "How the output was checked",
    "privacy": "What was redacted or why publication is safe",
    "artifact_type": "visual"
  }
}
```

The `session` object is required for every newly added case. Its price and target
must come from the structured `lov-share-session --json` response; they may not
be typed by hand. Optional website fields are `titleEn`, `descriptionEn`, `testimonial`,
`testimonialEn`, `author`, `cover`, `gallery`, and `languageUnits`.

## Evidence rules

- Acceptance must refer to this exact output, not a different run or general
  praise for the Skill.
- `input`, `prompt`, and `output` are factual. Do not turn plans into completed
  results or local validation into production proof.
- Absolute home paths, access tokens, cookies, authorization headers, raw
  transcripts, customer names, and unpublished business data are excluded from
  the public case. The paid transcript is separately normalized and redacted by
  `lov-share-session` before upload.
- Relative image paths must resolve inside the target Skill. HTTPS images must
  be stable and authorized for public display.
- Set `evidence.artifact_type` to `visual` when the accepted result is primarily
  an image, poster, infographic, diagram, slide, or other visual artifact. Such
  a case must include `cover` with the accepted final output. When the result has
  multiple final variants, put the primary artifact in `cover` and the remaining
  accepted outputs in `gallery`; do not substitute process screenshots.
- A relative asset in a paid or private target repository is not public evidence
  unless the website serves it through an authenticated asset proxy. Otherwise
  publish a sanitized copy to the approved public catalog asset location and use
  its stable HTTPS URL.
- The case fingerprint is SHA-256 over canonical UTF-8 JSON. Public verification
  compares the entire case object, not only its title.
- `session.url` must be an HTTPS `lovstudio.ai/yoda/session/yss_*` URL. The public
  case never embeds transcript blocks or an arbitrary client-selected price.
- A paid Session contains text only. Attachments remain disallowed until their
  storage URLs are access-controlled as strictly as the snapshot.

## Duplicate and correction policy

An existing `id` or evidence fingerprint is a duplicate. A correction to the
same case uses `--replace-existing` and preserves the stable ID. A materially new
result receives a new case ID even when the prompt resembles an older example.

## Website completion gate

The following states are distinct:

1. `local` — the canonical local case file and target validator pass.
2. `pushed` — the intended source commit is on the public default branch.
3. `live-verified` — public raw JSON matches the fingerprint, the detail page is
   HTTP 200, every case image is referenced by the rendered page and returns
   non-empty `image/*` content, and the unauthenticated Session URL renders its
   paid paywall with the exact case title and Credits price after cache refresh.

Never report `live-verified` from a local build, a successful push, or a cache
refresh response alone.
