# Skill Group Composition

## Nearby Skills Inspected

- `lov-image-creator` owns image generation and visual-prompt work. It may supply
  a text-free local image, but it does not own card copy, DOM layout, rating, or
  final card export.
- `lov-integrate-modern-screenshot` adds PNG export to an existing arbitrary
  webpage. `lov-gen-card` owns a complete card artifact and therefore ships the
  required browser runtime itself; it does not invoke that sibling at run time.
- `lov-professional-infographic` owns evidence-led one-page Exhibits with charts,
  source linkage, recommendations, and an audit bundle. A series knowledge card
  is intentionally smaller and uses one visual plus concise reference fields.
- `lov-business-card` owns personal identity cards and contact-oriented fields.
  Its routing remains separate from topic, method, and collection cards.
- `lov-rich-export` may package finished HTML and PNG into broader delivery
  formats, but it does not participate in card creation.

## Atomic Handoffs

| Stage | Owner | Input artifact | Output artifact | Acceptance boundary |
|---|---|---|---|---|
| Optional upstream visual | Image-generation capability or user | A text-free 4:3 visual brief | Local PNG, JPEG, WebP, or SVG | No baked text, badge, logo, or card chrome |
| Core card | `lov-gen-card` | Structured JSON plus local visual | Self-contained HTML and dimension-checked PNG | Required fields valid, visual loaded, zero DOM overflow |
| Optional downstream package | Rich-export capability or user workflow | Finished HTML and PNG | Document or distribution package | Core card files remain unmodified and traceable |

There is no mandatory cross-Skill handoff. A supplied local visual is sufficient
for the core workflow.

## Overlap Decisions

The PNG mechanism overlaps with `lov-integrate-modern-screenshot`, but the
acceptance boundary differs. A card must be usable as one standalone artifact,
so the small browser runtime is embedded as a third-party asset rather than
calling a mutable sibling Skill. General webpage integration stays with the
sibling. Image generation, business identity, and evidence-led infographic work
remain intentionally separate.

## Composition Decision

This source is a Single Skill. Input normalization, one DOM preset, guarded text
fitting, browser export, and layout audit form one atomic user outcome. Multiple
scripts would not create independent user-facing modules, and no hard-coupled
external capability is required. Future visual presets can extend the same input
contract without turning the source into a Skill Kit.
