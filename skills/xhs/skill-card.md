# Skill Card — lov-xhs

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand how a topic request
becomes a source-backed report without opening the source first.

## Description

`lov-xhs` defaults to a source-backed Xiaohongshu research report. It discovers
notes through `xiaohongshu-cli`, reads selected note bodies, preserves an
auditable JSON corpus, and answers the operator's actual question with
conclusions, an executable plan, evidence links, and uncertainty. Search-only
mode remains available for explicit “search / title filter / export JSON”
requests.

## Owner

Maintained by the repository contributors. The upstream CLI is maintained by
its own project.

## License / Terms

MIT for this Skill source. The upstream `xiaohongshu-cli` is Apache-2.0; keep
its license and notices when redistributing. Source notes remain subject to
their own platform and copyright terms.

## Use Case

Chinese content researchers, independent creators, travel planners, and agent
workflows that need a conclusion from Xiaohongshu material rather than a raw
note dump. A bare topic such as 「冈仁波齐线路规划」 enters report mode by
default; explicit search language enters search-only mode.

## Deployment Geography

Global, on the operator's local machine. Requires network access to Xiaohongshu
and a logged-in local session.

## Requirements

- Python 3.9 or newer
- `xiaohongshu-cli` 0.6.4 or newer
- Active Xiaohongshu browser login
- UTF-8 terminal
- `lov-branding-consistency` for authored report copy

## Known Risks

- Upstream API changes: surface the raw CLI error and ask the operator to update.
- Paging or repeated note reads may trigger risk control: keep delays, cap notes,
  and preserve partial corpus state.
- A small or promotional sample may overgeneralize: show counts, conflicts, and
  uncertainty instead of presenting synthesis as platform fact.
- Public notes are evidence, not redistribution rights: return URLs and do not
  authorize republishing.
- Login state is sensitive: never read or print cookie values.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Research report contract](references/research-report.md)
- [Implementation notes](references/implementation.md)

## Skill Output

Default report mode produces a Markdown research report plus a JSON evidence
corpus. Search-only mode produces normalized JSON rows with note ID, title,
author, publish label, interaction counts, and URL. The report must keep source
facts separate from authored recommendations.

## Skill Version

0.2.0

## Ethical Considerations

Do not expose cookies, tokens, or secrets. Use only an account the operator is
authorized to use. Treat titles, bodies, and URLs as source evidence rather than
rights to republish. Do not download media unless the operator explicitly asks
for a downstream media handoff.

## User Cases

See `cases/cases.json`. The cases cover raw discovery, zero-match title
filtering, and the topic-to-report default behavior observed in September 2026.

## Dimension Map

- `correctness`: returned metadata and note bodies come from CLI JSON.
- `research-usefulness`: a bare topic yields an answer or plan, not a raw dump.
- `filter-precision`: title filters are local and zero matches are reported.
- `efficiency`: no API key, external database, or cloud service is required.

## Pricing Basis

Free public-source entry. The Skill wraps an open-source CLI and local Python
collection; it does not add proprietary services or recurring infrastructure.
The public source covers discovery, note-body collection, report synthesis, and
search-only export: it excludes account provisioning, manual services, and
upstream API guarantees.

## Distribution

Free channels: GitHub and LovStudio. Paid channels: none. No channel is marked
as uploaded or published beyond the current public source and catalog entry.
