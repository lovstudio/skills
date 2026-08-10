# Description

`lov-media-fetch` turns a natural-language movie or series request into a normalized
candidate list, an evidence-backed edition choice, a capacity-checked acquisition,
and a final local media verification. It combines qBittorrent discovery and first
probes with an aria2 continuation fallback for slow or unstable swarms.

# Owner

LovStudio / 手工川工作室. The source is maintained as a portable local Skill Kit.

# License

MIT. See [LICENSE](LICENSE).

# Use Case

The primary audience is a user who wants to save a film or series locally while
keeping edition, quality, size, subtitle coverage, and completion evidence visible.
The minimum prompt can be a title, an edition preference, or a Magnet/Torrent input.

# Deployment Geography

The source is ready for local macOS or Linux Agent runtime deployment. It keeps
credentials outside the source and writes reports beside the selected job.

# Requirements

Python 3.9+, PyYAML, FFmpeg/ffprobe, and qBittorrent 5.x are the core requirements.
aria2 1.36+ is an optional fallback. Storage preflight must pass before payload
transfer, and the runtime must provide a secure external credential path for qBittorrent.

# Known Risks

- Advertised source health may differ from live sustained speed; the kit records both.
- Similar releases can represent different cuts; runtime and release evidence decide.
- A completed media file can still lack the requested subtitle language.
- A `.aria2` file indicates resumable state, not a finished local artifact.

# References

- [workflow](SKILL.md)
- [candidate schema](references/candidate-schema.md)
- [acquisition policy](references/acquisition-policy.md)
- [subtitle handoff](references/subtitle-handoff.md)
- [download evidence](cases/evidence/lotr-download.json)
- [verification evidence](cases/evidence/lotr-verification.json)

# Skill Output

The output is a normalized candidate manifest, ranked decision JSON, acquisition and
transport trace JSON, verified local media, and optionally an exact-release UTF-8
Simplified Chinese SRT. `download_status`, `verification_status`, and `subtitle_status`
remain separate fields.

# Skill Version

0.2.0. This release adds aria2 continuation, transport evidence, the subtitle handoff,
and the real 《指环王》三部曲 case.

# Ethical Considerations

Respect applicable rights, source terms, and privacy. Keep credentials outside reports,
label discovery claims versus observed evidence, and state subtitle gaps instead of
presenting an incomplete language package as complete.

# User Cases

## 指环王三部曲

Input: `指环王三部曲`, with extended edition, balanced quality, original audio, and
`zh-Hans` plus English subtitle preferences. Prompt: `$lov-media-fetch 指环王三部曲`.

Output: the selected Extended Remastered 1080p HEVC release completed through a
qBittorrent discovery/probe followed by aria2 same-input continuation. Three media
files passed stream and duration inspection. The final warning precisely records the
missing `zh-Hans` stream and opens the exact-release SRT handoff.

# Dimension Map

| Dimension | Evidence | State |
| --- | --- | --- |
| 剪辑版本识别 | Extended Remastered candidate plus three duration readings | verified |
| 下载韧性 | qBittorrent probe, aria2 continuation, `.aria2` state, final completion | verified |
| 容量纪律 | Preflight formula includes payload, probes, continuation files, and reserve | verified |
| 媒体验收 | Three readable 1920x804 HEVC files, no errors | verified |
| 字幕保真 | English embedded; `zh-Hans` gap is isolated for exact-release SRT matching | warning |

# Pricing Basis

Free local source. The value is the complete evidence-backed workflow: it reduces
wrong-edition downloads, duplicate transfers, unverified client states, and silent
subtitle gaps. The boundary ends at local orchestration and verification; external
source availability and subtitle content are not bundled.

# Distribution

- `lovstudio`: local-ready source and trust bundle.
- `workbuddy`: prepared, not published.
- `skillpay`: pricing card prepared, not published as a paid product.
- `github`: source structure prepared, not remotely published.
