# Yoda long-running Electron runtime optimization

Verdict: `partially_verified`

Safety: `read_only_plan; no process termination or file deletion performed`

## Scope

- **application:** Yoda desktop
- **platform_family:** desktop
- **runtime:** Electron on macOS
- **adapters:** macos, electron, node-chromium, pty, tmux, git-worktree, sqlite
- **workload:** large project mount, periodic pull-request synchronization, session context refresh and resource inventory
- **workload_id:** yoda-large-project-periodic-sync-v1
- **case_version:** v0.18.10 / implementation commit 290fbc48c7
- **legacy_source:** lov-electron-runtime-optimizer@0.1.0
- **safety_boundary:** No blind tmux kill or unknown worktree deletion was used to demonstrate improvement

## Evidence ledger

| Stage | Kind | Metric | Value | Source |
| --- | --- | --- | ---: | --- |
| context | measurement | project-task-count | 916 tasks | runtime database inventory — The largest mounted project contained 33 active and 883 archived task rows. |
| before | inference | initial-task-hydration-upper-bound | 916 records | old getTasks hydration path combined with the task inventory — Code-derived upper bound: the old mount path returned active and archived rows; this is not direct MobX heap telemetry. |
| after | inference | initial-task-hydration-upper-bound | 33 records | active-only mount query combined with the same task inventory — Code-derived upper bound after the patch; archived tasks remain available through lazy loading and point lookup. |
| before | inference | pr-ipc-per-refresh-wave | 916 calls | task count multiplied by the per-task refresh loop — One matching repository completion event scheduled one PR RPC per loaded task. |
| after | code_fact | pr-ipc-per-refresh-wave | 1 calls | project-level batch PR query and single-flight refresh — One refresh wave issues one project batch RPC and updates an in-memory branch index. |
| before | inference | git-subprocesses-per-sync | 1832 processes | per-task RPC fan-out multiplied by two remote reads — Derived work for one project refresh; overlapping repository completion events could add more work. |
| after | measurement | git-subprocesses-per-sync | 15 processes | high-frequency process sampling during the next eight-remote cycle — Fifteen unique Git subprocesses were observed; peak concurrency was five and the cycle lasted about four seconds. |
| before | measurement | session-context-payload | 391000 bytes | full session-context RPC sample — The old polling route also constructed instruction, Skill and dynamic-tool context. |
| after | measurement | session-context-payload | 37600 bytes | lightweight conversation RPC sample — Prompts and messages are fetched without full instruction or Skill scanning. |
| before | measurement | full-session-context-latency | 202 milliseconds | full context request timing — One old-route request sample; not a percentile distribution. |
| after | measurement | lightweight-context-cache-hit | 2.5 milliseconds | lightweight context cache-hit timing — One cache-hit sample; it is not paired directly with the full-context request. |
| after | measurement | runtime-metadata-payload | 67 bytes | lightweight runtime metadata RPC sample — One sample completed in about two milliseconds. |
| before | measurement | tmux-sessions-preserved | 61 sessions | application-owned tmux server inventory — One session was attached; the snapshot covered 341 descendant processes and about 3.7 GiB aggregate RSS proxy. |
| after | measurement | tmux-sessions-preserved | 61 sessions | post-change inventory before any explicit cleanup — The implementation was validated without terminating the user's existing sessions. |
| before | measurement | unknown-worktree-entries-preserved | 307 directories | filesystem membership compared with Git registration — The pool had about 337 first-level entries and 30 Git-registered worktrees. |
| after | measurement | unknown-worktree-entries-preserved | 307 directories | post-change read-only inventory — Unknown entries remained inventory-only and never entered the automatic cleanup loop. |
| before | code_fact | terminal-scrollback-default | 200000 lines | terminal configuration before the bounded lifecycle change — The configured retained history limit was 200,000 lines. |
| after | code_fact | terminal-scrollback-default | 50000 lines | bounded terminal configuration — The default retained buffer is capped while history remains available. |
| before | code_fact | hot-xterm-limit | 4 terminals | renderer terminal lifecycle configuration — Up to four xterm instances could remain hot. |
| after | code_fact | hot-xterm-limit | 2 terminals | renderer terminal lifecycle configuration — The hot instance budget is capped at two. |

## Before/after comparisons

