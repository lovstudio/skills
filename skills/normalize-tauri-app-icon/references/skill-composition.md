# Skill Group Composition

This map was prepared from the existing Tauri, Logo, SVG, and application
release Skill group. It records optional artifact handoffs rather than external
runtime dependencies.

## Nearby Skills Inspected

| Skill | Classification | Routing contract | Decision |
| --- | --- | --- | --- |
| `lov-gen-logo` | upstream atom | Designs, iterates, approves, and publishes canonical brand marks and app-icon artwork. | Use only when the canonical artwork itself needs design or revision. Hand off an approved PNG/SVG; this Skill does not generate a new brand mark. |
| `lov-png2svg` | optional upstream atom | Converts an existing raster mark to editable SVG. | Use only when editable vector artwork is needed before rounded-corner composition. Raster PNG calibration works without it. |
| `lov-install-tauri-logo` | adjacent install atom | Creates an initial Tauri icon set, tray icon, and project wiring from a Logo. | Use first only for an unconfigured Tauri project. After this Skill takes ownership of scale calibration, do not re-run its icon-generation step with an older source. |
| `lov-install-web-logo` | not composed | Installs favicon, web manifest, and OG assets. | Keep separate: web icon sizing does not establish macOS Dock visual weight. |
| `lov-app-release` | downstream atom | Builds, signs, publishes, and verifies application releases. | Run only after this Skill reaches `dock_visually_verified`; it owns release artifacts and remote state. |
| `lov-optimize-tauri-backend` | not composed | Optimizes Tauri command/runtime backend concerns. | No artifact handoff for a visual icon calibration request. |

## Atomic Handoffs

```text
optional: lov-gen-logo / lov-png2svg
  approved canonical PNG or SVG
                |
                v
lov-normalize-tauri-app-icon
  normalized PNG -> Tauri icon set -> runtime embedding evidence
                |
                v
optional: lov-app-release
  verified app assets and release-ready evidence
```

| Boundary | Input artifact | Output artifact | Acceptance owner |
| --- | --- | --- | --- |
| Design → calibration | Approved canonical PNG/SVG, plus an approved reference icon or measured ratio. | A normalized canonical PNG with a stated alpha envelope. | `lov-normalize-tauri-app-icon` verifies the measured ratio. |
| Calibration → Tauri integration | Normalized PNG. | Regenerated icon set, coherent `bundle.icon`, and Cargo watch declarations. | `lov-normalize-tauri-app-icon` verifies source-to-build embedding. |
| Runtime verification → release | `dock_visually_verified` report and generated project assets. | Versioned, signed, published artifacts. | `lov-app-release` owns packaging and remote release verification. |

## Overlap Decisions

`lov-install-tauri-logo` and this Skill can both generate a Tauri icon set, but
they do not own the same final outcome. The install Skill establishes initial
brand/tray wiring; this Skill measures visual-envelope parity and proves the
debug native executable contains the intended `.icns`. The handoff is
single-owner: once calibration begins, regenerate assets from the normalized
canonical PNG and do not let a second generator overwrite them with a stale
scale.

`lov-gen-logo` intentionally remains upstream. If a user asks to change the
mark’s meaning, color system, or silhouette, route that design decision there
before measuring Dock size here.

## Composition Decision

This is a **Single Skill**, not a Skill Kit. Measurement, normalization, Tauri
asset generation, build-watch inspection, and embedded-byte verification are
one tightly coupled acceptance path with one primary artifact: a Dock icon that
is visually aligned and actually loaded by the native process. The surrounding
Skills create independent artifacts and stay optional handoffs instead of
embedded modules.
