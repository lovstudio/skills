# Data contract

Three files drive one sting: the logo spec, the timing, and the sound. The picture (Remotion component) and the
sound (synthesised WAV) both read the same timing file, so every hit lands on the same frame in both.

All coordinates in the logo spec are in the SVG's own user units. Frames in the timing file are local to the
first frame of the sting (frame 0 = the first frame of the sting clip or Sequence).

## Logo spec — `logo-sting-spec/v1`

Produced by `scripts/logo_spec.py` from an official logo SVG. Path data is copied verbatim; shapes are only ever
moved or scaled as whole shapes by the component, never redrawn or edited.

```json
{
  "schema": "logo-sting-spec/v1",
  "source": "logo-white.svg",
  "source_sha256": "<sha256 of the SVG file>",
  "viewBox": [80, 20, 320, 110],
  "mark": [
    {"d": "M92.2 31.4v56.7…Z", "box": [92.2, 31.4, 118.4, 114.3], "c": [105.3, 72.85]}
  ],
  "word": [
    {"d": "M270.1 85.2v7.1…Z", "box": [221.8, 57.8, 270.1, 106.6]}
  ],
  "markBox": [92.2, 31.4, 183.8, 131.8],
  "wordBox": [221.8, 57.8, 378.2, 106.6],
  "logoBox": [92.2, 31.4, 378.2, 131.8],
  "colors": {"final": "#FFFFFF", "accent": "#DB7759", "hot": "#FFC9AE", "background": "#000000"}
}
```

- `box` is `[x0, y0, x1, y1]` (exact: Bézier and arc extrema solved); `c` is the box centre.
- `d` is the attribute value as an XML parser reads it (line breaks inside the attribute become spaces).
- An entry carries `"rule": "evenodd"` when its SVG fill rule is evenodd (common in Figma exports); render it with
  `fillRule="evenodd"`, and with `clipRule="evenodd"` where the path sits inside a `<clipPath>` (clipping ignores
  `fill-rule`). Without `rule` the fill rule is nonzero.
- `mark` lists the shapes that slam in one per beat, in hit order (document order unless `--order` says otherwise).
  At least one entry. When several paths form one stroke (a mark side of more than 6 paths, grouped by overlapping
  boxes, or `--order 0+1`), `d` holds their path data joined by a space, a leading relative `m` spelled absolute;
  `logo_spec.py` refuses to join paths whose winding direction or fill rule differ, since that could cut holes.
- `word` is the rest of the lockup (wordmark, tagline) that lands together on the bar. It may be empty: then the
  lock-up is the mark alone and `wordBox` is `null`.
- `colors.final` is the logo's resting colour; `accent` drives glows, flares, sparks and rings; `hot` is the
  accent lifted toward white for the hottest light. `background` stays black unless the brand needs otherwise.
  Defaults: `final` `#FFFFFF`; `accent` the first coloured (not white, black or grey) fill in the SVG — visible
  shapes first, then any other fill or `<style>` rule — and `--accent` is required when there is none; `hot` the
  accent mixed 60 % toward white. The example shows the reference film's colours, passed with `--accent`/`--hot`.
- Transforms on `<g>`/`<path>` (translate, scale, matrix) are baked into the coordinates by rewriting path data
  only when the transform is a pure translate or uniform scale; anything else is rejected with a clear error.
- Also rejected with the reason: non-path shapes (`rect`, `polygon`, live `text`, `use`, `image` …), clip paths and
  masks, stroke-only paths, and badge / knock-out lockups (shapes of one colour drawn over a shape of another, which
  would merge into a solid block in one colour). Paths entirely outside the viewBox are not rendered and are dropped.
- `--preview preview.svg` also writes a quick-look SVG of the grouping (mark strokes in distinct hues numbered in hit
  order, word in grey, black ground); it does not change the spec. A symbol-only logo split by a wide internal gap
  shows up here as strokes drawn grey: rerun with `--mark N` (N = all paths) or `--order`.

## Timing — `logo-sting-timing/v1`

Produced by `scripts/sting_timing.py`. All values are integer frames local to the sting.

```json
{
  "schema": "logo-sting-timing/v1",
  "fps": 30,
  "beat": 18,
  "hits": [18, 36, 54],
  "bar": 72,
  "pulses": [90, 108, 126],
  "dur": 144,
  "cut": 140,
  "gate": 69
}
```

- Default grid from `--fps` and `--bpm` (default 100): beat `k` sits at `round(k * fps * 60 / bpm)`.
  `hits` are beats `1..N` (`N = len(spec.mark)`), `bar` is beat `N+1`, `pulses` are the next three beats (those
  before `cut`), `dur` is beat `N+5`. `round` is half up.
- `--beats 0,18,36,…` takes beat frames from a host project's own score grid instead (frames local to the sting
  start, so the first is 0); the same index rule applies, `--dur` may override the end.
- `beat` is the nominal beat length in frames: `round(fps * 60 / bpm)`, or the median beat interval with `--beats`.
- `cut = dur - round(4 * fps / 30)` (hard cut to black before the end); `gate = bar - round(3 * fps / 30)`
  (the suck-out: picture and sound both go nearly dark from here to the bar).
