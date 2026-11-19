# 视频转 PPT · Video2PPT · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

Turns a talk, lecture or screen-recording video into a deduplicated slide deck:
PNG frames, a PDF and a PPTX whose notes carry each slide's timestamp. Slides
embedded next to a speaker or above subtitles can be cropped out, crossfade
frames are skipped, and a contact-sheet review loop drops duplicates or adds
missed slides.

## Owner

Lovstudio — https://github.com/lovstudio

## License / Terms

MIT for the Skill source. Users are responsible for having the right to extract
and reuse slides from the source video.

## Use Case

For people who watch talks, courses and product demos and want the slides as a
document. Input is a local video (or a platform video downloaded first); output
is one reviewed slide package.

## Deployment Geography

Global; runs in a local agent runtime on macOS, Linux or Windows.

## Requirements / Dependencies

No credentials. Python 3.9+, Pillow, ffmpeg and ffprobe; python-pptx for PPTX.
Link inputs need a downloader such as `lov-media-crawler` or `yt-dlp`.

## Known Risks and Mitigations

- Same-colour slides look identical to a histogram → layout-aware `pixel` method.
- Subtitles and speaker insets cause fake slide changes → `--crop` to the slide region.
- Crossfades produce blended frames → `--settle` and `--min-duration`.
- Embedded demos get filtered out → review for timeline gaps, `pack --add`.
- Re-runs could overwrite a curated deck → `--overwrite` required; dropped frames are moved, not deleted.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Parameters and tuning evidence](references/tuning.md)
- Upstream desktop app: https://github.com/MarkShawn2020/video2ppt

## Skill Output

One output directory with `frames/`, `NAME.pptx`, `NAME.pdf`,
`contact-sheet.jpg` and `manifest.json` (plus `dropped/` after review).
Parameters: method, similarity, fps, crop, settle, min-duration, start/end.
Validation: manifest slide count equals PPTX and PDF page counts, and the
contact sheet is reviewed.

## Skill Version

0.1.0

## Ethical Considerations

Slides belong to their authors. Only process videos the user can legitimately
access; every slide keeps its source timestamp for attribution, and visible
watermarks or credits are not removed.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json): a 13-minute public talk from a
WeChat Channels link became a reviewed 39-slide PPTX; the desktop default found
only 6 slides.

### Dimension Map

Slide coverage, clean deck and turnaround, each with measured evidence in the
machine-readable card. Scores are left unset until more cases exist.

### Pricing Basis

Free entry, matching the MIT upstream project; weighted score 2.75/5. See
[`pricing-card.yaml`](pricing-card.yaml).

### Distribution

Free channels: `github`, `lovstudio`. No paid channel.

| Channel | State |
| --- | --- |
| lovstudio | live (2026-11-19): lovstudio/skills#90 merged as de7fe08 and read by the site; /skills/video2ppt HTTP 200 showing 0.1.0 and Free; isolated `--project` install delivered 0.1.0 |
