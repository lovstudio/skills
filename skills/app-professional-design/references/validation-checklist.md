# Production Validation Checklist

Use only the portions relevant to the change, but explicitly account for every
category before declaring completion.

## A. Runtime identity and baseline

- [ ] Confirm the running binary/app points to the intended worktree and commit.
- [ ] Capture cold, warm, revisit, and mutation behavior before the change.
- [ ] Use representative and large datasets, not only fixtures with a few rows.
- [ ] Record profiler, trace, logs, query counts, bridge counts, or timings that
      support the root cause.
- [ ] Separate measured facts from architectural inference.

## B. Lifecycle and correctness

- [ ] Every shared job has an explicit owner, stable identity, and teardown rule.
- [ ] Initialization is idempotent and single-flight for one identity.
- [ ] Page unmount/remount does not restart reusable work.
- [ ] Concurrent subscribers share one producer.
- [ ] Identity changes isolate data and obsolete work.
- [ ] Source changes during a scan produce a coherent snapshot and reconciliation.
- [ ] Last-good content remains available during refresh or recoverable failure.

## C. Incremental bridge

- [ ] Protocol version, identity, generation, sequence, and completion are explicit.
- [ ] First useful data arrives without waiting for the complete dataset.
- [ ] Batch count/size/cadence has a measured rationale.
- [ ] Stale, duplicate, missing, and out-of-order events are handled.
- [ ] Slow-consumer/backpressure behavior is bounded.
- [ ] Reconnect or remount can obtain the current snapshot without restarting work.
- [ ] Bridge call frequency, payload volume, and serialization cost are inspected.

## D. Cache and invalidation

- [ ] Cache key includes the required identity/scope.
- [ ] Schema version and incompatible-cache behavior exist.
- [ ] Source fingerprint detects the actual mutation modes.
- [ ] Noisy watcher/poll signals are debounced or coalesced.
- [ ] Unchanged sources do not trigger full reload or UI replacement.
- [ ] Cache writes are atomic/ordered and corruption is recoverable.
- [ ] Retention, size, privacy, account switch, and logout behavior are correct.

## E. Concurrency and resources

- [ ] CPU, database, network, subprocess, and bridge limits are independently bounded.
- [ ] Foreground interaction keeps priority over background maintenance.
- [ ] Queues expose capacity, overload behavior, cancellation, and shutdown.
- [ ] Worker count is derived/configured and tested against available resources.
- [ ] Oversubscription, queue saturation, retry storms, and slow I/O are tested.
- [ ] Workers, handles, transactions, listeners, timers, and watchers are released.

## F. User experience and diagnostics

- [ ] Existing coherent content is not replaced by a misleading zero/empty state.
- [ ] Progress is monotonic and meaningful, or intentionally indeterminate.
- [ ] Error state explains impact and recovery without exposing internal product intent.
- [ ] Error details are copyable and include safe identity/revision/generation context.
- [ ] Navigation, search, selection, scrolling, and input remain responsive during load.
- [ ] Accessibility and reduced-motion behavior remain correct when UI changes.

## G. Verification matrix

| Scenario | Required evidence |
|---|---|
| Cold start | first interactive and first useful data behavior |
| Warm start | durable snapshot reuse and background validation |
| Navigate away/back | producer call count stays stable; progress/result reused |
| Two consumers | one producer, both receive coherent state |
| Unchanged source signal | no reload, no list replacement |
| Real source mutation | background update reaches consumers once |
| Large dataset | incremental visibility, input/scroll responsiveness, bounded memory |
| Failure/retry | last-good snapshot, useful error, successful recovery |
| Identity switch | old events ignored, old resources released |
| Shutdown/resume | bounded shutdown and valid recovery/checkpoint behavior |

## H. Delivery evidence

- [ ] Lifecycle/state-machine unit tests pass.
- [ ] Bridge/integration tests pass.
- [ ] Typecheck, lint, build, and backend tests pass as relevant.
- [ ] The original interaction is rerun on the real runtime when practical.
- [ ] Before/after measurements use the same environment and data.
- [ ] Architecture decisions and operational diagnostics are documented.
- [ ] Commit/merge/deployment status is reported precisely.
- [ ] Any missing device/runtime/production evidence is named explicitly.

Compilation, a spinner, a toast, an HTTP success, or an installed binary is only
partial evidence. Completion follows the original user-visible performance and
lifecycle contract.
