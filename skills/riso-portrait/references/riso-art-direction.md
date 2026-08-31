# Riso Portrait Art Direction

## Accepted visual contract

Use the uploaded image as both the edit target and the identity reference. Ask `gpt-image-2`
to translate the visual medium while keeping the person and scene facts stable.

The prompt should express this contract in natural language:

```text
Use case: style-transfer
Asset type: 1:1 social profile avatar
Input image: The uploaded image is the edit target and identity reference.
Primary request: Turn the main subject into a friendly hand-drawn Riso cartoon portrait with bold black outlines, limited spot colors, halftone texture and a simple rounded card background. Preserve identity and key features.
Style/medium: authentic hand-printed Risograph portrait, flat graphic shapes, visible paper grain, halftone dots, bold imperfect ink edges, subtle 4 px registration offset; refined editorial illustration rather than a generic digital filter.
Composition/framing: square close head-and-shoulders portrait optimized for a circular avatar; keep the source pose and gaze direction, preserve the full hair silhouette, and leave comfortable space in front of the gaze.
Color palette: deep charcoal #182A2D, teal #087E8B, vermilion #EF542F, warm paper #F5DFBF.
Constraints: Preserve the exact person's recognizable face shape, eyes, nose, lips, expression, hairstyle, skin proportions, pose, clothing cues, accessories and held objects. Keep identity stable while translating only the visual medium. No facial beautification, age change, pose change, extra accessories or extra people.
Avoid: photorealism, anime style, plastic skin, glossy 3D rendering, text, logos, watermark, white circular cutout, ornate frame.
```

Append a short `Creator note` only when the user supplies a real preference, such as a cleaner
background, a specific two-ink palette, or a tighter crop. The note cannot cancel the identity,
anatomy, composition, or no-text constraints.

## Why direct redraw matters

Riso portrait quality comes from decisions about flat shapes, line weight, ink coverage, negative
space and halftone shadows. A post-processing pipeline can recolor pixels and add dots, but it
cannot reliably redesign those relationships. Do not add Canvas, Sharp, CSS, color-separation or
noise passes after generation.

## Iteration contract

- One correction per pass.
- Repeat every invariant in a correction Prompt.
- When the problem is local, identify the exact region and fact.
- Never describe a new generation as fixed until the corrected detail has been visually inspected.
