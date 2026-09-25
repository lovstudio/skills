# Codeex Runtime Plugin Contract

This reference describes the audited local contract. Re-read the target
repository before changing it because Codeex follows the upstream Codex app and
may evolve.

## Authoritative files

- `plugins/catalog.mjs` discovers plugin directories, validates required
  manifest strings, confines entry paths, and loads entry modules.
- `plugins/state.mjs` owns desired install state and writes it through a sibling
  temporary file followed by rename.
- `scripts/plugins-cli.mjs` is the supported local list/install/uninstall entry.
- `scripts/build-webview.mjs` calls installed `transformWebview` hooks against a
  staged copy of the production webview.
- `scripts/start.mjs` calls installed `beforeLaunch` hooks and owns managed
  rebuild, signing, launch, restart, and active plugin IDs.
- `scripts/control-server.mjs` exposes authenticated UI lifecycle actions,
  dispatches installed `handleControlRequest` hooks, and distinguishes desired
  plugins from the active runtime set. Its catalog view
  must not freeze the plugin directories that existed when the server started;
  newly valid source must become manageable without an unrelated app restart.
- `scripts/verify.mjs` checks the built app, signature, source markers, and
  installed plugin IDs.

## Source shape

```text
plugins/
└── plugin-id/
    ├── plugin.json
    ├── index.mjs
    ├── focused implementation files
    └── focused tests when needed
```

The directory name must equal `plugin.json.id`. The entry path must resolve
inside that directory.

## Manifest

Required string fields:

- `id`: lower-case kebab-case.
- `name`: user-facing display name.
- `version`: plugin version.
- `description`: concrete user-visible outcome.
- `entry`: relative ESM entry path.

Common optional fields:

- `category` and `icon` for the Codeex plugin directory.
- `requiresRestart` to disclose activation semantics.
- `permissions`, each with a short `label` and an actionable `detail`.

The Codeex management page is part of the plugin contract, not an optional
presentation layer. Every valid source plugin must have one catalog card, and
install/uninstall must use the same desired-state owner as the CLI.

Do not copy a port, socket, managed binary, filesystem scope, or background
process permission from another plugin unless the new implementation truly uses
it.

## Hook: transformWebview

`transformWebview(context)` runs during a staged renderer build. The audited
context contains:

- `stage`: staged webview root;
- `entryFile`: staged production entry chunk;
- `sourceWebview`: prepared upstream webview used only as source truth;
- `lovinspClient`: generated bridge path when available;
- `filesBelow(root, extension)`: deterministic staged-file discovery helper.

Write only inside the staged tree or declared generated outputs. Return compact
diagnostics such as transformed file and marker counts. A thrown error aborts
the new build before it replaces the current webview.

## Hook: beforeLaunch

`beforeLaunch(context)` runs after build verification and before the Codeex
runtime is spawned. The audited context contains:

- `env`: a mutable launch-plan copy, not permission to log all environment values;
- `officialCodexCli`: the bundled CLI selected by Codeex.

Return an object with an optional `env` overlay. A plugin that owns a daemon,
socket, watcher, or managed binary must make startup idempotent and document who
stops or reuses the process.

## Hook: handleControlRequest

`handleControlRequest(context)` runs inside the long-lived launcher/control
service after Codeex authenticates the request. The audited context contains:

- `request`: the Node HTTP request stream;
- `url`: a parsed URL rooted at the local control origin;
- `codexHome`: the active Codex home directory;
- `officialCodexCli`: the bundled CLI selected by Codeex.

Return `null` immediately for paths the plugin does not own. For a handled route,
return `{ status, body }`, restrict methods, bound request-body size, validate
every filesystem path, and keep tokens and prompt contents out of diagnostics.

The host cache-busts each plugin entry import, but Node can retain transitive
relative imports for the lifetime of the launcher service. A changed route
implementation or imported backend module therefore needs a launcher/control
service reload before production readback; restarting only the Electron runtime
does not reload that process.

## Hook independence

A plugin may export one or more of `transformWebview`, `beforeLaunch`, and
`handleControlRequest`. It must not import another plugin's private entry file.
Shared host behavior belongs in a small stable Codeex contract only when
multiple real plugins need it and focused regression tests cover the new
surface.
