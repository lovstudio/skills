# 插件雷达 · Plugin Radar · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

Searches the public dshfind plugin gateway and returns a ranked,
evidence-tagged list of DSH plugins that match the user goal, with gateway
provenance such as data version and freshness timestamps.

## Owner

Maintained by Lovstudio. Contact: https://lovstudio.ai

## License / Terms

MIT. Free to use, modify, and redistribute with attribution.

## Use Case

Audience: DSH / DeepSeek Harness users and plugin developers. Supported input:
a goal or keyword plus optional filters. Expected task: produce the candidate
plugin list with score, grade, install path, and risk evidence before the user
decides use-or-create.

## Deployment Geography

Global. Runs in any agent runtime with network access to
https://api.dshfind.com.

## Requirements / Dependencies

No credentials. Python 3.8+ with stdlib only. Public read-only gateway; no
auth. The OpenAPI document lives at
https://dshfind.lovstudio.ai/openapi.json.

## Known Risks and Mitigations

- Gateway data may be stale for newly indexed plugins: always cite
  data_version and as_of, and treat null score or grade as unrated.
- Keyword search can miss a good match: retry with synonyms, the category
  facet, or the catalog and GraphQL endpoints before concluding absence.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Gateway API contract](references/gateway-api.md)

## Skill Output

A ranked plugin list where each candidate carries description, score, grade,
stars, install kind, risk flags, and repository link. Formats: Markdown report
and optional raw JSON artifact. Validation: every claim cites a live response
or the saved artifact, with data_version and as_of reported.

## Skill Version

0.1.0

## Ethical Considerations

Search results are public catalog data. Do not present third-party plugins as
vetted by the user or by Lovstudio; gateway risk flags are evidence, not
guarantees.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Verified 2026-08-27 against the
live gateway: vision keyword search and memory suggestion.

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.
Dimensions: 结果准确, 覆盖充分, 检索高效.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free: the gateway is public and
read-only, so this skill adds a deterministic client and an evidence
discipline at no marginal cost.

### Distribution

Free channels only: github and lovstudio. Paid channels are not live.
