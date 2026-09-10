# 会话救援 · Session Rescuer · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

Diagnoses and recovers a Codex thread that cannot resume with `No tool output
found for tool call call_<id>.` or `Model provider ... not found` after switching
providers. It locates the rollout, finds dangling tool-call/output pairing,
returns on-disk deliverables, and can sync stale thread provider metadata.

## Owner

contributors · local package `lov-fix-codex-session`.

## License / Terms

MIT. Use and modify freely; keep attribution. Redistribution must preserve the
license.

## Use Case

Codex desktop / CLI users whose thread is stuck on a tool-call validation error,
or whose old thread cannot open after CC Switch changes the active provider.
Supported input is a thread id/codex link or `config.toml` plus `state_*.sqlite`;
the expected task is to recover the real deliverables and give a working resume
path.

## Deployment Geography

Global. Runs wherever the Codex sessions directory is readable.

## Requirements / Dependencies

Python 3.8+ (standard library only). Read access to `~/.codex/sessions`;
read/write access to `state_*.sqlite` only for explicit provider sync. No
credentials. Optional handoff to `lov-open-codex-session` for navigation.

## Known Risks and Mitigations

Editing a live thread's rollout may not take effect if the host caches state in
memory — prefer resuming from on-disk deliverables in a new thread. The script
never overwrites by default and keeps a `.bak` when `--write` is used. Provider
repair never rewrites rollout JSONL, because paginated byte offsets would break;
it backs up the SQLite database before `--apply`.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

A diagnostic report (JSON or human-readable) of rollouts, dangling tool calls,
last turn error, and provider distribution; the confirmed deliverable paths; an
optional repaired rollout copy; and a provider-sync report. Validation checks
that the dangling list is reported correctly, the repaired file parses as valid
JSONL, and provider candidates are stale-only unless explicitly expanded.

## Skill Version

0.2.0

## Ethical Considerations

Local-first and read-only by default. No credentials are collected; thread
content, transcripts, and full private paths are never persisted to the shared
profile. Only an explicit `--fix` / `--write` touches a rollout, always with a
backup; provider sync writes only the SQLite index after a consistent backup.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free Skills still explain their value,
boundary, and review trigger.

### Distribution

Keep paid channels (`workbuddy`, `skillpay`) and free channels (`github`, `lovstudio`)
explicit. A planned or unavailable channel must not be described as live.
