# Skill Group Composition

## Nearby Skills Inspected

- `lov-translation-review` accepts Chinese source documents plus English
  translations and returns a six-dimension Markdown review report. It does not
  edit images, preserve an existing screenshot, or expose rejected machine copy
  inside the final visual.
- `lov-fact-check` verifies a claim through primary and independent sources. It
  can establish a term's evidence but does not own translation, localization,
  or image rendering.
- `lov-image-creator` generates art, code-rendered layouts, or prompts. It can
  consume a finished visual brief but does not decide whether a translation is
  correct or how much wrong text must remain visible.
- System `imagegen` provides reference-image editing and text localization. It
  is a rendering capability, not an editorial acceptance workflow.
- `lov-visual-clone` extracts layout, palette, typography, and style into a
  replication prompt. Its output is design DNA rather than a corrected raster.
- `lov-describe-image` can transcribe an image for a text-only model. It is not
  needed when the active runtime already has vision and does not validate or edit
  translations.

## Atomic Handoffs

- Optional upstream atom: `lov-fact-check` can supply a dated evidence note for
  a current, niche, legal, medical, or product-specific term. The artifact is a
  claim, source list, boundary, and confidence statement.
- Optional upstream atom: `lov-describe-image` can supply a block-by-block text
  transcription when the active runtime lacks vision. The transcription remains
  untrusted until checked against the raster.
- Core atom: `lov-image-translation-errata` accepts the source image, audience,
  and correction intent; it owns the correction map, marked-up image, and all
  five acceptance gates.
- Optional downstream atom: a host image editor, system `imagegen`, or
  `lov-image-creator` can consume the immutable image contract plus rendering
  brief. The renderer does not decide whether the output is accepted.
- No external handoff is required when the host already supplies vision,
  source access, and reference-image editing.

## Overlap Decisions

Translation review is reused conceptually for semantic comparison, but its
Chinese-document-to-English-report contract is too narrow and its final output
is different. Generic image creation and visual cloning are not extended because
they do not own source-backed translation judgments. Rendering remains an
optional tool boundary rather than a hidden sibling dependency.

## Composition Decision

This source is a Single Skill. Source verification, error selection, visible
track changes, rendering constraints, and final visual acceptance all serve one
input image and one user-visible result. Splitting them into a Kit would create
hard coupling without producing independently useful modules.
