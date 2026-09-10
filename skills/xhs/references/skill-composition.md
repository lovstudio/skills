# Skill Group Composition

This record explains why `lov-xhs` remains a Single Skill after adopting a
default research-report mode.

## Core atom

`lov-xhs` owns one user-visible result: **turn a Xiaohongshu topic request into a
source-backed research report, while retaining an explicit search-only mode for
JSON discovery**.

The same evidence pipeline supports both modes:

1. `xhs_search.py` discovers notes and returns normalized rows.
2. `xhs_collect.py` reads selected note bodies and exports an auditable corpus.
3. The agent synthesizes the corpus into a report with source links, explicit
   uncertainty, and a clear answer to the operator's actual question.

## Nearby Skills Inspected

- `lov-media-crawler`: consumes a selected note URL and downloads media. It
  does not discover or synthesize topic research, so it remains an optional
  downstream handoff.
- `lov-media-publisher`: publishes to WeChat Channels or Bilibili. It is not a
  Xiaohongshu research capability and is excluded from this workflow.
- `deep-research`: handles multi-source, non-Xiaohongshu, or cross-platform
  research. It may consume the local evidence corpus, but it is not a hidden
  dependency for a Xiaohongshu-only report.
- `lov-search-twitter`, `lov-search-chat`, `lov-search-file`, and `lov-wxmp-cli`
  use different data sources and evidence chains. They cannot substitute for
  Xiaohongshu discovery.
- `lov-create-media-script`: downstream content creation. It does not own
  Xiaohongshu evidence collection or report synthesis.

## Atomic handoffs

- Upstream CLI: `xiaohongshu-cli` owns login, signing, search, and note reads.
- Core evidence: `xhs_search.py` and `xhs_collect.py` own deterministic
  discovery and note-body collection.
- Core report: `lov-xhs` owns the default source-backed report contract.
- Downstream handoff: `lov-media-crawler` receives one explicitly selected note
  URL when the operator asks to download media.
- Excluded publishing: `lov-media-publisher` does not receive the report.

## Overlap decisions

There is no second local Skill that owns “Xiaohongshu topic → evidence corpus →
report”. `deep-research` starts from general web evidence, while `lov-xhs`
starts from authenticated Xiaohongshu discovery and note bodies. The report
mode therefore belongs to `lov-xhs`; it is not an accidental duplicate of
generic research.

## Composition decision

Single Skill. Report generation and search-only export share one evidence
boundary and one delivery surface. Splitting them would create a hidden
dependency between the search atom and the report atom without adding an
independently triable user result.
