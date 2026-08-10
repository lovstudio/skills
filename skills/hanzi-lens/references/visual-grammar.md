# Hanzi visual grammar

Choose the visual from the character's evidence relationship, not from a stock
“Chinese style”.

## Preferred relationships

| Evidence relationship | Professional infographic template | Character-specific visual job |
|---|---|---|
| Core sense → semantic branches → examples | `driver-tree` | Make one governing meaning explain the recorded senses |
| Character alternatives × same criteria | `comparison-matrix` | Compare readings, components, senses, and usage consistently |
| Documented form stages over time | `roadmap` | Show attested forms, dates, sources, and change points |
| Two independent qualities | `positioning-map` | Place related characters only when both axes are defensible |
| Actors / sources → evidence → conclusion | `operating-model` | Explain how standards, dictionaries, texts, and interpretation combine |

Avoid waterfall and quantitative small multiples unless the evidence is truly
numeric and comparable.

## Strong action titles

Weak:

- 认识“翕”
- “翕”的前世今生
- 一个很有文化的字

Strong:

- “翕”不是静止的闭合，而是起飞前的敛翼
- “曌”以日月临空构成新字，政治象征来自使用语境而非部件算命
- “祎”与“袆”只差一旁，却分属美好之义与礼服之名

The visual must prove the title.

## Character as a plotted mark

The target glyph should carry information through at least one of:

- form anatomy with sourced component roles;
- tension or motion supported by a text;
- comparison against related glyphs;
- documented form sequence;
- containment showing root sense and semantic branches.

A huge character with random calligraphy around it is decoration, not evidence.

## Rare-glyph handling

- Run `font-check` before layout.
- Prefer a verified font glyph over an image.
- Preserve IVS sequences when provided.
- If the glyph is absent from the intended font, choose and embed a verified
  fallback; do not replace it with a visually similar character.
- At full size, inspect stroke integrity, clipping, baseline, and font fallback.

## Historical-form handling

Use seal, bronze, or oracle-bone forms only when:

- the form is attested;
- the exact source or facsimile is recorded;
- the stage and date/period are labeled;
- the visual is reproduced faithfully.

Never ask an image model to invent an ancient form. Geometric wings, motion
lines, or component guides may be used only when labeled as visual metaphor.

## Composition

For a 16:9 master:

- header: 7%–18%;
- main visual: 58%–82%;
- footer: 5%–8%;
- one glyph-focused stage may occupy 30%–45% of the width;
- the remaining area should expose the evidence relationship;
- use one accent color for the governing semantic distinction.

Reject equal card walls, decorative ink splashes, faux parchment, random
stamps, pseudo-calligraphy, oversized topic titles, and unreadable source notes.
