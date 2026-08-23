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
  "evidence": {
    "acceptance": "user-confirmed",
    "verified_at": "2026-08-23",
    "method": "How the output was checked",
    "privacy": "What was redacted or why publication is safe"
  }
}
```

Optional website fields are `titleEn`, `descriptionEn`, `testimonial`,
`testimonialEn`, `author`, `cover`, `gallery`, and `languageUnits`.

## Evidence rules

- Acceptance must refer to this exact output, not a different run or general
  praise for the Skill.
- `input`, `prompt`, and `output` are factual. Do not turn plans into completed
  results or local validation into production proof.
- Absolute home paths, access tokens, cookies, authorization headers, raw
  transcripts, customer names, and unpublished business data are excluded.
- Relative image paths must resolve inside the target Skill. HTTPS images must
  be stable and authorized for public display.
- The case fingerprint is SHA-256 over canonical UTF-8 JSON. Public verification
  compares the entire case object, not only its title.

## Duplicate and correction policy

An existing `id` or evidence fingerprint is a duplicate. A correction to the
same case uses `--replace-existing` and preserves the stable ID. A materially new
result receives a new case ID even when the prompt resembles an older example.

## Website completion gate

The following states are distinct:

1. `local` — the canonical local case file and target validator pass.
2. `pushed` — the intended source commit is on the public default branch.
3. `live-verified` — public raw JSON matches the fingerprint, the detail page is
   HTTP 200, and the case title is visible after cache refresh.

Never report `live-verified` from a local build, a successful push, or a cache
refresh response alone.
