# Platform adapter matrix

The core workflow composes three adapter layers:

1. **Host adapter** — macOS, Windows, Linux, iOS, Android or browser environment.
2. **Runtime/framework adapter** — Electron, Tauri/WebView, native UI, React Native,
   Flutter or Web/PWA.
3. **Resource adapter** — optional PTY/tmux, Git worktree, database, cache, media,
   worker, sidecar, network job or project-specific durable resource.

Unsupported layers become evidence gaps. Never borrow a lifecycle or metric from a
different platform merely because its name sounds similar.

## Adapter matrix

| Platform | Runtime boundaries | Preferred final evidence | Lifecycle cases that must be covered |
| --- | --- | --- | --- |
| Electron | main, renderer, GPU, utility/child processes, Node and Chromium tasks | packaged/release build; input/long-task, main event-loop, footprint, IPC/query/subprocess counts | window visibility, renderer reload/crash, app quit/relaunch, helper/session resume |
| Tauri | Rust core, WebView, async tasks, plugins and sidecars | release build; native profiler plus WebView trace and command/sidecar counts | window close/hide, core lifetime, sidecar termination, reopen and relaunch |
| Native desktop | UI thread, worker threads, helpers/services | Instruments, ETW/WPA or perf on release build | window lifecycle, app activation, sleep/wake, helper restart, relaunch |
| iOS | main/UI thread, render pipeline, Swift/ObjC tasks, optional JS/native bridge | real-device Instruments, MetricKit/signposts, release/profile build | foreground, background, suspend, system termination, restoration, BGTask limits |
| Android | main thread, RenderThread, Binder, coroutines, WorkManager and optional JS bridge | real-device Perfetto, Macrobenchmark, JankStats, meminfo, release/profile build | Activity/Compose lifecycle, background restrictions, Doze, process death, restore |
| React Native | compose iOS/Android host with JS/UI/native threads, Hermes/JSC and bridge/JSI | real-device release; native plus JS/bridge traces | native lifecycle plus JS runtime recreation, navigation/surface mount and headless tasks |
| Flutter | compose mobile/desktop host with UI, raster, IO/platform threads and isolates | profile for diagnosis, real release build for final validation | route/view lifecycle, app lifecycle, isolate/plugin work and restoration |
| Web/PWA | main thread, workers, Service Worker, frames and browser processes | PerformanceObserver/User Timing/DevTools plus field RUM where available | visibility, pagehide/pageshow/freeze, BFCache, tab discard, SW update, offline/install mode |

## Desktop read-only examples

Use task-specific variables and the actual application root/PID:

```bash
APP_MAIN_PID=12345
ps -p "$APP_MAIN_PID" -o pid=,ppid=,%cpu=,rss=,etime=,command=
lsof -a -p "$APP_MAIN_PID" -d cwd -Fn
```

On macOS, `sample` and `vmmap -summary` can add native stack and footprint evidence.
On Linux, use application telemetry plus `ps`, `/proc`, `pidstat` or `perf` according to
privileges. On Windows, prefer ETW/WPA and platform process tooling. Record profiler
overhead and do not compare unlike boundaries as one metric.

List a process tree once and aggregate all known roots; do not execute one whole-system
process listing per resource.

## Mobile rules

- Final claims require a physical target device. Simulator/emulator results remain
  diagnostic unless the product explicitly targets that environment.
- Freeze OS, model, build, thermal/power state, dataset and gesture/action script.
- Do not expect continuous app sampling while the OS suspends or kills the process.
  Use signposts, MetricKit/Perfetto, durable markers and restore-time checks.
- Apps cannot proactively kill arbitrary peer processes. Optimize owned tasks, jobs,
  caches and lifecycle subscriptions within platform policy.
- Verify foreground/background transitions, interruption, process death and restoration;
  a fast foreground trace can still hide background energy or data-loss regressions.

## Web/PWA rules

- Fix URL/build, browser version, device class, network, cache and installed-versus-tab
  mode. Cold, warm, BFCache and Service Worker controlled loads are distinct workloads.
- Use `PerformanceObserver`, User Timing and browser traces for lab evidence. Field/RUM
  distributions answer a different question and must stay separate.
- Hidden tabs are throttled; Service Workers terminate by design; pages may enter
  BFCache or be discarded. Model resume/revalidation instead of assuming a daemon.
- Lighthouse, bundle analysis and image compression may support a hypothesis but do not
  replace long-running interaction and lifecycle verification.

## Optional Electron/Yoda resource adapters

These are not core dependencies. They are retained because the first case uses them.

### tmux

Resolve the application-owned socket; never touch the user's unrelated default server:

```bash
APP_TMUX_SOCKET=application-socket
tmux -L "$APP_TMUX_SOCKET" list-panes -a \
  -F '#{session_name}\t#{session_created}\t#{session_activity}\t#{session_attached}\t#{pane_pid}\t#{pane_current_path}'
```

Normalize a proven local “no server” to an empty inventory. Timeout, SSH, permission or
parse failure remains unknown. Inventory each execution context once.

### Git worktrees

```bash
PROJECT_ROOT=/path/to/repository
git -C "$PROJECT_ROOT" worktree list --porcelain
```

Compare registered canonical paths with durable owners and live cwd inventory. Unknown
directories are inventory-only. Never run prune, forced branch deletion or recursive
removal during an audit.

### SQLite and source amplification

Use a read-only connection and query counts/timestamps rather than content. Preserve
the SQL beside the metric. Trace timers/completion events to subscribers and per-entity
loops; search results are leads, not evidence until the complete call path and scale are
verified.

### SSH

Treat each connection identity as a separate runtime. Reuse bounded single-flight
inventories and the project's structured executor. A disconnected remote protects its
resources; “could not list” does not mean “empty.”
