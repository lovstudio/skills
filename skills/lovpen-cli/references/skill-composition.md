# Skill Group Composition

## Nearby Skills Inspected

- `lov-cli-creator` turns a local project into an installed, tested CLI
  harness. Its output contract is a ready `lov-cli/v1` package with real-backend
  E2E evidence. It is an upstream creation tool, not a runtime dependency.
- `lov-wdb-cli` is a concrete Skill for querying local WeChat databases through
  its own deterministic CLI. It demonstrates CLI-backed agent routing, but its
  inputs, outputs, privacy model, and acceptance criteria do not overlap Lovpen
  Markdown rendering.
- `lov-skill-creator` creates and validates portable Skill source. It owns this
  source's scaffolding and local installation only; it is not needed when the
  finished Skill runs.
- `lov-skill-publisher` consumes validated Skill source and owns remote
  packaging, submission, catalog state, and public verification. Publication
  was not requested in this workflow.
- No installed Skill already owned the exact `/lovpen-cli` outcome: selecting
  Lovpen CLI commands from natural language and verifying HTML artifacts.

## Atomic Handoffs

| Role | Owner | Input artifact | Output artifact | Acceptance owner |
|---|---|---|---|---|
| Optional upstream | `lov-cli-creator` | Lovpen project source | Ready `lovpen-cli` harness | `lov-cli-creator` owns backend fidelity, installation, and CLI E2E |
| Core | `lovpen-cli` | User intent, Markdown, and optional render settings | Verified HTML or JSON resource/diagnostic result | This Skill owns routing, safe invocation, limitation disclosure, and result interpretation |
| Product backend | `lovpen-cli` executable | Typed argument array | `lov-cli/v1` envelope and material artifact | The CLI owns parsing, atomic writes, and postcondition checks |
| Optional downstream | `lov-skill-publisher` | Validated local Skill source | Channel package or published listing | Publisher owns each channel state and public evidence |

The core Skill may consume a ready CLI created earlier, but it never invokes
`lov-cli-creator` during rendering. The executable is a product dependency,
not an external Skill-to-Skill call.

## Overlap Decisions

The new Skill does not copy Markdown parsing, themes, templates, CSS, or output
verification from the CLI. It keeps only agent-level intent mapping, portable
backend resolution, diagnostic policy, and response interpretation.

`lov-wdb-cli` remains separate because it reads private databases and returns
stable records, while this Skill renders user-supplied Markdown into HTML.
`lov-skill-publisher` remains optional because local installation is complete
without creating remotes, packages, uploads, or listings.

## Composition Decision

This source is a **Single Skill**. Doctor, resource discovery, and render are
commands of one backend and serve one user-visible outcome: operating Lovpen's
standalone and shared WeChat-copy render paths safely from natural language.
They are not independently valuable pipeline stages that justify embedded
Skill modules.

The deterministic resolver stays in `scripts/`. There are no hidden sibling
Skill dependencies and no Skill Kit pipeline.
