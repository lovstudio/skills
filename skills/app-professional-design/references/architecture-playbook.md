# Application Performance Architecture Playbook

Use this reference to reason about the whole product path before selecting a
framework-specific mechanism.

## 1. Start with lifetimes, not files

A module boundary is not automatically a lifecycle boundary. Assign every job
and dataset to the narrowest correct lifetime:

| Lifetime | Examples | Typical owner |
|---|---|---|
| Application | service discovery, durable index supervisor | process-level runtime |
| Identity/account | account directory, permissions, remote session | identity runtime |
| Workspace/database | local index, database snapshot, file watcher | keyed domain runtime |
| Page/view | sorting, viewport, selected item | route or component |
| Request/interaction | one search query, export, mutation | request controller |

The display lifetime may be much shorter than the work lifetime. A view can
subscribe and unsubscribe without controlling a shared producer.

### Ownership test

For each expensive operation ask:

1. Would another page or future revisit reuse the result?
2. Should the work continue with zero current subscribers?
3. What stable identity makes one result different from another?
4. Which event proves the source changed?
5. Who closes workers and clears state when that identity changes?

If answers are missing, the architecture is likely encoded accidentally in UI
effects or backend command handlers.

## 2. Startup is a schedule

Do not treat startup as one promise. Build a dependency graph and schedule four
classes:

| Class | User contract | Examples |
|---|---|---|
| Bootstrap | required to render a coherent shell | locale, route, minimal settings |
| Essential | required for the first intended action | active account, database handle |
| Background | valuable soon, does not gate interaction | index hydration, metadata scan |
| Idle/conditional | run only when relevant or resources are free | maintenance, rare feature prep |

Properties of a professional initializer:

- idempotent `ensure(identity)` semantics;
- single-flight deduplication;
- explicit status such as idle, loading, refreshing, ready, degraded, error;
- progress based on meaningful units when available;
- restartable checkpoints for costly work;
- priority and resource budget;
- dependency failures isolated from unrelated capabilities;
- health and retry visible to diagnostics.

Avoid making the shell await indexes, analytics, update checks, caches, and every
database before first render. Also avoid starting every possible job at once.

## 3. State layers

Use separate layers deliberately:

1. **Authoritative source:** database, filesystem, service, or native subsystem.
2. **Domain snapshot:** coherent version owned by the application runtime.
3. **Durable cache:** optional versioned snapshot/checkpoint for warm startup.
4. **Frontend external store:** renderer-friendly projection and subscription seam.
5. **Page state:** selection, filters, viewport, open panels, transient input.

The page should not become an accidental database, task supervisor, or global
cache. The backend should not emit opaque work that leaves the frontend unable to
render progress or distinguish stale data.

### Placement decision

Do not use “frontend” and “backend” as competing default destinations. Place each
responsibility using these questions:

| Question | Favors frontend/view | Favors domain runtime/backend |
|---|---|---|
| Who owns the state? | ephemeral selection, viewport, draft input | authoritative/shared data |
| How expensive is it? | cheap derivation over visible data | scans, indexing, decode, aggregation |
| Who reuses it? | one mounted view | many views, windows, sessions, or revisits |
| What lifetime is needed? | page/interaction | app, identity, workspace, database |
| What API/data access is required? | renderer-safe local values | native I/O, database, privileged service |
| What failure boundary is useful? | local render fallback | retryable worker or isolated process |
| What latency matters? | immediate input/render feedback | throughput and shared preparation |

Some work belongs in a frontend Web Worker, a shared renderer store, an Electron
utility process, a native application service, or a remote service rather than a
simple frontend/backend binary. Choose the smallest boundary that satisfies the
lifetime, safety, reuse, responsiveness, and recovery contract.

Keep the bridge thin but expressive: the backend should not dictate individual UI
components, and the frontend should not reconstruct authoritative domain state
from a pile of unrelated commands.

## 4. Freshness and invalidation

An invalidation signal means “the source may have changed”, not “discard all
content immediately”. Use a cheap verification step before expensive reload.

A source fingerprint may combine:

- stable source identity;
- schema/version;
- database transaction or data version;
- row count and monotonic row/change token;
- file size and modification generation;
- service ETag, cursor, or revision;
- application-specific logical revision.

Choose fields that detect the real mutation path. Modification time alone may be
noisy; count alone misses in-place edits. When exact change feeds exist, prefer
them over polling.

Recommended refresh flow:

```text
watch/poll signal
  -> debounce/coalesce
  -> inspect lightweight fingerprint
  -> equal: keep current snapshot
  -> changed: background refresh from known revision
  -> publish ordered delta or atomically replace complete snapshot
```

During refresh, retain the last complete snapshot and mark it refreshing. Empty
loading states are appropriate only when no coherent snapshot exists.

## 5. Cache contract

Every durable cache needs:

- cache key including identity and relevant scope;
- schema version and migration/discard behavior;
- source fingerprint/revision;
- written-at time only when time-based freshness matters;
- atomic commit or journal semantics;
- corruption handling;
- size/retention budget;
- privacy and logout cleanup behavior.

Use stale-while-revalidate when slightly stale content is useful and visibly safe.
Do not persist large datasets in synchronous browser storage. Indexed storage,
SQLite, native files, or existing domain caches are usually better fits.

## 6. Failure and recovery

Model failures by layer:

- source unavailable;
- cache corrupt or schema-incompatible;
- worker crashed;
- bridge disconnected;
- slow consumer/backpressure;
- partial batch failed;
- identity changed mid-flight;
- app exited during checkpoint/commit.

The user-facing state should retain useful content, explain whether it may be
stale, provide retry where meaningful, and expose copyable diagnostic details.
Internal diagnostics should include identity hash or safe identifier, generation,
sequence, source revision, phase, queue depth, and the failing operation.

## 7. Systemic audit strategy

When the user says the product has many similar problems:

1. Inventory startup effects, interval polling, file watchers, bridge calls,
   database scans, worker creation, large stores, and route-mount loaders.
2. Group them by shared root cause instead of filing one issue per component.
3. Rank by user pain, frequency, data size, resource cost, and architectural
   leverage.
4. Implement one representative vertical slice that establishes the reusable
   runtime/store/protocol seam.
5. Migrate adjacent paths incrementally with regression tests.

Avoid a big-bang rewrite. A small shared primitive with explicit contracts often
removes several page-local anti-patterns safely.

## 8. Decision record

Write an ADR when the fix changes two or more of these:

- lifecycle owner;
- frontend/backend contract;
- cache format or identity;
- consistency model;
- concurrency model;
- recovery behavior.

Record context, decision, alternatives, consequences, migration, observability,
and rollback. Keep benchmark claims linked to reproducible commands or artifacts.
