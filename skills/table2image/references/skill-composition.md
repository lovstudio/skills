# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Actual contract and decision |
| --- | --- | --- |
| `lov-table2image` | core atom | Owns Markdown table plus optional Mable layout to hosted PNG URL, with optional verified local download. |
| `lov-gen-card` | not composed | Produces an editorial DOM card and high-resolution PNG from structured card content plus a visual; it does not accept a table-to-URL contract. |
| `lov-professional-infographic` | not composed | Produces evidence-led consulting Exhibits with claims, sources and recommendations; a plain table image should not inherit that editorial workflow. |
| `lov-image-creator` | not composed | Owns AI image generation, general code-rendered posters and prompt engineering, not deterministic Mable table rendering. |
| `baoyu-markdown-to-html` | optional upstream atom | Can convert a broader Markdown document to styled HTML, but the core Skill consumes the original Markdown table directly. |
| `lov-rich-export` | optional downstream atom | Can package a finished PNG or URL into broader HTML, DOCX or PDF delivery; it does not own table rendering. |

## Atomic Handoffs

| Stage | Owner | Input artifact | Output artifact | Acceptance boundary |
| --- | --- | --- | --- | --- |
| Optional upstream authoring | User, editor or data workflow | Standard Markdown table | Approved Markdown table | Text and data are correct before external rendering |
| Core table image | `lov-table2image` | Markdown plus optional model or layout JSON | Hosted PNG URL, metadata and optional local PNG | Required response fields exist; downloaded file passes PNG checks |
| Optional downstream package | Publishing or rich-export workflow | Verified PNG or URL | Article, document or delivery package | Core image remains traceable and unmodified |

The Mable service is an API boundary, not a sibling Skill. It owns layout solving, font adaptation,
rendering and content-addressed persistence. The client owns request validation, transport, local
download verification and user-facing diagnostics.

## Overlap Decisions

The output format overlaps with card, infographic and image-generation Skills, but their acceptance
criteria differ. Extending them would mix general visual authoring with a narrow table API contract.
`lov-table2image` therefore reuses no sibling implementation and exposes PNG or URL artifacts for
optional downstream consumption.

## Composition Decision

This source is a **Single Skill**. Input validation, one API request, response verification and an
optional download are one user-visible outcome. They are not independently useful modules and do
not justify a Skill Kit. The server implementation remains outside the distributed source, while
the local client stays self-contained and uses only the Python standard library.
