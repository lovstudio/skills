# Skill Card — lov-cli2anything

This card mirrors `skill-card.yaml` and records the currently verified local
release state.

## Description

Converts authorized observed API evidence into a validated OpenAPI contract,
API graph, JavaScript SDK, Swagger UI, or task-focused local CLI.

## Owner

LovStudio — https://lovstudio.ai

## License / Terms

MIT. Local use, modification, and redistribution are permitted under the
bundled license.

## Use Case

For developers and agents converting APIs they are authorized to inspect into
reproducible local contracts and callable tools. The current built-in target is
ZenMux.

## Deployment Geography

Runs locally on macOS or Linux; no hosted deployment is required.

## Requirements / Dependencies

Python 3.8+, Node.js 20+, the sibling cli2anything++ project runtime, and npm
dependencies declared by that project. Offline artifact generation requires no
credentials. Live browser workflows require an authorized account session.

## Known Risks and Mitigations

- Observed traffic can contain credentials or private payloads. Prefer redacted
  offline evidence and never persist cookies, tokens, or captured payloads in the
  Skill or shared Profile.
- Unsupported hosts can produce misleading expectations. The Skill stops when no
  verified target adapter exists; version 0.1.0 has a ZenMux adapter.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Composition decision](references/skill-composition.md)

## Skill Output

JSON manifests and OpenAPI/API graph files, JavaScript SDK modules, optional
Swagger HTML/server files, or a generated local CLI. Validation includes the
project regression suite, JSON parse checks, and JavaScript syntax checks.

## Skill Version

0.1.0

## Ethical Considerations

Operate only on accounts, traffic, and interfaces the user is authorized to
inspect. Do not export cookies, tokens, secrets, or unrelated private payloads.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records the real ZenMux log API generation
case and its checked outputs.

### Dimension Map

The machine-readable card tracks contract correctness, credential containment,
and local reproducibility. Scores remain unset until an external benchmark is
defined; the evidence fields record what was actually tested.

### Pricing Basis

[`pricing-card.yaml`](pricing-card.yaml) records free local use, the current
scope boundary, and the conditions for reconsidering access or pricing.

### Distribution

The Skill is locally installed and verified. GitHub, LovStudio catalog,
WorkBuddy, and SkillPay publication have not been performed.
