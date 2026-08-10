# Portrait Editing Prompt Recipes

Use these as modular prompt blocks. Keep only the blocks relevant to the
current request.

## Identity lock

```text
Use case: identity-preserve
Asset type: professional profile portrait
Input images: Image 1 is the edit target and the sole identity reference.
Primary request: Edit the supplied photograph, not a newly imagined person.
Constraints: Preserve the exact identity, face geometry, apparent age,
expression, gaze, pose, body proportions, camera perspective, clothing,
composition, and background unless a requested change below explicitly names
one of them.
Avoid: face reshaping, enlarged eyes, narrowed nose, altered jaw, different
teeth, different ears, changed ethnicity, changed age, waxy skin, illustration,
beauty-filter look, text, logo, watermark.
```

## Natural cleanup

```text
Requested changes: Remove temporary blemishes and minor redness, gently even
the skin tone, soften harsh under-eye shadows, and tidy small flyaway hairs.
Keep pores, fine texture, natural asymmetry, moles or identity-defining marks,
and realistic facial contrast. The improvement should be visible but
photographic.
```

## Face brightening

```text
Requested changes: Lift facial midtone exposure slightly, improve eye clarity
and subtle catchlights, and balance white balance across the face. Preserve the
person's natural skin-tone family and the original background exposure.
Avoid global whitening, clipped highlights, glowing skin, or a halo around the
head.
```

## Professional finish

```text
Intended use: resume, professional profile, speaker bio, or personal website.
Requested changes: Create a clean, confident, contemporary professional-photo
finish through restrained retouching, balanced studio-like facial light,
controlled contrast, tidy grooming, and coherent sharpness. Preserve the
original wardrobe and scene unless separately requested.
Style: premium editorial corporate portrait, natural and approachable rather
than stiff, glamorous, or synthetic.
```

## Hat removal and hairstyle reconstruction

```text
Requested structural change: Remove only the hat. Reconstruct the hidden head
and hair using a natural hairline consistent with the visible face, temples,
ears, head angle, lighting, and age. Create a neat 70/30 side part with slight
volume and realistic individual strands. Preserve the face, ears, neck,
clothing, pose, background, framing, and all other pixels as closely as
possible.
Avoid: oversized hair, helmet shape, painted strands, implausible hairline,
extra ears, distorted skull, changed forehead, or altered facial identity.
```

## Targeted correction

```text
This is a correction pass on the latest result. Change only: <one issue>.
Restore and preserve every other aspect from the supplied image, especially
identity, face geometry, skin tone, expression, hairline, clothing,
composition, and background. Do not reinterpret the portrait.
```
