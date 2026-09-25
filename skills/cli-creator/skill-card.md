# CLI 工坊 · CLI Studio · Skill Card

## Description

`lov-cli-creator` turns a local project, or the current Skill invocation
directory by default, into an installable and tested CLI. The command exposes the
project's real backend, supports human and JSON output, and includes executable
acceptance tests.

## Owner

Maintained by LovStudio Skills contributors through the local source repository.

## License / Terms

The Skill source uses the MIT License. Target project licenses, backend runtime
terms, API policies, and data permissions remain authoritative. CLI-Anything is
credited as methodology research under its Apache License 2.0 boundary; its
implementation is not copied into this source.

## Use Case

The audience is a developer or agent that needs dependable command-line access
to an existing application, library, service, native-format tool, or repository.
The Skill inspects callable surfaces, designs task-oriented commands, generates
the harness, installs it locally, and verifies a real project workflow.

## Deployment Geography

Global, local-first. Normal environments are a developer workstation, repository
worktree, and isolated Python virtual environment.

## Requirements / Dependencies

- Python 3.9 or newer.
- Read access to the target project and write access to the selected output.
- The target project's actual executable, API, protocol, library, or renderer.
- No Skill credential. Any backend credentials stay in user-owned runtime
  configuration and are not persisted in plans or evidence.

## Known Risks and Mitigations

- Backend drift or fake behavior: call the maintained backend and require real
  installed-command E2E tests plus postcondition readback.
- Unsafe mutation: use typed argument arrays, preserve unrelated work, inspect
  before mutation, support dry-run where meaningful, and verify resulting state.
- Secret or private-path leakage: keep sensitive values out of source, Profile
  records, argv echoes, logs, JSON evidence, and reusable examples.
- Incomplete breadth: deliver a coherent verified vertical slice and report gaps
  instead of generating broad stubs.

## References

- [Primary Skill instructions](SKILL.md)
- [Machine-readable card](skill-card.yaml)
- [CLI contract](references/cli-contract.md)
- [Project analysis rules](references/project-analysis.md)
- [Upstream research](references/upstream-research.md)
- [Verified case result](cases/evidence/skill-creator-result.json)

## Skill Output

The main output is `agent-harness/` in the target project unless overridden. It
contains an installable Python package, console command, `lov-cli.json` contract,
backend adapter, README, CLI specification, test plan, unit tests, and real E2E
tests. The default command name is `lov-cli-` plus the project slug.

Acceptance requires source and installed invocation, JSON introspection, a real
domain workflow, programmatic postcondition verification, and a passing
`validate_cli.py` run. Remote publication is not part of this output.

## Skill Version

0.1.0

## Ethical Considerations

Only expose operations the user is authorized to perform. Respect target
licenses, privacy boundaries, rate limits, and safety controls. Do not replace
closed or unavailable internals with an imitation and present it as authentic.

## LovStudio Evidence

### User Cases

The first real case used this repository's `skill-creator-skill`. The generated
`lov-cli-skill-creator` exposed `create` and `validate`, installed into an
isolated Python 3.9 environment, passed five generated-CLI tests, created a real
temporary Skill scaffold, and validated the source through its real backend.
See [the case record](cases/cases.json).

### Dimension Map

- **Real backend fidelity — verified:** both domain commands called maintained
  Skill Creator scripts.
- **Agent usability — verified:** help, JSON envelopes, built-in introspection,
  typed inputs, and nonzero failures were exercised.
- **End-to-end correctness — verified:** five helper tests, five generated-CLI
  tests, and five final validator checks passed.
- **Portable defaults — verified:** current-directory input, relative generated
  contract, isolated installation, and private-path hygiene were checked.

### Pricing Basis

Free local source. The value is reusable analysis, generation, and validation;
target runtimes and custom adapters remain outside the price. See
[the pricing card](pricing-card.yaml).

### Distribution

- WorkBuddy: not prepared.
- SkillPay: not prepared.
- GitHub: not published.
- LovStudio: local-only installation verified.
