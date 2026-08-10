---
name: lov-professional-portrait
category: Design
tagline: "Turn one photo into a clean, identity-preserving professional portrait."
description: >
  Turn a single-person photo into a polished professional portrait while
  preserving the person's identity. Use restrained skin retouching, exposure
  cleanup, optional hat removal and hairstyle reconstruction, background
  polish, and an explicit quality gate. Trigger when the user asks for a
  professional headshot, business portrait, profile photo, skin retouch,
  brighter face, hat removal, or hairstyle cleanup. Also trigger on "职业照",
  "形象照", "证件形象照", "精修人像", "磨皮提亮", "去掉帽子", "换发型",
  "professional portrait", "headshot", "portrait retouch", and "remove hat".
license: MIT
compatibility: >
  Portable Agent Skills format. Requires an agent runtime with image viewing
  and generative raster-image editing, such as image_gen or an equivalent
  built-in image tool. No Python dependency is required.
metadata:
  author: lovstudio
  version: "0.1.1"
  tags: portrait headshot retouch identity-preserve photo-editing
---

# Professional Portrait — 职业形象照精修

Turn one source photo into a polished, believable professional portrait. The
face should still look unmistakably like the same person; "more professional"
must not become "a different, AI-perfect person."

## When to Use

- A casual photo needs to become a professional headshot or profile image.
- The user wants cleaner skin, brighter facial exposure, or a more polished
  overall look without changing identity.
- A hat, stray hair, or distracting background should be repaired.
- The user is iterating with feedback such as "变化不明显", "更干净帅气一点",
  or "只提亮面部".
- The user wants a before/after or progressive comparison after the edits.

## Core Principle

Identity fidelity outranks beautification. Lock the following unless the user
explicitly requests a change:

- Face geometry, eyes, nose, lips, jaw, ears, and apparent age.
- Skin tone family and recognizable facial details.
- Expression, gaze, body proportions, pose, and camera perspective.
- Clothing, accessories, framing, and background.

Remove only temporary distractions by default. Preserve believable skin
texture, asymmetry, and age-appropriate detail.

## Workflow (MANDATORY)

### Step 1: Inspect the edit target

Identify the user's source photo as the **edit target**, not merely a style
reference.

- If the photo is a local file, view it with the runtime's image-viewing tool
  before editing.
- Check face visibility, lighting, sharpness, crop, background, clothing,
  accessories, hair boundaries, and compression artifacts.
- Never publish, upload as a public example, or add the user's portrait to a
  repository unless the user separately asks for that.

### Step 2: Infer the smallest sufficient brief

Do not ask the user to choose from a long style menu when the request already
has a clear outcome. Use these defaults:

| User intent | Default treatment |
|---|---|
| "磨皮 / 干净一点" | Light skin cleanup with visible pores |
| "提亮" | Lift face exposure and eye clarity; preserve skin tone |
| "职业照 / 形象照" | Natural retouch + balanced light + polished crop/background |
| "去帽子" | Reconstruct only the hidden hair/head region |
| "帅气 / 精神" | Improve grooming, contrast, posture impression, and catchlights without reshaping the face |

Ask one concise question only when the answer materially changes the result,
such as whether to replace the background or what hairstyle to reconstruct.
Use the user's prior messages and visible photo to infer everything else.

### Step 3: Plan the passes

Use the fewest generative edits possible because every extra pass can drift
identity.

1. **Base pass** — restrained retouch and lighting cleanup.
2. **Structural pass** — only when requested: remove hat, rebuild hair, replace
   background, or adjust wardrobe.
3. **Correction pass** — one targeted fix after inspection, not another broad
   makeover.

When multiple changes are requested together and the edit tool handles them
reliably, combine them into one identity-locked pass. Otherwise isolate the
structural change.

### Step 4: Build the edit prompt

Classify the task as `identity-preserve`. Label the source image as:

```text
Image 1: edit target and identity reference.
```

Every prompt must include:

- Intended use: professional profile photo or headshot.
- Exact requested changes.
- Identity and composition invariants.
- Realistic skin and hair requirements.
- A short avoid list.

Read `references/prompts.md` and use the closest recipe. Keep the prompt
specific to the current request; do not silently add wardrobe, background,
body, or facial changes.

### Step 5: Edit with the native image tool

- Prefer the runtime's built-in generative image-editing tool.
- Include the inspected source photo as the edit target.
- Preserve source resolution and aspect ratio unless the user requests a crop.
- Save non-destructively. Default filename:
  `<source-stem>-professional-portrait-v1.png`.
- If the user names a destination, save the selected final there.
- Do not substitute a text prompt, SVG mockup, or CSS filter for the requested
  raster portrait.

### Step 6: Inspect at full image and face crop

Read `references/quality-gate.md`. Check at least:

1. Identity match.
2. Natural skin texture and tone.
3. Eyes, teeth, ears, jaw, and hairline integrity.
4. Hat-removal seams or background edge artifacts.
5. Coherent lighting, shadows, and sharpness.
6. Professional framing without unrequested changes.

If a check fails, make one localized correction and repeat the gate.

### Step 7: Handle iterative feedback precisely

Translate short feedback into one changed dimension:

- "没太大区别" → increase only the requested retouch/brightness strength.
- "脸不够干净" → refine blemishes and uneven tone; preserve pores and shape.
- "再亮一点" → lift face exposure and midtones; do not whiten globally.
- "风格变了" → restore original color, composition, clothing, and facial
  character; reduce the edit scope.
- "更职业" → improve light, background discipline, crop, grooming, and finish;
  do not make the person older, richer, or more corporate by assumption.

Repeat all identity invariants in every correction prompt.

### Step 8: Deliver

Return:

- The final image inline when the runtime supports it.
- The saved file path for project-bound or local-file work.
- A concise list of intentional changes.
- A note confirming what was preserved.

If requested, create a separate before/after or progressive comparison board.
Do not bake labels, watermarks, or marketing text into the portrait itself.

## Completion Criteria

The task is complete only when:

- The final is recognizably the same person at first glance.
- The requested improvement is visible at normal viewing size.
- Skin and hair remain photographic rather than plastic or painted.
- No unrequested identity, clothing, pose, or scene changes remain.
- The original file is untouched and the final path is reported.
