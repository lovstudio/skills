# Verification Matrix

Use the smallest set that proves the changed surface, then add a real lifecycle
check for product-visible behavior.

| Changed surface | Required evidence |
| --- | --- |
| Manifest only | `codeex_plugin.py validate`, Codeex source checks, plugin-directory rendering when applicable |
| Pure plugin logic | Focused unit test plus manifest/entry validation |
| `transformWebview` | Staged fixture assertion, production build, static verification, and isolated renderer behavior |
| `beforeLaunch` | Focused environment/process test, idempotent repeated call, bounded failure diagnostics, isolated launch |
| `handleControlRequest` | Direct route tests for owned/unowned paths, methods, body bounds, errors, and response shape; launcher-service reload plus authenticated readback when backend source changes |
| State lifecycle | Install, duplicate install, uninstall, duplicate uninstall, unknown-ID rejection, and readable state after every step |
| Management UI | Card discovery after source appears, authenticated install/uninstall round-trip, desired/active/restart state rendering, and no duplicate or stale cards |
| Official UI integration | Inspect Public, Personal, and Codeex states; ensure official source markers, search text, content, and selection recover after switching |
| Native composer/sidebar UI | Browser fixture plus packaged CDP comparison of native and plugin icon path/viewBox, computed color, geometry, placement, open state, unique mount, and dispose cleanup |
| Background ownership | Record owner PID or socket, restart behavior, uninstall cleanup, and no duplicate process |

## Baseline commands

From the Codeex repository:

```bash
python3 "$SKILL_DIR/scripts/codeex_plugin.py" validate <plugin-id> --project-root "$CODEEX_ROOT"
python3 "$SKILL_DIR/scripts/codeex_plugin.py" exercise <plugin-id> --project-root "$CODEEX_ROOT"
pnpm check
```

Use `pnpm smoke` for an isolated production UI instance when product-visible
behavior changed. Use `pnpm smoke:daemonize` when the plugin changes background
task continuity. Do not stop or restart the user's active Codeex instance merely
to satisfy a generic checklist.

For production iteration, inspect the current `package.json` scripts rather than
assuming these names are permanent. A renderer restart does not reload the
launcher/control service; use the reload matrix in `development-loop.md`.

## Evidence language

- `source present`: directory exists and validates.
- `installed`: desired state contains the plugin ID.
- `prepared`: staged build and static verification passed.
- `active`: the running runtime reports the plugin ID.
- `verified`: plugin behavior and uninstall recovery were exercised.

Never collapse these into “done” when later states have not been observed.
