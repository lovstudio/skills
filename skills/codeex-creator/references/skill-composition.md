# Skill Group Composition

## Nearby Skills Inspected

- `plugin-creator` creates Codex marketplace packages with
  `.codex-plugin/plugin.json`, optional Skills, hooks, MCP, Apps, and marketplace
  entries. Its output is not loadable by Codeex's local runtime catalog.
- `lov-integrate-lovinsp` idempotently integrates Lovinsp into supported frontend
  bundlers. Its output can supply an implementation idea or generated bridge,
  but it does not own Codeex plugin state, production bundle staging, or restart
  verification.
- `lov-electron-app-relaunch` owns generic Electron/Tauri relaunch semantics and
  process replacement evidence. Codeex already has a managed restart and active
  plugin-set contract, so generic relaunch logic must not bypass it.
- `dsh-plugin-creator` creates `@deepseek-ai/dsh-*` packages with Cordis effects,
  capability seams, and package registry rules. Its artifact and runtime are
  unrelated to Codeex.
- `lov-skill-creator` produced this portable Skill source and trust bundle. It is
  an authoring tool, not a runtime dependency of a generated Codeex plugin.
- `frontend-design` can help make a new surface intentional, but an integration
  beside official Codeex controls must first reuse the packaged native DOM,
  icon, spacing, and popover contract documented by this Skill.

## Atomic Handoffs

| Role | Owner | Input artifact | Output artifact | Acceptance boundary |
| --- | --- | --- | --- | --- |
| Optional upstream atom | `lov-integrate-lovinsp` | Frontend project or browser bridge requirement | Lovinsp bundler configuration or bridge code | This Skill must still wrap it in a Codeex plugin, declare permissions, stage the production bundle, and verify uninstall. |
| Optional UI review | `frontend-design` | A plugin with a genuinely new visual surface | Art direction and focused UI critique | Native Codeex controls remain the source of truth for matching icons, geometry, tokens, and interaction. |
| Core atom | `lov-codeex-creator` | Codeex repository plus a plugin capability brief | Validated plugin source, desired-state transition, active-state evidence, and rollback record | The capability appears only while the plugin is active and disappears after uninstall without harming other plugins or official UI. |
| Optional downstream atom | `lov-electron-app-relaunch` | A verified generic relaunch defect outside Codeex's managed lifecycle | Electron/Tauri relaunch implementation and PID evidence | Use only when the problem is the host relaunch mechanism itself; Codeex plugin activation remains owned by Codeex. |
| Optional downstream atom | `lov-skill-publisher` | Validated local Skill source | Remote catalog or channel publication | Publication is outside this Skill and was not requested for the initial release. |

## Overlap Decisions

The Codex `plugin-creator` overlaps in the phrase “create a plugin” but owns a
different manifest, marketplace, installation path, and runtime. Route by the
requested artifact: `.codex-plugin/plugin.json` goes to `plugin-creator`;
Codeex plugin source with `transformWebview` or `beforeLaunch` goes to this
Skill. No files or install commands cross that boundary.

`lov-integrate-lovinsp` remains reusable as an optional upstream atom. This
Skill does not duplicate its bundler knowledge and does not require it for
non-Lovinsp plugins.

## Composition Decision

This is a Single Skill. Scaffolding, hook implementation, validation,
installation, runtime activation, uninstall, and rollback share one Codeex
plugin identity and one final acceptance criterion. The deterministic CLI has
multiple subcommands, but they do not justify independently triggerable Skill
modules. External Skills remain optional artifact-level handoffs.
