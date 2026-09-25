# Cross-platform runtime audit and verification playbook

## 1. Verify the thing being measured

Resolve the actual user-facing runtime before profiling:

- source/commit and application version;
- development, profile, release or packaged build;
- device/browser model, OS, runtime engine and relevant feature flags;
- process, thread, isolate, WebView, worker, frame and helper boundaries;
- data scale, cache state, network condition, foreground/background state;
- profiler, log and telemetry locations without copying secrets.

If source and runtime differ, restart only with authorization or label the result
historical. A simulator, debug build or laboratory browser profile can diagnose, but it
cannot silently substitute for the product's final acceptance environment.

## 2. Freeze the workload and comparison contract

Before changing code, define one reproducible action and record:

- exact setup, data size, warm-up and number of repetitions;
- device/browser, OS, build, network, cache, power and thermal conditions;
- sampler and cadence, process/thread boundary and aggregation method;
- declared product threshold and safety invariants.

Use the same `workload_id` after the change. If a dimension changes, label the result
directional and explain the mismatch.

## 3. Collect four evidence axes

| Axis | Examples |
| --- | --- |
| User experience | input latency, frame/jank rate, long tasks, startup/navigation, ANR/hang |
| Runtime resources | CPU, UI/event-loop lag, RSS/footprint, heap, energy, process/thread/isolate count |
| Internal work | IPC/bridge, query, fs, network, render, worker, subprocess counts or bytes |
| Scale | records, mounted surfaces, sessions, jobs, tabs, caches, files, remotes |

Multiple short samples are better than one screenshot. Include idle foreground, idle
background, a typical interaction and at least one known periodic event. Measure the
sampler's own overhead. Descendant RSS sums may double-count shared pages and must be
labeled proxy data.

## 4. Build work and ownership graphs

Map user surface → durable owner → runtime object → external resource, and separately
timer/event → subscribers → per-item work. For every large count, identify the loop
that consumes it.

Quantify amplification:

```text
event frequency
× matching owners or jobs
× resident records or views
× surfaces, frames or subscribers
× per-item IPC + DB + fs + network + render + subprocess work
```

Common amplifiers across stacks include full historical hydration, per-row network or
bridge calls, broadcast invalidation, duplicate query keys, recursive scans, hidden
surface polling, eager prewarming and unbounded async fan-out.

## 5. Reduce work at the right layer

Apply fixes in this order:

1. Stop work that should not start: hidden polling, stale owner revival, eager history.
2. Collapse repeated work: batches, indices, shared caches, single-flight.
3. Bound necessary work: concurrency, byte/time/residency budgets and backpressure.
4. Schedule by lifecycle and visibility; keep an immediate refresh path on re-entry.
5. Reclaim only after ownership, resume and data-loss semantics are explicit.

Track internal work counts beside user-visible metrics. A CPU change alone may be a
scheduler accident; a call-count change alone may leave jank untouched.

## 6. Verify causality and safety

Run repository correctness gates, then rerun the frozen workload on the intended real
runtime. Strong pairs include:

- lower jank/input latency plus fewer main-thread/bridge/render operations;
- lower background energy plus fewer wakeups/jobs/network requests;
- lower resident memory plus bounded object/process counts and successful resume;
- lower mount/start cost plus correct deep-link, restore and cold-start behavior;
- reclaimed resources plus proof that visible, dirty, unknown and in-use items remain.

For mobile final acceptance, use a real device and release/profile build. Test
foreground → background → suspend/process death → restore. For Web/PWA, report lab
PerformanceObserver traces separately from field/RUM data and include visibility,
BFCache, tab discard, Service Worker update and offline behavior where relevant.

## 7. Report residuals honestly

Use only these terminal states:

- `diagnosed`: ranked cause supported; implementation not requested;
- `implemented_not_runtime_verified`: implementation/tests exist; comparable live run absent;
- `partially_verified`: some declared outcomes have runtime support, material gaps remain;
- `verified`: comparable runtime evidence meets all declared thresholds and safety gates;
- `blocked`: runtime identity, authority, adapter or required evidence cannot be obtained.

For each residual hotspot, name one discriminating next measurement. Do not write
“performance solved” when only a fan-out or configuration bound changed.
