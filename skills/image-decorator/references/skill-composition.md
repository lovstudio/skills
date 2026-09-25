# Skill Group Composition

## Nearby Skills Inspected

| Skill | Actual routing contract | Classification |
|---|---|---|
| `lov-image-creator` | Generates, code-renders, or prompts a new image. | Optional upstream atom |
| `lov-gen-card` | Builds a complete structured knowledge card as HTML and PNG. | Not composed |
| `lov-table2image` | Converts a Markdown table into a hosted or local PNG. | Optional upstream atom |
| `lov-document-illustrator` | Plans and generates illustrations inside a document. | Optional upstream atom |
| `lov-upload-image` | Turns a verified local image into a public URL or rewrites Markdown references. | Optional downstream atom |

No inspected local or installed Skill accepts an existing raster image and owns
the final outcome of adding a deterministic bottom caption decoration with a
right-aligned brand Logo.

## Atomic Handoffs

| Stage | Owner | Input artifact | Output artifact | Acceptance boundary |
|---|---|---|---|---|
| Optional upstream | Image creation, table rendering, illustration, or user-provided media | Prompt, table, document, or original raster | Verified local image | Upstream owner confirms image content and rights. |
| Core | `lov-image-decorator` | Existing PNG, JPEG, or WebP plus optional caption and Logo | Decorated local PNG, JPEG, or WebP plus JSON receipt | This Skill confirms the original image is preserved, decoration is outside it, caption and Logo sources are explicit, and output metadata matches the file. |
| Optional downstream | Upload or platform publishing Skill | Verified decorated image | URL, media ID, draft, or publication | Downstream owner validates transport and destination rendering. |

## Overlap Decisions

- `lov-image-creator` can code-render arbitrary designs, but it is intentionally
  broader and non-deterministic at the routing layer. Reusing it would add HTML,
  browser, or model machinery to a simple raster transform.
- `lov-gen-card` owns a full editorial card schema with multiple content fields;
  caption decoration alone should not require that schema.
- `lov-table2image` may provide an upstream PNG, but its hosted-table contract and
  layout service remain independent.
- `lov-upload-image` may consume the decorated result later; upload credentials
  and network state do not belong in this Skill.

## Composition Decision

This source is a **Single Skill** with one deterministic Python CLI. Caption
resolution, layout, Logo composition, encoding, and verification all serve one
user-visible result and share one acceptance boundary. External Skills remain
optional file-level handoffs, so a Skill Kit would add ceremony without an
independently useful embedded stage.
