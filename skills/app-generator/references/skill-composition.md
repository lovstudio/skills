# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-integrate-lovinsp` | Integrates Lovinsp into a Vite/Webpack/Next.js/Nuxt frontend and verifies click-to-source | required downstream atom | Run for every browser-rendered app; this Skill never hand-installs Lovinsp |
| `lov-gen-logo` | Creates versioned logo drafts and application icons from what the project does | conditional downstream atom | Run for new apps and for upgrades without a logo |
| `lov-install-shadcn-ui` | Installs and brand-configures shadcn/ui while keeping existing theme edits | conditional downstream atom | Run when the UI baseline uses shadcn/ui |
| `lov-install-tanstack-query` | Makes TanStack Query the shared server-state layer | conditional downstream atom | Run when the app has server state; skip for purely local static tools |
| `lov-install-tauri-logo` | Installs a confirmed logo into Tauri bundle and tray icons | conditional downstream atom | Run for Tauri apps, fed with the padded logo from `lov-gen-logo` |
| `lov-project-port` | Picks a stable dev port and updates the project config | optional downstream atom | Preferred for the dev server, never required |
| `lov-finder-action` | Creates a Finder file Quick Action or folder-background menu extension | overlapping atom | See Overlap Decisions |
| `lov-app-release`, `lov-release-via-cicd` | Run and verify a multi-channel release or an existing release pipeline | downstream workflow | This Skill only wires CI/CD and updater config; releasing is handed off |
| `lov-mobile-adapt`, `lov-optimize-tauri-backend` | Adapt an existing web app for phones; restructure an existing Tauri backend | not composed | Follow-up work on an app, not part of generating or standardizing it |
| `lov-oh-my-landingpage` | Builds or rebuilds a brand landing page | not composed | This Skill builds the app workflow itself, never a marketing page |

## Atomic Handoffs

```text
lov-app-generator
  input: app brief (name, app type, platforms, screens, backend, distribution)
         or an existing frontend/Tauri/macOS project
  owns:  app-type decision, scaffold or upgrade, audit_app_project.py checklist,
         Configurable Academic UI rules, CI/CD and updater wiring, final checks
     |
     +--> lov-gen-logo ---------------> lov-install-tauri-logo (Tauri only)
     +--> lov-install-shadcn-ui        (when shadcn/ui is selected)
     +--> lov-install-tanstack-query   (when server state exists)
     +--> lov-integrate-lovinsp        (every browser-rendered app)
     +--> lov-project-port             (optional)
  output: runnable app plus audit, typecheck/build, and Lovinsp readback evidence
```

This Skill owns acceptance of the whole app: the audit and the final checks run
after every delegated atom has finished.

## Overlap Decisions

Both this Skill and `lov-finder-action` can produce a Finder Quick Action. This
Skill treats it as an app deliverable: a containing macOS app with a signed
Action Extension embedded in `Contents/PlugIns`, audited with
`--native-integration finder-quick-action` and accepted only after the packaged
and runtime checks in `references/macos-finder-quick-actions.md`.
`lov-finder-action` remains the narrower creator for a single Finder action.

`lov-install-shadcn-ui`, `lov-install-tanstack-query`, and the logo Skills are
also used on their own. This Skill calls them instead of copying their steps, so
their idempotent behavior applies unchanged when an app is generated again.

## Composition Decision

Single orchestrating Skill. The brief, app-type decision, audit, and acceptance
share one project context and one checklist, while every reusable layer is
already its own Skill reached through `depends_on`; a Kit would only duplicate
that routing.
