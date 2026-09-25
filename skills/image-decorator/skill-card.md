# 图片装帧 · Image Finishing · Skill Card

## Description

Decorates an existing PNG, JPEG, or WebP with a bottom caption bar and verified
bottom-right brand Logo. Artwork uses a Warm Academic outer frame; screenshots
can use a flush borderless treatment.

## Owner

LovStudio — https://lovstudio.ai

## License / Terms

The CLI is MIT licensed. Input media and supplied Logos remain subject to their
original copyright, privacy, attribution, and brand rules. Bundled Noto Sans SC
uses the SIL Open Font License 1.1.

## Use Case

Writers, editors, designers, developers, and publishing agents can turn an
existing image into a consistent article or social-media figure without opening
a design editor. The Skill accepts a local raster image plus optional caption and
Logo, and returns a verified decorated raster file.

## Deployment Geography

Global, local-only execution on macOS, Linux, or Windows.

## Requirements / Dependencies

- Python 3.9+
- Pillow 9+
- Read/write access to local input and output paths
- No credentials, browser, model, or network access

## Known Risks and Mitigations

- Rights and attribution remain the caller's responsibility; the Skill does not
  fetch or license source media.
- Long captions are measured, wrapped, and reduced within a safe range. The CLI
  fails instead of truncating text silently.
- Missing or incompatible Profile Logos fall back to the verified bundled mark.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Style contract](references/style-contract.md)
- [Asset provenance](assets/asset-provenance.json)

## Skill Output

One local PNG, JPEG, or WebP with decoration outside the original image area,
plus a JSON receipt containing caption and Logo provenance, dimensions, layout
metrics, bytes, and SHA-256.

## Skill Version

0.2.1

## Ethical Considerations

Do not remove required attribution, imply a false endorsement, expose private
images, or decorate media whose copyright status is unknown.

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) records the current DSH article's real
artwork input, explicit-caption output, fallback-caption output, and verification
receipt.

### Dimension Map

The machine-readable card covers content preservation, caption integrity, brand
provenance, and output verification. Scores remain unset; each dimension uses
file-backed verification rather than a manufactured numeric rating.

### Pricing Basis

[`pricing-card.yaml`](pricing-card.yaml) records the free local-only boundary and
the conditions that would justify a pricing review.

### Distribution

WorkBuddy, SkillPay, GitHub, and LovStudio are all `not_published`. Local source
creation and installation do not imply any remote listing or release.
