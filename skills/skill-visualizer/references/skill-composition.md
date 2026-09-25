# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

- `lov-skill-creator`: creates, validates, and locally installs a complete Skill
  source. It produces an approved input for this Skill but does not visualize
  the created Skill's runtime contract.
- `lov-skill-optimizer`: audits and edits an existing Skill, bumps its version,
  and verifies distribution copies. It does not own a visual logic artifact.
- `lov-skill-distiller`: turns prior project evidence into a Skill blueprint,
  not a runnable local Skill, so it is adjacent but not an input dependency.
- `lov-algo-viz-creator`: creates interactive single-file HTML explanations for
  algorithms and information processes. Its user outcome is presentation, not
  static analysis of Skill source.
- `baoyu-diagram`: renders supplied content as a standalone SVG diagram. It can
  consume a verified logic model but does not extract Skill semantics.
- `baoyu-markdown-to-html`: converts Mermaid-bearing Markdown to an alternate
  styled HTML treatment and can render Mermaid blocks to images. It is an
  optional presentation consumer, not the built-in review path.
- LovStudio web `SkillDependencyExplorer`: visualizes catalog-level relations
  among many Skills. It does not parse the runtime flow inside one Skill.

## Atomic Handoffs

| Role | Owner | Input artifact | Output artifact | Acceptance boundary |
| --- | --- | --- | --- | --- |
| Upstream atom | `lov-skill-creator` | User request or blueprint | Validated local Skill directory | Creator owns source completeness and installation; Visualizer starts from the local source. |
| Core atom | `lov-skill-visualizer` | Skill directory or `SKILL.md` | Scenario-first trust-review HTML, Mermaid Markdown, and `lovstudio/skill-logic/v1` JSON | Visualizer owns the internal/external boundary, fixed input-to-outcome narrative, line-bound evidence, Kit sub-workflows and quality gates, trust gaps, coverage counts, and missing-resource diagnostics. |
| Downstream atom | `baoyu-markdown-to-html` | Verified Mermaid Markdown | Alternate styled HTML and optional Mermaid images | Renderer owns alternate visual fidelity; it must not alter extracted semantics. |
| Downstream atom | `baoyu-diagram` | Verified JSON or Mermaid logic | Standalone SVG | Renderer owns SVG composition; Visualizer remains the semantic source of truth. |

## Overlap Decisions

Generic diagram Skills overlap only at presentation. They stay separate because
they do not resolve Skill paths, extract routing and Profile contracts, preserve
source lines, or diagnose undeclared resources. The catalog dependency explorer
stays separate because its nodes are whole Skills rather than runtime steps.
`lov-skill-optimizer` may use this report during an audit, but the optimizer does
not become a required downstream stage and this Skill never edits its target.

## Composition Decision

This source is a Single Skill. Path resolution, static extraction, Mermaid
source generation, presentation-only localization, embedded Mermaid SVG
rendering, JSON serialization, and diagnostics are one user-visible outcome
with one shared context. The Python CLI and vendored browser runtime are
deterministic machinery, not independently triggerable modules. External
renderers remain optional artifact-level handoffs. Runtime execution and
observed-effect capture remain separate future capabilities: the Visualizer must
not imply that a static graph or packaged validation script proves the target
Skill's real-world result.
