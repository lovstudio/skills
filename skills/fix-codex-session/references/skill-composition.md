# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-fix-general` | overlap, kept separate | Diagnoses generic software errors. The session-poisoning failure is a narrow, harness-specific state problem (rollout JSONL tool-call pairing), so it is not delegated here. |
| `lov-fix-by-add-log` | not composed | Adds diagnostic logging to a repo; unrelated to Codex session state. |
| `lov-fix-until-no-error` | optional downstream atom | Could re-run a check after repair, but the outcome here is a recoverable session, not a pass/fail command loop. |
| `lov-open-codex-session` | downstream atom | Navigates to a thread after the id is resolved; it does not modify or repair state. |
| `lov-search-chat` | not composed | Recalls past discussion; does not repair a poisoned thread. |
| `lov-skill-optimizer` / `lov-skill-publisher` | optional downstream atoms | Review or publish this source later; not runtime dependencies. |
| `codex-provider-manager` / CC Switch | adjacent external tool | They change `config.toml`; this Skill repairs the Codex-local thread index after the provider name has become stale, without duplicating config management. |

## Atomic Handoffs

```text
lov-fix-codex-session
  thread id / codex:// link
        -> resolved rollout path + diagnosed dangling tool-call report
        -> recovered on-disk deliverables
        -> optional repaired rollout copy (kept separate from the original)
                |
                v
optional: lov-open-codex-session          navigate to the recovered/alternate thread
optional: lov-fix-general                 continue generic repair if the failure is broader
optional: lov-skill-optimizer             review the source
optional: lov-skill-publisher             distribute the validated source
```

`lov-fix-codex-session` owns: resolving the thread id, locating the rollout,
diagnosing dangling tool-call/output pairing, recovering on-disk deliverables,
producing a safe repaired copy, and aligning stale `threads.model_provider`
values with the active `config.toml` provider. `lov-open-codex-session` owns only
UI navigation; downstream repair states remain explicit and optional.

## Overlap Decisions

No sibling Skill is a hidden runtime requirement. `lov-fix-general` is deliberately
not invoked because it would over-broaden an already-narrow, deterministic harness
fix. `lov-open-codex-session` is optional and consumes only the resolved thread id.

## Composition Decision

`lov-fix-codex-session` is a **Single Skill**. One outcome — diagnose and recover
an un-resumable Codex session — is served by two deterministic CLIs plus
instruction context: rollout repair for tool-call poisoning, and SQLite-only
provider sync for config mismatch. No embedded Kit modules are required.
