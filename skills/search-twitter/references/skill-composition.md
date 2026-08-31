# Skill Group Composition

## Nearby Skills Inspected

- `lov-media-crawler`: turns a known public social link into a local media file.
  It is relevant after an X post is identified, but it does not discover status
  IDs, recover text, or grade source provenance.
- `lov-fact-check`: evaluates whether a claim is supported. It may consume the
  evidence bundle produced here, but it must not replace verbatim recovery with
  a truth verdict.
- `lov-search-chat`: searches local AI conversation memory. It may recover a
  previously seen X URL, but it does not search the public web.
- `lov-search-file`: locates previously delivered local files. It may locate a
  screenshot supplied earlier, but it does not establish that image's origin.
- `lov-ataru-indexing`: maintains local memory indexes and is unrelated to
  public X discovery.
- `baoyu-danger-x-to-markdown`: converts a known live X URL into Markdown. That
  narrow transformation is useful for accessible posts, but it does not own
  multi-source discovery, deleted-post recovery, screenshot evidence, or
  completeness claims.

## Atomic Handoffs

- Optional upstream from `lov-search-chat` or `lov-search-file`: a text file of
  candidate URLs, status IDs, quote fragments, or local screenshot paths.
  Acceptance boundary: each item remains a candidate until independently tied
  to a source URL or evidence record.
- Core owned here: candidate inventory, live/archive extraction, screenshot
  manifest, provenance grading, verbatim report, and unrecovered ledger.
- Optional downstream to `lov-media-crawler`: a confirmed X URL whose attached
  media the user may save. Acceptance boundary: this Skill retains the post-text
  evidence record; the downstream Skill returns a verified media file.
- Optional downstream to `lov-fact-check`: an evidence bundle plus the exact
  claim to evaluate. Acceptance boundary: the fact-check result is commentary,
  not a replacement for the original-text record.

## Overlap Decisions

Known-URL conversion is deliberately kept as a small overlap because recovery
must compare two renderers and archives under one evidence model. Media download,
general truth assessment, local-memory search, and publication stay separate.
No sibling Skill is a runtime dependency; handoffs use URLs, JSON, JSONL,
Markdown, or image files.

## Composition Decision

This source is a Single Skill. Discovery, extraction, screenshot registration,
and evidence reconciliation share one candidate inventory and one acceptance
boundary: a defensible verbatim X/Twitter compilation. Splitting those stages
into user-facing child Skills would expose implementation choices and make it
easier to lose provenance between stages.
