# 黑白人像 · B&W Portrait · Skill Card

This human-readable card mirrors `skill-card.yaml`. A reviewer should understand the Skill
without opening its source.

## Description

`lov-bw-portrait` redraws an authorized single-person photo as a recognizable black-and-white
studio avatar with gpt-image-2. The default look is bright and editorial on a light-gray seamless
backdrop; a dark studio look is available. Every result is reviewed against the source for face,
teeth, accessories and small-size legibility before delivery.

## Owner

Lovstudio.AI maintains the Skill. Product information is available at
[lovstudio.ai](https://lovstudio.ai).

## License / Terms

The source is MIT licensed. Users remain responsible for image rights and consent, provider terms,
model usage charges, review of generated output and the final use of the portrait.

## Use Case

The Skill is for people and agents who want a premium monochrome profile avatar that still looks
like the real person. It accepts one authorized photo, such as a selfie, an event photo or an
already stylised portrait, plus a minimal brief. It outputs a square portrait and an honest list of
differences from the source.

## Deployment Geography

It can run in any geography where the user's runtime is allowed to reach a GPT Image 2 endpoint
and to process the supplied photo.

## Requirements / Dependencies

- Image viewing in the agent runtime
- Python 3.8 or newer; the generation CLI uses only the standard library
- An OpenRouter key in `OPENROUTER_API_KEY` with access to GPT Image 2, or an equivalent native
  image-editing tool in the host
- ImageMagick 7 for crop, flip, comparison and thumbnails; macOS `sips` covers plain preparation
- PyYAML for the bundled profile and validation scripts
- No sibling Skill or hosted Lovstudio.AI service is required

## Known Risks and Mitigations

- Models can drift identity or alter eyewear, teeth, fingers, headwear patterns and clothing
  prints. Observed facts are locked in the prompt, results are reviewed at three scales, and
  remaining differences are reported.
- A face photo leaves the machine. The workflow states the upload, asks first when AI generation
  was not requested, and limits consent to the current photo and task.
- A grayscale filter can imitate the surface without the lighting. Local filters are rejected as
  substitutes; the workflow stops when no model is available.
- Generation can fail on a low provider balance. A read-only balance check runs before any work.
- A correction pass redraws the whole image. Each pass is compared with the previous version
  before it is accepted.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Art direction and prompt structure](references/art-direction.md)
- [Quality gate](references/quality-gate.md)
- [Provider notes](references/provider.md)
- [Skill composition record](references/skill-composition.md)

## Skill Output

The normal output is a non-destructive 1024 by 1024 portrait as PNG, with a JPEG export for
delivery. Optional evidence includes a before and after comparison with a zoomed crop and an
avatar-size preview strip. Completion requires identity, fact and avatar-size checks, not visual
appeal alone.

## Skill Version

0.1.0

## Ethical Considerations

Use only photos the user is authorized to process. Tell the user that the photo is uploaded to a
model provider. Do not infer identity or sensitive traits, publish a portrait or set it as an
account avatar without separate permission, or present a model-redrawn face as an unaltered
photograph.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records two real runs: a purple halftone speaking portrait
redrawn in the bright monochrome look, and a single-fact teeth correction with a measured before
and after comparison. The person shown in both is the Skill owner, who asked for the Skill to be
published with these images.

### Dimension Map

The machine-readable card tracks identity fidelity, monochrome studio look, factual integrity and
avatar readiness. Scores are internal judgments on the recorded cases, all on one person; they are
not a guarantee for other faces.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). The Skill is a free entry: it is an instruction and
review layer with a small CLI, users supply their own model access, and the public source is easy
to copy. The pre-publication pricing pass scored it 2.6 out of 5 on six weighted dimensions.

### Distribution

| Channel | State | As of | Evidence |
| --- | --- | --- | --- |
| `github` | live | 2026-11-17 | Private source repository `lovstudio/bw-portrait-skill`; tag `v0.1.0` and its Release sit on the commit that records this state. |
| `lovstudio` | live | 2026-11-17 | Free entry merged in `lovstudio/skills#77`; lovstudio.ai read that commit, the detail page returned HTTP 200 showing version 0.1.0, and `npx lovstudio skills add bw-portrait --project` installed 0.1.0 into a clean directory. lovstudio.cn was not verified. |
| `workbuddy` | not planned | 2026-11-17 | No package built or submitted. |
| `skillpay` | not planned | 2026-11-17 | No product submitted. |

A channel counts as live only after its repository, catalog entry, detail page and install command
are verified independently.
