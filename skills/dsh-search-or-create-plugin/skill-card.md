# 插件选型顾问 · Plugin Advisor · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

Searches the dshfind gateway, analyzes which DSH plugin best fits a goal, then
either adopts the best match with a usage path or produces a new-plugin brief
based on the closest open source.

## Owner

Maintained by Lovstudio. Contact: https://lovstudio.ai

## License / Terms

MIT. Free to use, modify, and redistribute with attribution.

## Use Case

Audience: DSH / DeepSeek Harness users who need a capability and want one
decision: use an existing plugin or build a new one. Supported input: a goal
with core verbs plus optional constraints. Expected task: a verdict per
candidate (MATCH / PARTIAL / NO-MATCH) with gateway-field evidence, then the
chosen path.

## Deployment Geography

Global. Runs in any agent runtime with network access to
https://api.dshfind.com.

## Requirements / Dependencies

No credentials. Python 3.8+ with stdlib only. Public read-only gateway; no
auth. Optional downstream handoffs: dsh-plugin-creator for the create path and
dsh-plugin-publisher for publishing.

## Known Risks and Mitigations

- Verdicts rely on gateway metadata that can be stale or null for new
  plugins: cite gateway fields from the current run, and fall back to stars,
  pushed_at, and install evidence for unrated plugins.
- A missing keyword match can be mistaken for absence: retry with synonyms
  and facets before concluding NO-MATCH, and report evidence gaps explicitly.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Fit analysis rubric](references/fit-analysis.md)
- [Gateway API contract](references/gateway-api.md)

## Skill Output

A decision report: per-candidate MATCH / PARTIAL / NO-MATCH with evidence,
plus the adopted usage path or a new-plugin brief based on the closest open
source. Formats: Markdown report, Markdown brief file, and JSON search
artifact. Validation: every verdict cites gateway fields fetched in this run
or the saved artifact, and usage paths derive from install fields and the
repository README.

## Skill Version

0.1.0

## Ethical Considerations

Do not claim a plugin covers a capability without gateway or repository
evidence; do not present community plugins as vetted. The new-plugin brief
must not copy proprietary logic from the base implementations.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Verified 2026-08-27 against the
live gateway: one MATCH case (vision toolkit) and one NO-MATCH case (RSS to
Feishu delivery).

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.
Dimensions: 决策可靠, 能力覆盖评估, 集成可行.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free: the gateway is public and
read-only, and the analysis is an evidence discipline with no marginal cost.

### Distribution

Free channels only: github and lovstudio. Paid channels are not live.