| Metric | Before | After | Delta | Change | Evidence quality | Contract note |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| git-subprocesses-per-sync | 1832 processes | 15 processes | n/a | n/a | directional_evidence | The after value is observed while the before value is inferred, so exact delta is not claimed. |
| hot-xterm-limit | 4 terminals | 2 terminals | -2 | -50.0% | implementation_bound | This is an exact configuration bound, not a measured memory reduction. |
| initial-task-hydration-upper-bound | 916 records | 33 records | n/a | n/a | directional_evidence | The bounds come from code and row counts, not paired renderer heap instrumentation. |
| pr-ipc-per-refresh-wave | 916 calls | 1 calls | n/a | n/a | directional_evidence | The before value is a scale inference; the report suppresses an exact percentage. |
| session-context-payload | 391000 bytes | 37600 bytes | n/a | n/a | directional_evidence | The endpoints return different payload shapes and were not captured as a strict paired timing trial. |
| terminal-scrollback-default | 200000 lines | 50000 lines | -150000 | -75.0% | implementation_bound | This is an exact configuration bound, not a measured RSS reduction. |
| tmux-sessions-preserved | 61 sessions | 61 sessions | 0 | 0.0% | paired_observation | The same application-owned server and inventory definition were used around the change. |
| unknown-worktree-entries-preserved | 307 directories | 307 directories | 0 | 0.0% | paired_observation | The same directory membership definition was used; zero deletion is the safety result. |

## Reclamation plan

| Resource | Kind | Policy | Verdict | Reasons |
| --- | --- | --- | --- | --- |
| representative-working-conversation | agent_session | idle_resumable | **protect** | activity_working |
| representative-idle-resumable-conversation | agent_session | idle_resumable | **candidate** | all_required_proofs_present |
| representative-attached-tmux | tmux | idle_resumable | **protect** | attached_or_subscribed |
| representative-dirty-unreferenced-worktree | worktree | orphan_only | **protect** | dirty |
| representative-clean-orphaned-worktree | worktree | orphan_only | **candidate** | all_required_proofs_present |
| representative-unregistered-directory | directory | inventory_only | **protect** | inventory_only_policy, owner_unknown, activity_unknown, identity_unknown, evidence_missing, retention_unknown, dirty_unknown |

## Ranked hypotheses

- **P0 · eager-archived-hydration:** Mounting archived and active task rows together raised the initial hydration bound and amplified task-scale reactions.
  - Supports: project-task-count, initial-task-hydration-upper-bound
  - Falsifier: The old renderer loads only active rows during mount and resolves archived deep links through point lookup.
- **P0 · full-context-polling:** A UI polling path repeatedly requested substantially more session context than visible surfaces needed.
  - Supports: session-context-payload, full-session-context-latency, lightweight-context-cache-hit
  - Falsifier: Runtime traces show the full context route is reached only by an explicit detail action.
- **P0 · historical-session-revival:** Provisioning tasks restarted historical conversations, preventing idle-session sweeps from creating a stable low-resource state.
  - Supports: tmux-sessions-preserved
  - Falsifier: Startup traces from the old build show only pending work or already-live canonical sessions are started.
- **P0 · per-task-pr-refresh:** A repository synchronization completion event amplified into task-count-scale IPC, Git and database work.
  - Supports: project-task-count, pr-ipc-per-refresh-wave, git-subprocesses-per-sync
  - Falsifier: A trace of the old build shows a bounded project-level query and no per-task repository reads.
- **P0 · unknown-worktree-cleanup-risk:** Filesystem directories absent from Git registration cannot be assigned safely from their names and must remain inventory-only.
  - Supports: unknown-worktree-entries-preserved
  - Falsifier: Every directory carries independently verified product ownership, clean state and no live cwd references.

## Correctness and release gates

- **passed · Yoda release correctness gates:** 591 test files and 3,115 tests passed with format, lint, typecheck and production build; this is a correctness/release gate, not a performance threshold. (`v0.18.10 release run and commit 290fbc48`)
- **passed · Reclamation race coverage:** Focused tests cover fail-closed status, ABA identity, registration/consumer, dirty and unknown resource guards. (`290fbc48 tmux-reclamation and worktree guard tests`)
- **not_run · Production bulk cleanup and on-demand resume trial:** No destructive bulk cleanup was performed on the 61 existing sessions or 307 unknown directories. (`Yoda reclamation case boundary`)

## Evidence gaps

- No controlled packaged-build A/B for input latency, long-task count, event-loop p95/p99, energy, or RSS under the same workload.
- The session payload and latency samples compare different API shapes and single samples; they support direction, not an exact performance percentage.
- The initial task hydration values are code-derived upper bounds rather than direct MobX resident-object telemetry.
- Safe reclamation implementation and race tests landed, but production bulk cleanup plus end-to-end on-demand resume was intentionally not exercised.

## Warnings

- git-subprocesses-per-sync: comparison quality is directional_evidence; exact delta suppressed
- initial-task-hydration-upper-bound: comparison quality is directional_evidence; exact delta suppressed
- pr-ipc-per-refresh-wave: comparison quality is directional_evidence; exact delta suppressed
- session-context-payload: comparison quality is directional_evidence; exact delta suppressed
