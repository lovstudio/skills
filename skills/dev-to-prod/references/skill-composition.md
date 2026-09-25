# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Concrete contract and decision |
| --- | --- | --- |
| `lov-app-release` | downstream atom | Owns a multi-channel external app release with signing, upload, store or website actions, and remote readback. It consumes a verified release candidate or artifact, but it is not invoked for a local-only install. |
| `lov-release-via-cicd` | downstream atom | Configures and publishes CI/CD and GitHub Release workflows. It consumes an explicit release request, version, and release candidate. It remains separate because it can commit, tag, push, and publish. |
| `lov-app-optimizer` | optional upstream atom | Produces real runtime performance evidence. That evidence can inform a production target, but packaging and local-install acceptance remain owned here. |
| `lov-optimize-tauri-backend` | optional upstream atom | Improves a Tauri development boundary, command surface, or restart ergonomics. Its output is source-level backend improvement, not a signed production artifact. |
| `lov-app-generator` | overlap avoided | Creates or standardizes application foundations. It is useful for a new app or broad app-standard upgrade, but does not own conversion of an existing development workspace into a verified production artifact. |
| `lov-electron-app-relaunch` | not composed | Handles Electron lifecycle and relaunch semantics only. It does not own general production readiness or packaging. |

## Atomic Handoffs

```text
optional lov-app-optimizer / lov-optimize-tauri-backend
  runtime evidence or focused source improvement
                    |
                    v
lov-dev-to-prod (core)
  project scope + production-readiness report + verified local artifact
                    |
                    v
optional lov-app-release or lov-release-via-cicd
  remote release, channel mutation, and live readback
```

- The optional upstream handoff is a concrete runtime-evidence record or a focused source change. Its owner accepts performance or backend quality, not packaging.
- `lov-dev-to-prod` owns the production-ready local artifact: it accepts actual build and platform-verification evidence, and returns a compact release-handoff summary if an external release is later requested.
- The downstream release owner accepts an explicit external-release instruction plus version sources and the verified artifact; it owns tags, uploads, public availability, and channel readback.

## Overlap Decisions

No inspected Skill owns the complete boundary between a development workspace and a locally verified production artifact. `lov-app-generator` overlaps in broad application standards but would be too expansive for an existing app. `lov-app-release` and `lov-release-via-cicd` overlap only after the user authorizes external publication; this source deliberately stops before that boundary. The optional upstream Skills remain artifact-level inputs rather than implicit runtime dependencies.

## Composition Decision

This is a **Single Skill**. Scope definition, configuration audit, minimal production changes, production build, native verification, local installation, and release handoff are one ordered outcome sharing the same project and acceptance condition. `scripts/production_audit.py` is deterministic support for that outcome, not an independently useful module. No sibling Skill is required at runtime.