- With fps 30, bpm 100 and a three-stroke mark this reproduces the reference sting exactly:
  hits 18 36 54, bar 72, pulses 90 108 126, dur 144, cut 140, gate 69.

## Sound — `sting.wav`

Produced by `scripts/sting_audio.py --timing timing.json --out sting.wav`: 48 kHz stereo 16-bit PCM, exactly
`round(dur / fps * 48000)` samples, deterministic (fixed seeds), true peak normalised to −1 dBTP. With the
reference timing it is sample-identical to the reference sting. N strokes: metal hits rise D4 A4 D5 then A5 D6 …,
pans spread evenly across ±0.32, stroke levels cycle. Frame offsets designed at 30 fps (the margin between the
last stroke's reverse swell and `gate`, the fade at `cut`) are scaled by `fps / 30`, so they keep their duration.

## Component — `assets/remotion/LogoSting.tsx`

Self-contained (imports only `react` and `remotion`). The exported types (`LogoStingSpec`, `LogoStingTiming`,
`LogoStingProps`) take boxes and points as `number[]` and `rule` as a string, so the spec and timing JSON can be
imported and passed as they are (`import spec from './data/logo-sting-spec.json'`, with `resolveJsonModule`). Props:

| prop | type | meaning |
| --- | --- | --- |
| `spec` | logo spec object | required |
| `timing` | timing object | required; its `dur` is the Sequence length |
| `audioSrc` | string, optional | path under `public/` (via `staticFile`) or URL of `sting.wav`; omitted = silent picture |
| `gain` | number, default 0.95 | sting gain inside the host mix |
| `intro` | `"point"` (default) or `"black"` | start from a centred point of light (hand-off from a scene that collapses to a point) or from black |

Layout adapts to the composition (`useVideoConfig`): portrait, landscape and square (width and height within 5 %).
Sizes that were tuned in pixels for a 1080-px short side scale by `min(width, height) / 1080`, so 1080×1920 and
1920×1080 render exactly like the reference.

- Final lockup: as wide as 700/1080 of the frame width in portrait, 840/1920 in landscape, 0.6 in square, but never
  taller than 30 % of the short side (a mark-only or tall lockup).
- Build (mark alone): the mark as wide on screen as the reference mark (≈ 0.394 / 0.399 / 0.396 of the short side in
  portrait / landscape / square), never taller than 55 % of the short side. The slam frames may overflow the frame
  edge for an instant, as in the reference 16:9 cut.
- Logo-unit offsets (stroke slam directions, light-sweep band, the bar's spark band) scale with `logoBox` height
  / 100.4. Stroke intensities (shake, RGB split, ring, sparks, streak) ramp from the first to the last stroke; with
  three strokes they are the reference values.
- Picture timing uses `hits`, `bar`, `pulses`, `gate` (start of the suck-out), `cut` (`dur − cut` black frames) and
  `dur`; animation durations designed at 30 fps scale by `fps / 30`, so other frame rates keep the same seconds.
  `hits` must have one frame per `mark` entry.
- `colors.final` fills the resting logo; `accent` and `hot` drive every glow, flare, ring, spark and ember;
  `background` is the ground and the vignette. Pure white stays white light (cores, streak centres, sparks). The
  negative frame's ground is derived from `hot` (its hue at ≤ 40 % saturation, lightness 85 / 80 / 64.5 %).
- The audio is a `<Sequence><Audio/></Sequence>` from frame 0 to `dur` with a 1-frame fade-in and a fade-out over
  the `dur − cut` black frames, times `gain`; only when `audioSrc` is given.

## Standalone render

`scripts/render_sting.py --spec spec.json --timing timing.json --audio sting.wav --aspect 9x16 --out sting.mp4`
renders the sting as its own clip (H.264 CRF 16 yuv420p + AAC 320 kb/s 48 kHz, tagged bt709) from
`assets/remotion-template/`, for pipelines that are not Remotion (FFmpeg concat, 剪映 import). Aspects: `9x16`
1080×1920, `16x9` 1920×1080, `1x1` 1080×1080, `4x3` 1440×1080 (repeat `--aspect` or give a comma list; `--out` is a
file for one aspect, `<stem>-<aspect>.mp4` for several, or a directory of `logo-sting-<aspect>.mp4`). Optional:
`--intro black`, `--gain`, `--crf`, `--work-dir`, `--keep-work-dir`.

- The template is copied with `LogoSting.tsx` into a work dir (default: a new dir under the system temp dir, removed
  after success); nothing is written inside the skill dir.
- `--node-modules DIR` reuses an existing Remotion 4.0.534 install read-only: the work dir gets its own
  `node_modules` of links into `DIR`, without `.cache` and `.remotion`, and a headless browser already downloaded
  in `DIR/.remotion` is passed with `--browser-executable`. Without it, `npm install` runs once into
  `~/.cache/lov-logo-sting/remotion-4.0.534` (or `$XDG_CACHE_HOME/...`) and the work dir links to that.
- Each output is checked with ffprobe: h264 at the aspect's size, `dur` frames, `dur / fps` seconds, one AAC
  48 kHz stream when `--audio` is given (none otherwise), bt709 tags (added with `ffmpeg -c copy` if missing).
