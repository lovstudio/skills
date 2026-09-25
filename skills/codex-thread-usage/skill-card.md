# Codex 用量账本 · Codex Usage Ledger · Skill Card

## Description

Given a local Codex deeplink or thread UUID, this Skill produces a reset-aware
historical token report and separates it from the latest SQLite snapshot.

## Owner

Maintained by LovStudio Skill contributors through the local source repository.

## License / Terms

MIT. Use, modify, and redistribute under the included license.

## Use Case

Codex users and developer-tool maintainers can inspect one local task without
opening its conversation or manually adding thousands of cumulative token events.
The result includes processed, input, cached, output, reasoning, TUI-style, and
latest-snapshot values.

## Deployment Geography

Local use worldwide on macOS, Linux, or Windows where Codex state and rollout
files are readable.

## Requirements / Dependencies

- Python 3.9 or newer, standard library only.
- Read access to the local Codex data directory.
- No credentials or network access for normal inspection.

## Known Risks and Mitigations

- Latest SQLite values can reset after resume. The CLI reconstructs monotonic
  rollout segments and reports both values.
- Accumulated token events can be estimated or replayed. The CLI exposes quality
  and never calls the result an invoice.
- Local paths and conversation content can be sensitive. The CLI abbreviates
  paths and never emits message bodies.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Token semantics and evidence](references/token-semantics.md)
- [Composition analysis](references/skill-composition.md)

## Skill Output

Plain-text or JSON token usage report. The JSON contract includes the thread ID,
rollout envelope statistics, latest state snapshot, historical totals, optional
raw-response totals, segment details, method, quality, and warnings.

## Skill Version

0.1.0

## Ethical Considerations

The Skill is local and read-only. It does not expose message bodies, estimate a
person's productivity, or infer billing and account quota from token counts.

## LovStudio Evidence

### User Cases

The redacted real case in [`cases/cases.json`](cases/cases.json) records the
provided deeplink, minimum prompt, verified local output, CLI version, and input
hash without publishing the full local thread identifier.

### Dimension Map

`skill-card.yaml` records four verified dimensions: reset-aware correctness,
metric transparency, local privacy, and portable runtime.

### Pricing Basis

The Skill is free because it is a compact local diagnostic. It excludes account
quota, currency-cost estimation, invoice reconstruction, and remote publication.

### Distribution

The source is locally installed only. GitHub is not published; WorkBuddy and
SkillPay are not planned. No remote channel is represented as live.
