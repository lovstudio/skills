# Skill Group Composition

## Nearby Skills Inspected

- `migrate-to-codex`: migrates instructions, Skills, agents, hooks, and MCP
  configuration into Codex. It does not inspect thread usage and is not composed.
- `lov-distill`: turns completed sessions into reusable writing and only contains
  legacy Claude Code session-stat guidance. It does not own Codex token
  accounting and is not composed.
- `lov-fact-check`: validates technical claims from source and runtime evidence.
  It was an optional upstream method for establishing the token semantics, not
  a runtime dependency of this deterministic inspector.
- Installed `codex-primary-runtime` entry: no routable `SKILL.md` or usage
  output contract was present, so there was no capability to compose.

## Atomic Handoffs

- Optional upstream atom: `lov-fact-check` can provide a dated evidence note;
  this Skill accepts the established field semantics through
  `references/token-semantics.md`.
- Core atom: `lov-codex-thread-usage` accepts a deeplink or UUID and owns the
  final local token report, including correctness of reset-aware aggregation.
- Optional downstream atom: `lov-distill` may consume the JSON report as one
  evidence artifact for a later retrospective; it does not change acceptance of
  the token report.
- No external handoff is required for the user-visible result.

## Overlap Decisions

No inspected Skill owns the same deeplink-to-thread-token outcome. Account quota
and rate-limit readers are intentionally separate because subscription windows
cannot be derived from per-thread token events.

## Composition Decision

This source is a Single Skill. Deeplink parsing, read-only state lookup,
streaming rollout inspection, reset detection, and report formatting share one
input and one acceptance boundary. Splitting them into independently triggered
modules would add coupling without creating separately useful outcomes.
