# Skill Group Composition

## Nearby Skills Inspected

- `lov-skill-creator` — creates and validates portable Agent Skills. It is an
  upstream atom for this source directory, but it does not generate a CLI for an
  arbitrary product repository.
- `lov-app-generator` — creates or standardizes Web, PWA, and Tauri apps. Its
  routing contract explicitly excludes CLI-only deliverables, so it is not
  composed into this workflow.
- `lov-api-creator` — adds a specific FastAPI gateway and uni-app client layer.
  It does not own general project-to-CLI conversion and is not composed.
- `lov-wdb-cli` — is a concrete CLI product for local WeChat data. It is a useful
  quality example, not a generator or runtime dependency.
- `lov-repo2docs` — produces a documentation website from a source folder. It
  can optionally consume the finished harness and README after this Skill has
  accepted the CLI, but it does not participate in CLI correctness.
- `dsh-plugin-creator` — creates plugins inside one named plugin architecture.
  Its output contract is a plugin package rather than an installable CLI harness.

The installed Skills catalog was also searched for “generate CLI”, “create CLI”,
“CLI harness”, and Chinese command-line generation triggers. No installed Skill
owned the same user-visible result.

## Atomic Handoffs

| Role | Owner | Input artifact | Output artifact | Acceptance owner |
|---|---|---|---|---|
| Upstream atom | `lov-skill-creator` | Request for a reusable Skill | Validated `lov-cli-creator` source | `lov-skill-creator` validates the Skill shell only |
| Core atom | `lov-cli-creator` | Local project path or current directory | Installed, tested CLI harness | `lov-cli-creator` owns backend fidelity and E2E acceptance |
| Optional downstream atom | `lov-repo2docs` | Accepted harness and its README | Documentation site | `lov-repo2docs` owns the site, never CLI correctness |
| Optional downstream workflow | Package/release tooling | Accepted local Python package | Published artifact | Publisher owns channel state and public verification |

There is no required sibling handoff during normal execution. The target
project's own executable, API, protocol, or native renderer is a product backend,
not an Agent Skill dependency.

## Overlap Decisions

`lov-app-generator` and `lov-api-creator` may touch the same repository, but they
own different outcomes. This Skill may expose an app or API through commands; it
does not regenerate the app or redesign its API. Concrete CLIs such as
`lov-wdb-cli` should be preserved and refined directly rather than regenerated.

The CLI-Anything project is research input, not a sibling Skill dependency. This
source adopts its real-backend and E2E principles while using its own portable
contract and helpers.

## Composition Decision

This is a **Single Skill**. Project inspection, contract design, scaffolding,
backend adaptation, installation, and validation are consecutive stages serving
one acceptance criterion: a working CLI for the target project. None is an
independently useful user outcome that warrants an embedded Skill module.

The deterministic helpers remain scripts inside this Skill. External Skills are
optional artifact consumers only, so the source is self-contained and has no
hidden runtime coupling.
