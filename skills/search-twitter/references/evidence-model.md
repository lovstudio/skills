# X/Twitter Evidence Model

Use one primary tier per candidate and keep every supporting source as an
additional evidence item.

## Provenance tiers

1. `live_original` — text is visible at the original X/Twitter status URL or
   returned for that exact ID by a live public renderer.
2. `archived_original` — an archive payload for the exact original status URL
   contains recoverable post text.
3. `embedded_card` — another page preserves an X embed tied to the handle or
   status ID; the card may be truncated.
4. `screenshot_copy` — a retained image visibly represents a post, with source
   page, capture time, and SHA-256 recorded.
5. `media_quote` — a third-party page quotes exact words but does not preserve
   the full original object.
6. `media_paraphrase` — a source describes the post without a verifiable exact
   quotation.
7. `unrecovered` — a URL/ID or claim exists, but no recoverable text evidence was
   found. A blank archive shell belongs here.

## Confidence labels

- `two-renderer-match`: two public renderers return equivalent text after only
  URL expansion and whitespace normalization.
- `single-source`: one source yields text and no contradictory variant is found.
- `partial`: the evidence visibly truncates or only quotes part of the post.
- `conflict`: sources tied to the same ID disagree beyond URL/whitespace changes.
- `unrecovered`: no source contains recoverable text.

Confidence does not upgrade provenance. Two copies of the same embed remain an
embedded card, and OCR of a screenshot remains derived evidence.

## Required fields

Each candidate record should contain:

- handle and status ID, or `identity_unresolved`;
- canonical original URL when derivable;
- source URL and retrieval time;
- primary provenance and confidence;
- exact text variants with extractor/source labels;
- screenshot SHA-256 and original/crop relationship when images are used;
- visible truncation, translation, OCR ambiguity, and access-limit notes.

## Claim rules

- “Original text” requires `live_original` or `archived_original` evidence.
- A complete visible `embedded_card` may be transcribed as “embedded-card text”,
  not silently relabelled as a live original.
- `media_quote` can support a quotation only to the visible quoted extent.
- `media_paraphrase` supports topic attribution, not wording.
- “All posts” requires an enumerated account inventory and reconciliation.
  Public search coverage is always described as best effort.
