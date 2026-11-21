# Skill Group Composition

This record prevents adjacent Skills from becoming accidental duplicates or hidden
dependencies. Inspected 2026-11-21.

## Nearby Skills Inspected

| Skill | Routing contract | Relation |
| --- | --- | --- |
| `lov-media-crawler` | Downloads a known social-media link and verifies the media file | upstream atom (optional): fetches a reference clip the user wants to imitate |
| `lov-bw-portrait`, `lov-riso-portrait`, `lov-professional-portrait` | Redraw a photo into a styled still portrait with gpt-image-2 | not composed: they output stills from a generative model; this Skill needs a deterministic, identity-faithful line map, so it does its own local line art |
| `lov-algo-viz-creator` | Interactive single-file HTML that steps through an algorithm | overlap in topic only: it produces an interactive page, not a rendered video of a photo |
| `lov-media-creator` | Edits finished footage into publishable cuts with music, subtitles and covers | downstream atom (optional): takes the silent MP4 for music or for inclusion in a longer edit |
| `lov-media-publisher` | Publishes a local video to Channels, Bilibili or Xiaohongshu | downstream atom (optional), only on a separate publish request |
| `lov-branding-consistency` | Audience-visible copy gate | declared dependency for the on-screen title |

## Atomic Handoffs

- **Reference clip** (optional): link → `lov-media-crawler` → verified MP4 that this Skill
  uses only for visual comparison. `lov-media-crawler` owns download verification.
- **Core**: photo → `scripts/fourier_portrait.py` → silent 1080×1920 MP4 plus `report.json`
  and contact sheets. This Skill owns line-art quality, Fourier accuracy and safe areas.
- **Music and editing** (optional): silent MP4 → `lov-media-creator`. That Skill owns music
  selection and mixing; this Skill never synthesizes audio.
- **Publishing** (optional): finished MP4 → `lov-media-publisher` on an explicit request.

## Overlap Decisions

- Generative portrait Skills are not reused for the line art. Redrawing can change identity
  details, and the Fourier path must follow the user's actual features.
- No interactive web output is added; that remains `lov-algo-viz-creator`'s outcome.

## Composition Decision

Single Skill. Line art, path building, Fourier analysis and rendering always run together to
produce one outcome, and none of them is useful to users on its own. Adjacent Skills stay
optional and are connected only through files.
