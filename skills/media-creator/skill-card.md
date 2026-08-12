# Skill Card — lov-media-creator

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

`lov-media-creator` turns screen recordings, demos, source audio and optional BGM into a publish-ready video. It protects the important result audio, keeps waiting UI short, and returns media, audio, creative and publish evidence as separate states.

## Owner

Media Creator Maintainers; contact through the repository issue tracker.

## License / Terms

MIT. Users may use, modify and distribute the Skill while retaining the license notice.

## Use Case

The Skill is for creators and product teams who need to turn a long recording into a short, understandable video: establish the problem, show credible operation evidence, and finish on the actual result.

## Deployment Geography

Global, in a local Agent Skills environment on macOS, Linux or Windows.

## Requirements / Dependencies

- Python 3.8+ and PyYAML for structural validation.
- FFmpeg and FFprobe for inspection, rendering, frame extraction and audio QC.
- Optional Pillow, Playwright or an image tool when a new cover asset is requested.
- User-provided media and an isolated output directory.

## Known Risks and Mitigations

- The final result or its original audio can be lost. Mark protected segments in the EDL, then spot-check the rendered result and run audio QC.
- Waiting UI can dominate the cut. Keep only the state signal needed for comprehension.
- Unverified speed or publish claims can enter the title or report. Separate rendered, uploaded, published and read-back states.
- BGM can mask speech or feedback. Use ducking, fades and loudness checks; give the result audio priority.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Media workflow](references/media-workflow.md)
- [Delivery contract](references/delivery-contract.md)

## Skill Output

The output is a publish-ready H.264/AAC MP4, a cover direction or asset, an edit manifest, media and audio JSON reports, and a Markdown delivery report. Validation covers streams, dimensions, frame rate, timeline overlap, decodability, loudness, true peak and protected result segments.

## Skill Version

0.1.0

## Ethical Considerations

Process only materials the user has the right to use. Keep credentials and account data outside the Skill and its reports. Do not invent platform read-back, success rates, or performance claims.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). The case records a real Input → Prompt → Output run that ended in a verified video-channel publication.

### Dimension Map

The machine-readable card records four evidence-backed dimensions: editorial fit, audio integrity, technical delivery, and status traceability.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). The local Skill is free; its boundary excludes cloud rendering, media licensing, account credentials and platform operation.

### Distribution

Paid channels: `workbuddy` and `skillpay` are `not-published`. Free channels: `github` is `not-published`, and `lovstudio` is `local-only`. None of these states claims a live remote release.
