# Changelog

All notable changes to this project are documented here.

## [0.3.0] - 2026-07-29

### Changed

- Added explicit `topic` and `action` title modes; `topic` is now the default
  for standalone, public-facing infographics.
- Changed the default reading order to subject/purpose → visual evidence →
  evidence-backed recommendation.
- Added a shared tail recommendation region between the main visual and source
  footer, with source linkage and duplication rules.
- Extended the CLI with `--title-mode` and `--recommendation`, and upgraded
  generated project metadata to schema version 3.
- Extended strict audit and the quality proxy to check recommendation presence,
  placement, evidence linkage, copy length, and title/recommendation role
  separation.
- Kept answer-first action titles as an opt-in mode for contextual executive
  Exhibits without a repeated recommendation band.

## [0.2.0] - 2026-07-28

### Changed

- Reframed the output unit from a styled poster to an evidence-led consulting
  Exhibit with an action title, dominant visual proof, direct annotation, and
  explicit decision meaning.
- Changed the default master from `4:5` to `16:9`; portrait and square outputs
  are now treated as separately recomposed derivatives.
- Replaced the generic card-based scaffold with eight semantic templates:
  comparison matrix, decision tree, driver tree, positioning map, waterfall,
  roadmap, operating model, and small multiples.
- Added template-specific DOM contracts for evidence, units, axes, branches,
  drivers, gates, flows, annotations, decisions, and visual encodings.
- Added an 85/100 machine proxy gate with critical-dimension floors, area and
  occupancy checks, card-wall rejection, and mandatory recorded human review.
- Added public Bain, McKinsey, and BCG Exhibit benchmarks and two audited 16:9
  examples built from the same source material.
- Removed the original low-density card-wall example from the published cases.

## [0.1.0] - 2026-07-28

### Added

- Consulting-grade message architecture and evidence-ledger workflow.
- Visual-grammar selection matrix for argument maps, comparisons, matrices,
  roadmaps, systems, metric stories, landscapes, and feedback loops.
- Code-first HTML/SVG poster template with Skill Publisher branding and attribution.
- Portable user brand profiles with CLI, environment, and shared-profile
  resolution.
- Playwright-based PNG renderer for `4:5`, `16:9`, `1:1`, and `A4`.
- Strict audit for copy budgets, required regions, overflow, contrast, image
  loading, logo portability, and PNG dimensions.
- Hybrid rendering policy that limits image generation to text-free supporting
  illustrations.
- A fully rendered, editable, and strict-audit-passing example.
