# Hybrid rendering policy

The hybrid route combines code-rendered information with a model-generated
supporting illustration. It is not permission to generate the whole poster as
an image.

## Use an illustration only when

- a physical scene, object, or metaphor is central to comprehension;
- a bespoke cross-section or conceptual object would take unreasonable time to
  draw in SVG;
- the asset can remain non-factual and subordinate;
- the main argument remains understandable if the illustration fails to load.

Prefer CSS/SVG for arrows, matrices, processes, systems, charts, icons, and
labels.

## Asset contract

The prompt must require:

- no words, letters, numbers, glyphs, watermarks, signatures, charts, or logos;
- transparent background or a single flat background color;
- palette specified with exact hex values;
- a clear silhouette at the intended small display size;
- no busy background, fake interface, or generic AI glow;
- no claims that the asset represents factual data.

Example:

```text
Create one editorial vector-style illustration of a bridge connecting two
abstract capability platforms. Clean geometric forms, restrained institutional
style, flat lighting, palette #1F2937 #4F46E5 #F3EEE7. Transparent background.
No text, letters, numbers, icons with labels, charts, logo, watermark, border,
gradient glow, or decorative particles.
```

## Composition

- Generate at least 1.5× the displayed pixel dimensions.
- Crop deliberately; never stretch.
- Set meaningful `alt` text in the HTML.
- Keep the asset below 25% of the visual area unless it is the main explanatory
  object.
- Place all factual labels and callouts as HTML or SVG overlays.
- Apply the same corner radius and color discipline as the code-rendered page.

## Failure handling

Reject and regenerate when the asset contains pseudo-text, unexplained symbols,
brand-like marks, excess detail, wrong palette, or a composition that competes
with the governing message.

If no compliant result is available after one retry, continue with a
code-rendered diagram. Do not block the infographic on decoration.
