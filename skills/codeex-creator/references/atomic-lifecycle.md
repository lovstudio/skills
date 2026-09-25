# Atomic Plugin Lifecycle

Codeex plugin lifecycle has four distinct layers. Calling all of them
“installed” hides failure states and makes rollback unsafe.

## 1. Source present

The plugin directory exists and passes manifest, entry containment, ESM syntax,
and hook checks. New source is written to a sibling staging directory and moved
into its final name only after validation. An occupied final directory is never
overwritten by scaffolding.

## 2. Desired state committed

The plugin ID is present or absent in the Codeex state file. Use Codeex's CLI or
authenticated control API so validation and the temporary-file-plus-rename
writer remain authoritative. Never edit the JSON in place.

Install and uninstall are idempotent desired-state operations. Uninstall does
not delete source, generated evidence, user data, or shared caches.

## 3. Runtime prepared

Codeex builds a fresh staged production webview, applies installed hooks,
atomically swaps the completed staged directory, and signs the wrapper. A hook
failure must leave the currently running runtime and previous prepared bundle
usable.

Desired state may differ from the active set while a restart is pending. Report
that explicitly.

## 4. Runtime active

After an authorized managed restart or an isolated smoke launch, the active
plugin IDs match desired state and the plugin's observable behavior passes. A
successful state write or bundle build alone is not active-state proof.

For a plugin with `handleControlRequest`, runtime activation and backend loading
are separate observations. The Electron runtime may be current while the
long-lived launcher service still holds an older transitive module. Record the
launcher/control reload and authenticated route readback separately.

## Installation transaction

1. Validate plugin source and focused tests.
2. Commit desired installed state through Codeex.
3. Build and verify a staged runtime.
4. Restart only when authorized, or use an isolated smoke profile.
5. Read desired and active sets and exercise visible behavior.
6. If the plugin owns a control route, reload the launcher service when its
   handler or imported backend changed, then exercise the authenticated route.

## Uninstallation transaction

1. Commit desired uninstalled state through Codeex.
2. Build a runtime without the plugin.
3. Restart only when authorized, or use isolated smoke.
4. Verify behavior and owned processes are absent while source remains available.
5. Verify unrelated plugins and official Codex behavior remain intact.

## Rollback

If source validation fails, discard only the staging directory. If desired-state
mutation fails, verify the previous state file is byte-for-byte readable and do
not restart. If build or activation fails, keep the old runtime running, reverse
the desired-state transition, rebuild, and re-read both desired and active sets.

Deleting the plugin directory is not rollback. Removing source is a separate
destructive maintenance request with its own ownership and recovery decision.
