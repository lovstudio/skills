# 品牌片尾 · Logo Sting · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

`lov-logo-sting` turns a brand's official logo SVG into a closing brand sting: a point of light implodes, the logo's
strokes slam in one per beat (shake, RGB split, shockwave, sparks), the build is sucked dark, a single negative frame
lands on the bar line with the wordmark, a light sweep crosses the lockup, it breathes on the beat and hard-cuts to
black. A synthesised sound reads the same timing file, so every hit is on the same frame in picture and sound. The
result is a Remotion `<LogoSting>` Sequence or a standalone H.264/AAC clip, with key-frame, brand-safety and loudness
checks. It was extracted from the 4.8 s ending of the film 《如何用 AI 制作视频》 v0.2.

## Owner

LovStudio (lovstudio.ai).

## License / Terms

MIT; see [`LICENSE`](LICENSE). The Skill ships no logo. Users feed in official logo files they are entitled to use,
and the resulting sting is subject to that brand's own usage rules.

## Use Case

Creators and teams publishing videos for their own or a client's brand, and the video Skills that call it when a
film's ending is decided (`lov-media-creator`, `lov-motion-media-creator`, `lov-3d-motion-media-creator`,
`lov-interview-media-creator`, `lov-motivational-video`, `lov-roundtable-clip`). Input: the official logo SVG, the
film's fps and aspect, optionally the score's beat grid. Task: a 4–5 s logo ending that lands on the music, appended
to a Remotion project or any editing pipeline.

## Deployment Geography

Global, in a local Agent Skills environment on macOS, Linux or Windows (verified on macOS with Apple Silicon). The
host can be a Remotion 4 project or any pipeline that accepts an MP4 (FFmpeg, 剪映/CapCut, NLEs).

## Requirements / Dependencies

- No credentials.
- Python 3.9+; `sting_audio.py` needs numpy, the other scripts use the standard library only.
- Node.js 24+ with npm/npx; Remotion 4.0.534 and React 19.1.0, pinned in the render template.
- ffmpeg and ffprobe; rsvg-convert, qlmanage or a browser to view the grouping preview.
- Network once for `npm install` on the first standalone render, unless `--node-modules` reuses an existing
  Remotion 4.0.534 install.
- No other Skill is required. The output carries no authored reader-visible copy, so `lov-branding-consistency`
  does not apply.

## Known Risks and Mitigations

- **Wrong logo** (the Profile's `brand.logo` is another brand or a square icon): ask once when the film's brand
  differs from `brand.name` or the file is an icon; report the file and its sha256.
- **Redrawn or altered logo**: only official SVGs, path data copied byte for byte, only whole-shape moves and uniform
  scales; QC compares sha256 and regenerates the spec with the same flags for a byte comparison.
- **Wrong stroke grouping or order**: a grouping preview SVG is written on every run and checked by eye; fix with
  `--mark` or `--order`, never by editing the file.
- **Rising-sun composition** (a disc with radiating rays, a known risk with mainland Chinese audiences): streaks,
  sparks and flashes are horizontal, the only round elements are thin shockwave rings; the key-frame sheet is
  checked, and the host's hand-off scene follows the same rule.
- **Loudness jump or true-peak overflow** after mastering and AAC encoding: re-measure the whole film on the encoded
  file. In the reference film this pushed the master target to −2.5 dBTP with a 0.70 limiter (final −16.0 LUFS /
  −2.8 dBTP).
- **Hits off the music**: take the host score's beat grid with `--beats`; end the score on the bar line where the
  sting starts.
- **Edge touch in 16:9**: a slamming stroke may touch the frame edge for one or two frames, as in the reference; the
  final lockup keeps wide margins.

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Data contract](references/spec-contract.md)
- [Integration](references/integration.md)
- [Quality checks](references/qc.md)
- [Skill group composition](references/skill-composition.md)

## Skill Output

`spec.json` (logo-sting-spec/v1) and a grouping preview SVG; `timing.json` (logo-sting-timing/v1); `sting.wav`
(48 kHz stereo 16-bit, −1 dBTP); a `<LogoSting>` Sequence in the host project, or `logo-sting-<aspect>.mp4` clips
(9x16, 16x9, 1x1, 4x3; H.264 CRF 16 yuv420p, AAC 320 kb/s 48 kHz, bt709); a key-frame contact sheet and QC numbers.
Parameters: fps, bpm or beat grid, duration, aspect, colours (final, accent, hot, background), intro (point or
black), gain. Validation: ffprobe checks in the render script, sha256 and spec regeneration, contact-sheet review
including the anti-rays check, and whole-film loudness and true peak.

## Skill Version

0.2.0

## Ethical Considerations

Use only logos the user is entitled to use; never redraw or alter them, and never make a sting that impersonates
another brand. No text or claims are added to the picture. Avoid the disc-with-rays composition. The Skill collects
no personal data; the Profile stores only brand preferences the user stated directly, never credentials.

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json): the ending of 《如何用 AI 制作视频》 v0.2 (2026-10-21), requested as a cool
brand ending with sound, published on Bilibili (BV16gnz6hEgE), and then extracted into this Skill at the author's
request.

### Dimension Map

| dimension | evidence |
| --- | --- |
| correctness | sound byte-identical to the film's sting WAV; path data byte-identical to the SVG; picture vs the delivered films mean Y-PSNR 53.6 / 53.3 dB (9:16 / 16:9, the 140 frames before the black cut), minimum 40.8 / 40.0 dB on the negative frame, explained by the film's colour re-tagging (44.4 dB against the master) |
| effectiveness | used for the 4.8 s ending of the published v0.2 film; the author later called it good and asked for this Skill |
| efficiency | sound in about 0.8 s; two aspects rendered in about 17 s with an existing Remotion install |
| brand-safety | refuses live text, badge lockups and unsupported transforms with a reason; the grouping preview caught a mis-split icon logo; the film's 5 fps ending sheet showed no disc-with-rays composition |
| portability | LovPen, mark-only and even-odd test logos; 30 and 60 fps renders; four aspects; direct JSON import in a strict Remotion host; FFmpeg concat and sample-exact external mix tested |

All scores are `evidence-backed`; see `skill-card.yaml` for the full evidence text.

### Pricing Basis

Free. See [`pricing-card.yaml`](pricing-card.yaml): it is the default ending of every LovStudio video Skill, and its value is
brand consistency across films rather than a stand-alone sale.

### Distribution

| channel | state |
| --- | --- |
| local install | installed: `~/.claude/skills/lov-logo-sting` → `~/.agents/skills/lov-logo-sting` → source directory (verified 2026-10-22) |
| github (free) | private source repository `lovstudio/logo-sting-skill`; the public copy is the `lovstudio/skills` catalog mirror (2026-11-17) |
| lovstudio (free) | pending: catalog entry and mirror submitted; detail page, version and install not yet read back (2026-11-17) |
| workbuddy (paid) | not published |
| skillpay (paid) | not published |
