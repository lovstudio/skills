# Concurrency and Capacity Design

Use concurrency to protect responsiveness and improve measured throughput, not as
a default marker of sophistication.

## 1. Classify the workload

| Workload | First choice | Reason |
|---|---|---|
| Many waiting I/O operations | async tasks with bounded concurrency | low idle cost |
| CPU-heavy independent units | bounded worker pool | parallel throughput |
| Blocking native/database API | dedicated blocking pool | protects async/UI loops |
| Crash-, memory-, or runtime-isolated work | process/utility process | fault boundary |
| Ordered single-writer state | actor/serial queue | correctness and backpressure |
| Tiny infrequent work | direct call | lower complexity |

Threading does not remove duplicate work, serialization, lock contention, database
limits, or excessive subprocess creation. Optimize those independently.

## 2. CPU budget

For CPU-bound background work, begin with a bounded value derived from available
logical CPUs while reserving capacity for the UI, event loops, OS, and foreground
actions. A typical starting policy is:

```text
background_cpu_workers = clamp(configured_or_auto, 1, max(1, logical_cpu - reserve))
```

`reserve` and the cap are product decisions, not universal constants. Laptop
thermal limits, efficiency/performance cores, battery state, and foreground load
may justify a lower dynamic budget. Benchmark one, several, and maximum workers on
the same dataset; choose the knee of the curve rather than the highest CPU usage.

Expose a safe automatic default and an advanced override only when users benefit.
Never spawn one worker per item or assume logical CPU count equals optimal database
parallelism.

## 3. Independent limits

Use separate semaphores/queues for resources with different constraints:

- CPU workers;
- filesystem scans;
- database readers and writers;
- remote requests per host/provider;
- subprocesses;
- bridge serialization/in-flight batches;
- image/video/model tasks.

A single global pool may let low-priority indexing starve visible work. Use
priority lanes or reserved capacity where foreground latency matters.

## 4. Queue contract

Every queue defines:

- maximum queued and active work;
- enqueue timeout or rejection behavior;
- priority and fairness;
- deduplication/coalescing key;
- cancellation semantics;
- retry policy with backoff/jitter when appropriate;
- result delivery and stale-generation handling;
- shutdown and drain behavior;
- observable queue depth and wait time.

For replaceable work, prefer latest-wins coalescing. For durable mutations, use
idempotency keys or a journal and preserve ordering requirements.

## 5. Database concurrency

More parallel queries can slow an embedded database through cache churn, locks,
connection overhead, and disk contention.

- Respect the database's single-writer or transaction model.
- Reuse prepared statements and snapshots where appropriate.
- Avoid recounting/scanning the same tables for every view or subscriber.
- Combine related metadata queries when it reduces round trips without delaying
  the first useful result.
- Use incremental cursors/change logs when supported.
- Bound read concurrency and measure cold-cache versus warm-cache behavior.
- Ensure cancellation does not leave transactions or connections hanging.

## 6. Threads versus processes

Choose a process when one or more are decisive:

- untrusted or crash-prone native code needs isolation;
- the runtime cannot parallelize CPU work effectively in threads;
- memory reclamation after a task is important;
- independent lifecycle, priority, or permissions are required.

Account for startup time, memory duplication, IPC, deployment/signing, and recovery.
For ordinary application indexing or database reads, a bounded in-process worker
pool is usually simpler unless measurements or fault boundaries argue otherwise.

## 7. Cancellation and shutdown

Cancellation is scoped:

- consumer cancellation removes delivery to one consumer;
- request cancellation stops one request when its result has no shared value;
- identity cancellation terminates obsolete account/workspace work;
- application shutdown stops intake, drains or checkpoints required work, and
  joins/terminates workers within a deadline.

Do not share one page's abort token with a global producer. Check cancellation at
safe boundaries and make partial writes atomic or recoverable.

## 8. Adaptive behavior

If the product needs it, reduce background pressure when:

- foreground latency or event-loop lag rises;
- the app is on battery or under thermal pressure;
- memory crosses a threshold;
- the database reports contention;
- consumers fall behind;
- the application is backgrounded.

Adaptive control needs hysteresis and observable state; otherwise it oscillates
or makes performance difficult to debug.

## 9. Capacity verification

Test at least:

- one worker versus configured default versus upper bound;
- empty, representative, and worst-case datasets;
- cold and warm caches;
- foreground interaction during background load;
- slow I/O/database and slow consumer simulations;
- cancellation, identity switch, app exit, and worker crash;
- queue saturation and retry storms;
- CPU, RSS, disk/network I/O, throughput, queue wait, and tail latency.

Use P50/P95/P99 or another distribution appropriate to the workload. Report the
same-machine, same-data comparison and preserve the command or benchmark harness.
