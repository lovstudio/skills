# Codeex Plugin Development Loop

Use this loop after inspecting the current repository. It shortens iteration
without confusing a rebuilt renderer, a restarted Electron runtime, and a
reloaded launcher/control service.

## 1. Classify the changed surface

| Changed surface | Fast focused evidence | Minimum live reload | Final proof |
| --- | --- | --- | --- |
| Injected runtime, DOM, or CSS | Browser fixture and staged transform assertion | Rebuild staged webview; restart managed runtime or use isolated smoke | Packaged DOM/CDP readback and screenshot |
| `transformWebview` implementation | Idempotent staged-bundle test | Rebuild staged webview and managed runtime | Static bundle marker plus visible behavior |
| `beforeLaunch` or owned process code | Environment/process test, including repeated call | Start a new managed runtime process | PID/socket ownership and active plugin set |
| `handleControlRequest` entry or imported backend module | Direct request/response test with bounded bodies | Reload launcher/control service | Authenticated production API readback |
| Manifest or desired state | Manifest validation and catalog/status read | Runtime restart only when active set must change | Desired and active sets reported separately |
| Host launcher, control server, or runtime manager | Focused host regression | Full wrapper/service reload | One wrapper, one service, expected runtime PID |

The launcher is a long-lived Node process. Codeex cache-busts the plugin entry
module, but Node may retain its transitive relative imports. If a control route
delegates to another module, an Electron `/api/restart` rebuilds the renderer
and runtime but does not prove that the launcher loaded the changed backend.
Reload the launcher/control service, then read the route again.

## 2. Match native UI before styling

For composer, sidebar, popover, or settings integration:

1. Locate the adjacent native control through a stable semantic attribute.
2. Inspect its actual DOM, classes, SVG, bounding box, and computed color in the
   packaged renderer.
3. Clone or reuse the real icon/surface when the host node is available. Remove
   copied source-inspection metadata that would point to the wrong owner.
4. Use a visually identical fallback only when the native node is absent.
5. Keep insertion idempotent across React rerenders and MutationObserver calls.
6. Dispose listeners, observers, popovers, and owned DOM nodes together.
7. In browser fixtures, wait for the browser process to exit and the local
   server to close before deleting its profile directory. Treat teardown-only
   `ENOTEMPTY` as a cleanup race to fix, not as product-behavior evidence.

Do not accept “looks close” when the neighboring native control is available.
Compare SVG path/viewBox, rendered size, computed color, spacing, and open-state
motion directly.

## 3. Use one running topology

Before launching or restarting, read the authenticated Codeex status and inspect
the exact wrapper, launcher-service, and runtime PIDs. Reuse the existing
managed instance for authorized live iteration.

- If the control port is occupied, identify its owner before acting.
- Do not start a second wrapper or server to work around `EADDRINUSE`.
- A runtime restart is sufficient for renderer-only work.
- A launcher/control-service reload is required for changed control backends.
- Stop only the exact resolved process, then confirm the replacement owns the
  expected port and reports the intended active plugin set.

Prefer isolated smoke when the user has not authorized interruption of the
active instance.

## 4. Read back facts, not intentions

After the required reload:

1. Read desired and active plugin sets.
2. Confirm `restartRequired` matches the sets.
3. Exercise the plugin's actual authenticated route when it owns one.
4. Inspect packaged DOM state, not source or a dev-server approximation.
5. Record compact evidence: runtime version, unique mount count, placement,
   icon/style parity, route result shape, runtime PID, and reload boundary used.

Do not print prompt contents, tokens, control credentials, or complete
environment values while collecting evidence.
