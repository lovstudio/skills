# 傅里叶画像 · Fourier Portrait · Skill Card

This human-readable card mirrors `skill-card.yaml`.

## Description

Turns a single-person photo into a vertical Fourier epicycle video. The photo dissolves into
line art, rotating circles redraw the whole face as one continuous line while the number of
terms grows from 1 to 1024, and the video ends on the line art with the series formulas.

## Owner

Lovstudio.AI — https://lovstudio.ai

## License / Terms

MIT. Users remain responsible for photo rights, consent, fonts and logos they supply, and the
final use of the video.

## Use Case

Creators and agents recreating the popular rotating-circles portrait clip with their own
photo, for a short-video post, a talk opener or a personal brand piece. Input is one photo
with a clearly visible face; output is a silent 1080×1920 MP4 with QC material.

## Deployment Geography

Global. Runs locally; nothing is uploaded.

## Requirements / Dependencies

- uv, or Python 3.10+ with numpy, opencv-python-headless, scipy, skia-python, matplotlib
- ffmpeg and ffprobe
- Optional macOS 14+ with Swift for Apple Vision segmentation and face crop
- No credentials

## Known Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Noisy or low-contrast photos give blotchy line art | QC stills first; tune offset, speck size and crop |
| No Vision segmentation off macOS | Report the fallback; use an explicit crop or a plain background |
| Title copy misdescribes the person | One factual line, checked by `lov-branding-consistency` |
| Silent video mistaken for a finished post | Report no audio; hand music to an editing step |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Prior art and technique](references/prior-art.md)
- [Tuning guide](references/tuning.md)

## Skill Output

MP4 (H.264, 1080×1920, 30 fps, no audio), line-art PNG, QC stills, contact sheets and a JSON
report. Validation: recognizable features, final error under 1 %, ffprobe checks and clear
safe areas.

## Skill Version

0.1.0

## Ethical Considerations

Process only photos the user is authorized to use. Everything runs locally. Do not publish or
set the result as an avatar without a separate request.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json): a Channels reference clip and a brand headshot
became a 38.9 s video with final error 0.16 % and fitted decay 1.45.

### Dimension Map

Line-art fidelity, reconstruction accuracy, reference look and render efficiency, each with
measured evidence; scores stay empty until more people and external users are covered.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free entry: fully local, no paid model.

### Distribution

Free channels: `github`, `lovstudio`. No paid channel.
