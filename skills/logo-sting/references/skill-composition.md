# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

Inspected on 2026-10-22 by routing description, frontmatter and the lines that mention this Skill.

| Skill | routing contract (short) | relation |
| --- | --- | --- |
| `lov-media-creator` | recordings, Screen Studio projects, vlogs into Remotion films with subtitles, mix, covers | downstream consumer, optional: lists `lov-logo-sting` in frontmatter `dependencies:`; offers it once when the ending of a brand-facing film is decided |
| `lov-motion-media-creator` | motion atlas films without live footage (timeline, map, catalogue, process, scale) | downstream consumer, optional (`dependencies:`; listed in its suite reference) |
| `lov-3d-motion-media-creator` | 3D process/product films on top of the motion-media pipeline | downstream consumer, optional (`dependencies:`); routes "only a brand logo ending" here |
| `lov-interview-media-creator` | one interview into a vertical WeChat Channels short | downstream consumer, optional (`dependencies:`); the sting can replace its static `LogoCard` |
| `lov-motivational-video` | original motivational film package for a brand | downstream consumer, optional (`dependencies:`); offered after the emotional landing, never on drafts |
| `lov-roundtable-clip` | roundtable/interview footage into topic clips, 剪映 drafts or rendered clips | downstream consumer, optional (`dependencies:`); only for rendered `video`/`vertical` brand-facing clips |
| `lov-gen-logo` | creates versioned logo drafts and app icons | upstream atom: an approved, published logo SVG from it can be the input; drafts are not |
| `lov-find-logo` | fetches public logos (Clearbit, og:image, favicon) for lineups | upstream atom, conditional: only when the result is the brand owner's own vector SVG; raster or third-party logos are refused |
| `motion-graphics` / `hyperframes` | design-led HyperFrames motion graphics, including a "logo sting / brand lockup" | overlap in topic, kept separate (see below) |
| `lov-video-chapter` | chapter bars and overlays from subtitles | not composed: no shared artifact |
| `lov-channels-cover` | WeChat Channels cover pairs | not composed: covers are stills, the sting is the film's last seconds |
| `lov-branding-consistency` | gate for reader-visible copy | not applicable: the sting has no authored copy (the wordmark is the logo's own shapes) |

## Atomic Handoffs

| step | input artifact | owner | output artifact | acceptance owned by |
| --- | --- | --- | --- | --- |
| logo | official logo SVG (brand assets, Profile `brand.logo`, or an approved `lov-gen-logo` file) | brand owner / upstream Skill | the same SVG, unedited | this Skill checks sha256 and grouping |
| spec | official SVG + flags (`--mark`, `--order`, colours) | this Skill (`logo_spec.py`) | `spec.json` (`logo-sting-spec/v1`) + grouping preview | this Skill |
| timing | stroke count, film fps, optional beat grid from the host's score | this Skill (`sting_timing.py`) | `timing.json` (`logo-sting-timing/v1`) | this Skill; the host supplies fps and beats |
| sound | `timing.json` | this Skill (`sting_audio.py`) | `sting.wav` (48 kHz stereo) | this Skill |
| picture | spec + timing (+ wav) | this Skill (`LogoSting.tsx`, `render_sting.py`) | `<LogoSting>` Sequence in the host project, or `logo-sting-<aspect>.mp4` | this Skill: key frames, brand checks, duration |
| placement and mix | Sequence or clip + `sting.wav` | host video Skill | the finished film | host Skill: position, whole-film loudness and true peak after encoding |

With no host Skill, the user receives the clips directly and appends them in their editor; the whole-film
re-measurement in `integration.md` still applies.

## Overlap Decisions

- `motion-graphics` (HyperFrames) also lists "logo sting / brand lockup". It designs a new, brief-driven motion
  piece in HyperFrames HTML. This Skill reproduces one established, verified brand outro from the official SVG, with
  a synthesised sound locked to the same frames, as a Remotion component or a clip, deterministically. They stay
  separate: "our brand's logo ending / the sting from the last film" routes here; "a new logo animation in another
  style" or any HyperFrames request routes to `motion-graphics` / `hyperframes`.
- The downstream video Skills keep their own static logo endings as the fallback. They declare this Skill as an
  optional install preflight (`dependencies:`), not in `depends_on`, so they work without it.

## Composition Decision

Single Skill. The spec, timing, sound and picture stages serve one user-visible outcome (the logo ending) and share
one data contract; none of them is useful on its own to another Skill, so a Kit would only add routing. Sibling
Skills stay optional and exchange files only: official SVG → `spec.json` → `timing.json` → `sting.wav` → Sequence
or clip. No external Skill is required at runtime.
