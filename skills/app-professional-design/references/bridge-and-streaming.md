# Bridge and Incremental Data Protocol

Use this reference for Tauri commands/events/channels, Electron IPC, native mobile
bridges, Web Workers, service workers, WebSocket/SSE streams, and similar seams.

## 1. Bridge responsibilities

The bridge should communicate domain intent and versioned state, not mirror every
backend function or expose renderer lifecycle details.

Recommended control operations:

- `ensure(identity, options)` — single-flight start or reuse;
- `getSnapshot(identity)` — current coherent state without restarting work;
- `subscribe(identity, sinceSequence)` — ordered future updates;
- `inspectSource(identity)` — lightweight revision/fingerprint;
- `invalidate(identity, signal)` — mark possibly stale and schedule verification;
- `retry(identity)` — retry a failed producer;
- `unsubscribe(subscriptionId)` — release one consumer only;
- `disposeIdentity(identity)` — explicit domain teardown.

The exact API may be command/response, event-based, shared memory, or an existing
service abstraction. Preserve project conventions and type the contract.

## 2. Event envelope

A robust message contains enough information to reject stale or duplicated work:

```ts
type StreamEnvelope<T> = {
  protocolVersion: number;
  streamId: string;
  identity: string;
  generation: number;
  sequence: number;
  sourceRevision?: string;
  kind: "snapshot" | "batch" | "patch" | "progress" | "complete" | "error";
  payload?: T;
  progress?: { completed: number; total?: number; phase?: string };
  recoverable?: boolean;
};
```

Adapt field names to the repository. The important properties are stable identity,
generation isolation, monotonic ordering, protocol versioning, and explicit phase.

## 3. Snapshot versus delta

Use snapshots when:

- the complete result is reasonably sized;
- consumers can replace state atomically;
- correctness is simpler than patch reconciliation;
- reconnect frequency is low.

Use batches/patches when:

- the first useful subset should appear quickly;
- the dataset is large;
- updates are frequent and naturally keyed;
- retransmitting the full state is expensive.

Often the best design is a versioned base snapshot plus ordered deltas. On a gap,
consumer restart, or protocol mismatch, request a fresh snapshot instead of trying
to infer missing state.

## 4. Batching and coalescing

Do not send one bridge event per database row, token, filesystem entry, or log
character unless the measured volume is tiny.

Batch by one or more of:

- item count;
- serialized byte size;
- elapsed time;
- animation frame/render cadence;
- transaction boundary;
- product-significant phase.

Tune against first-useful-result latency and total throughput. A larger batch is
not always faster if it blocks serialization or renderer reconciliation.

For high-rate replaceable state such as progress, cursor position, or service
health, keep only the newest pending value. For non-replaceable deltas, bound the
queue and define pause, merge, spill, resync, or producer-throttle behavior.

## 5. Subscription lifecycle

Keep these lifetimes separate:

- producer job;
- domain snapshot;
- bridge stream;
- subscriber;
- page/component.

One page leaving should normally remove one subscriber. Stop the producer only
when the domain contract says work has no future value, the identity is disposed,
or the application is shutting down. Reference-counting subscribers is useful only
when zero subscribers truly means the work is unnecessary.

Frontend adapters should use an external-store/subscription primitive appropriate
to the framework. A component should receive a stable snapshot and unsubscribe
cleanly; it should not call the full loader again on every mount.

## 6. Stale work and races

Use generation/request IDs to handle:

- account or workspace switch during load;
- rapid search input;
- old worker completion after retry;
- reconnect replay;
- refresh started while an earlier load is active;
- source mutation during a long scan.

Consumers accept only the active identity/generation and increasing sequences.
Producers should check whether the source revision changed during the scan. If it
did, publish only a coherent result and schedule another reconciliation instead of
mixing two source states silently.

## 7. Serialization and payload cost

Measure:

- calls/events per second;
- payload bytes before and after serialization;
- encode/decode time;
- copies across the boundary;
- main-thread parse/reconciliation time;
- reconnect/resnapshot volume.

Prefer compact typed payloads and stable IDs. Avoid repeatedly sending unchanged
large fields. Binary transfer or shared memory is justified only after measuring
JSON/structured-clone cost and considering portability/debuggability.

## 8. Platform notes

### Tauri

- Use async commands for orchestration and `spawn_blocking` or a bounded worker
  pool for blocking database/filesystem/CPU work.
- Prefer typed command adapters and channels/events designed for cancellation and
  stale-listener cleanup.
- Keep native state in managed application/domain state, not React page effects.

### Electron

- Keep heavy CPU work out of the renderer and main event loops.
- Use worker threads or utility/child processes when workload or isolation needs
  justify them.
- Type IPC channels, validate inputs, and avoid synchronous IPC.

### Web and mobile

- Use Web Workers/native background execution for measured heavy work.
- Page visibility, navigation, and mobile suspension are lifecycle signals, not
  automatic cache invalidations.
- Design reconnect and resume semantics explicitly.

## 9. Bridge regression cases

Test producer reuse, subscriber churn, batch ordering, sequence gaps, reconnect,
identity switch, source change during scan, slow consumers, queue limits, retry,
and last-good-snapshot retention. Assert call/event counts as well as rendered data;
otherwise duplicate background work can hide behind correct-looking UI.
