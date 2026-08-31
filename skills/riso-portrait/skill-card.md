# Skill Card — lov-riso-portrait

## Description

`lov-riso-portrait` redraws an authorized single-person photo as a recognizable Riso avatar with
`gpt-image-2`. It locks identity and scene facts, then reviews facial structure, hands, accessories,
objects and circular cropping before delivery.

## Owner

LovStudio maintains the Skill. Product information is available at
[lovstudio.ai](https://lovstudio.ai).

## License / Terms

The source is MIT licensed. Users remain responsible for image rights and consent, provider terms,
model usage charges, generated-output review and the final use of the portrait.

## Use Case

The Skill is for people and agents who want a distinctive profile avatar without turning a real
person into a generic AI face. It accepts one authorized portrait and a minimal brief, then outputs
a square Riso PNG suitable for circular cropping.

## Deployment Geography

It can run in any geography where the user's runtime is allowed to access `gpt-image-2` image
editing and process the supplied photo.

## Requirements / Dependencies

- Image viewing and generative raster-image editing
- `gpt-image-2`; programmatic image filters are not an accepted substitute
- Provider access or credentials supplied by the user's runtime
- No sibling Skill, local post-processing library or hosted LovStudio service is required

## Known Risks and Mitigations

- Models can drift identity or alter anatomy and objects. Every pass repeats identity and scene
  constraints, followed by full, face, hand and avatar-crop review.
- A filtered photo can imitate surface texture without becoming a Riso illustration. The workflow
  requires direct redraw and rejects post-generation color separation or halftone filters.
- Portraits can expose personal information. Inputs must be authorized, remain local unless the
  user separately approves publication, and never enter the shared Profile.
- Generation is not deterministic. Corrections target one observable fact at a time and are not
  accepted until visually inspected.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Riso art direction](references/riso-art-direction.md)
- [Quality gate](references/quality-gate.md)
- [Skill composition record](references/skill-composition.md)

## Skill Output

The normal output is a non-destructive square PNG. Optional evidence boards can compare source and
result or show a correction sequence. Completion requires identity, anatomy, medium and circular-
crop checks rather than visual appeal alone.

## Skill Version

0.1.0

## Ethical Considerations

Use only photos the user is authorized to process. Do not infer identity or sensitive traits,
publish private portraits without separate permission, or treat the illustration as documentary
evidence.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records a three-photo source/result comparison and a real
four-finger to five-finger correction. The user confirmed that every depicted person is authorized.

### Dimension Map

The machine-readable card tracks identity fidelity, Riso medium fidelity, factual integrity and
avatar readiness. Scores describe the current verified cases, not a guarantee for every source.

### Pricing Basis

The Skill is free because it is an instruction and QA layer; users supply their own model access and
generation usage. Hosted inference, bundled credits and rights clearance are outside the boundary.

### Distribution

The intended free channels are the public GitHub repository and LovStudio Skill Publisher. Each
channel is considered complete only after its repository, release, catalog entry, live page and
install command are independently verified.
