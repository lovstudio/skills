# Changelog

## [0.6.1] - 2026-09-07

### Added

- 统一展示名为「Skill 透视镜」，保持调用 ID 与能力契约。

## 0.6.0

- Replace the interactive evidence explorer with a scenario-first, single-scroll
  trust brief that leads with the concrete situation in which the Skill is the
  right choice.
- Present Before → internal transformation → After, the selected pipeline, its
  non-substitutable value, non-use boundary, deliverables, and trust boundary in
  one fixed narrative.
- Remove primary node selection, diagram tabs, zoom, fit, drag-like canvas work,
  source toggles, inspectors, and action buttons.
- Keep rendered Mermaid runtime, resource, and Kit diagrams as secondary
  technical evidence together with routing, diagnostics, raw source, and JSON.
- Persist the user's linear, read-only, scenario-first review preference in the
  shared Profile and add regression assertions against interaction-heavy output.

## 0.5.0

- Reframe the standalone page as a Skill trust review: declarations, supporting
  capability, acceptance rules, observed effect, and evidence gaps are separate.
- Remove host activation matching from the primary runtime graph; activation and
  non-trigger rules remain available in a collapsed external-boundary section.
- Preserve every step's authored actions, criteria, decisions, guardrails,
  commands, and verification lines with exact source spans.
- Parse Kit module sub-workflows and quality gates and link them to explicitly
  associated controller steps.
- Make every internal Mermaid step keyboard- and pointer-selectable with a
  synchronized evidence inspector and compact step index.
- Add a trust model for traceability, supporting modules/resources, deterministic
  scripts, declared checks, observed artifacts, and unproven effect.
- Fix hidden source panels being visually displayed when authored CSS overrode
  the browser's default `[hidden]` behavior.

## 0.4.0

- Redesign the standalone review around a restrained, purpose-first Mermaid
  canvas with less decorative chrome, smaller headers, and no theme toggle.
- Keep Mermaid source, step evidence, pipeline text, resource tables, and JSON
  collapsed until requested while preserving direct access to diagnostics.
- Add zh-first presentation localization for generated labels and the shipped
  real cases without mutating extracted JSON, paths, commands, or source code.
- Persist the user's HTML review preference through the shared Profile contract.
- Add focused tests for progressive disclosure, source-panel behavior, and
  presentation-only localization.

## 0.3.0

- Make rendered Mermaid SVG the primary HTML review surface instead of showing
  Mermaid only as collapsible source.
- Embed the MIT-licensed Mermaid 11.12.2 runtime for offline `file://` reviews.
- Add diagram tabs, synchronized read-only source, zoom, fit, source copy, SVG
  export, keyboard tab navigation, and render-status reporting.
- Add a browser-level acceptance gate that requires every declared diagram to
  render successfully; this caught and fixed an invalid empty merge node.
- Preserve responsive containment so mobile starts fitted and zooming stays
  inside the diagram canvas rather than widening the page.

## 0.2.0

- Generate a standalone offline HTML review beside every Markdown output by
  default, with explicit `--html` and `--no-html` controls.
- Present runtime flow, Kit pipelines, triggers, resources, diagnostics,
  Mermaid source, and the complete JSON model in one review surface.
- Add JSON download, print, theme, and copy actions with responsive, print, and
  reduced-motion styling and no external runtime assets.
- Add focused regression coverage for HTML embedding, offline behavior, and
  sibling output-path derivation.

## 0.1.1

- Preserve mapping-style `kit.yaml` pipelines and render every named sequence.
- Resolve root package manifests referenced from embedded module instructions
  without inventing per-module `skill.yaml` files.
- Add Kit module and pipeline counts to extraction coverage plus a regression
  test for mapping pipelines and shared root manifests.

## 0.1.0

- Add directory and `SKILL.md` input resolution.
- Extract triggers, ordered workflows, explicit conditions, runtime Profile,
  dependencies, Skill Kit declarations, and recursively linked local resources.
- Generate traceable Mermaid reports and `lovstudio/skill-logic/v1` JSON models.
- Add focused parser tests and a real Skill Creator visualization case.
