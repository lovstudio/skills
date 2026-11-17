# Quality checks

Run these on every sting before it ships, and again on the film after it is appended (`integration.md`). Report the
numbers; a check that was not run is reported as not run.

## 1. Key frames

| moment | local frame | reference (30 fps, 3 strokes) | what to see |
| --- | --- | --- | --- |
| point | `0` | 0 | a small centred point of light on black (`intro="point"`), or black (`intro="black"`) |
| each stroke | `hits[i]` | 18, 36, 54 | the stroke slamming in whole: shake, RGB split, ghost trail, horizontal flare |
| suck-out | `bar - r(1)` | 71 | dark frame, the full mark alone, glow gone |
| negative | `bar` | 72 | one negative frame (light ground from `colors.hot`, dark lockup) |
| landing | `bar + r(8)` | 80 | full lockup, thin shockwave ring, sparks and embers |
| sweep | `bar + r(14)` | 86 | a light band crossing the lockup, clipped to the shapes |
| hold | `cut - r(20)` | 120 | the clean lockup, breathing glow |
| cut | `cut` | 140 | pure black |

`r(n)` is `n` frames at 30 fps expressed at the sting's fps (`round(n * fps / 30)`, half up). In a film, add the
sting's start frame `S`.

```bash
# W = work dir with timing.json; S = 0 for the standalone clip, the start frame for the whole film
python3 - "$W/timing.json" "$S" > "$W/keyframes.txt" <<'EOF'
import json, sys
t = json.load(open(sys.argv[1])); s = int(sys.argv[2]); r = lambda n: int(n * t["fps"] / 30 + 0.5)
fr = [0, *t["hits"], t["bar"] - r(1), t["bar"], t["bar"] + r(8), t["bar"] + r(14), t["cut"] - r(20), t["cut"]]
print("+".join(f"eq(n\\,{s + f})" for f in fr))
EOF
ffmpeg -v error -y -i sting.mp4 -vf "select='$(cat "$W/keyframes.txt")',scale=-2:480,tile=6x2" \
  -frames:v 1 "$W/sting-sheet.png"    # tile=6x3 for more than five strokes
```

Look at every tile (the last one is black):

- The logo is the official one, complete and undistorted, in the final lockup at the hold; strokes land in the
  intended order; the wordmark appears only from the bar.
- Nothing important is cut off at the hold. A stroke may touch the frame edge for one or two slam frames (the
  reference 16:9 cut does the same at frame 18); the final lockup must sit well inside the frame.
- For route A also check the frame before the sting: the hand-off into the point (or into black) shows no jump.

## 2. Brand safety

- **Official file**: `source_sha256` in `spec.json` equals the official file's hash.

```bash
shasum -a 256 "<official-logo.svg>"
python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['source_sha256'])" "$W/spec.json"
```

- **Shapes unedited**: regenerate the spec from the official file with the same flags and compare byte for byte. A
  difference means the spec was edited by hand or came from another file.

```bash
python3 "$SKILL_DIR/scripts/logo_spec.py" --svg "<official-logo.svg>" <same flags> --out "$W/spec-check.json"
cmp "$W/spec.json" "$W/spec-check.json" && echo spec-unchanged
```

- **Colours**: `colors.final` is the logo's colour on a dark ground as the brand uses it; `accent` is the brand's
  accent, not a guess.
- **No rising-sun composition**: no disc with radiating lines anywhere, in red/white or any other palette. The
  component keeps inbound streaks, sparks and flashes horizontally biased and draws only thin shockwave rings as
  round elements; the host's hand-off scene must follow the same rule. Check the sheet (and a 5 fps sheet of the
  last seconds of the film when the hand-off is custom).

## 3. Sound

- `sting.wav`: 48 kHz, stereo, 16-bit, exactly `round(dur / fps * 48000)` samples; peak about −1 dBTP.
- The film after the sting is added: integrated loudness on target, true peak at or below the delivery target on
  the final encoded file (`ebur128=peak=true`). See `integration.md` for the reference lesson (−2.5 dBTP master
  target with a 0.70 limiter after the AAC file went above 0 dBFS).
- Listen once: each hit on its stroke, the gate goes quiet with the picture's suck-out, the big hit on the
  negative frame, nothing after the cut.

## 4. Duration and frame rate

- Standalone clip: `render_sting.py` checks H.264 yuv420p at the aspect's size, `dur` frames, `dur / fps` seconds,
  one AAC 48 kHz stream when `--audio` is given, and bt709 tags (added with `ffmpeg -c copy` when missing); a failed
  check exits non-zero and keeps the work dir.
- Route A: the composition fps equals `timing.fps`, the Sequence starts at the intended frame, lasts `timing.dur`
  frames, and the composition ends with it.
- Route B: the appended film's frame count is the film's plus `dur`, and audio and video lengths agree (allow the
  ≤ 20 ms AAC tail noted in `integration.md` when the sting is last).

## Reference results (0.1.0)

Verification run while building the skill against the reference film 《如何用 AI 制作视频》 v0.2 (sting = film frames
7532–7675 of 7676, 30 fps):

- **Logo spec**: from the official 手工川 white horizontal SVG (byte-identical to the file the film used, sha256
  `0e3fe649…7753fe`) with `--accent '#DB7759' --hot '#FFC9AE'`: 3 strokes + 3 wordmark paths, all six `d` strings
  byte-identical to the SVG. Exact Bézier/arc bounding boxes agreed with dense sampling on 46 paths (worst 2.9e-05).
- **Timing**: 30 fps / 100 bpm / 3 strokes gives hits 18 36 54, bar 72, pulses 90 108 126, dur 144, cut 140,
  gate 69; the film's own beat grid via `--beats` gives an identical file.
- **Sound**: `sting.wav` from that timing is byte-identical to the film's sting WAV, header included (`cmp`), and
  deterministic across runs. Measured −13.9 LUFS integrated, LRA 0.7 LU, true peak −1.0 dBFS.
- **Picture**: standalone 9:16 and 16:9 renders against the delivered films, frame by frame: mean Y-PSNR 53.6 /
  53.3 dB over the 140 frames before the cut (the 4 black frames are identical, PSNR ∞), minimum 40.8 / 40.0 dB at
  frame 72 (the negative frame). That frame's gap comes from the delivered film's
  colour tagging (its master was re-tagged bt709 without conversion, which shifts light warm colours) plus the film's
  overlay grain and second encode; against the film master the same frame is 44.4 dB with ground samples within
  1–2 levels. Offsets ±1 frame drop to about 40 dB, so the alignment is exact.
- **Rates and logos**: a 60 fps timing renders 288 frames whose even frames match the 30 fps render at 55.1 dB mean
  (46.3 dB minimum). LovPen (white), a mark-only spec, a two-stroke even-odd SVG (hole kept open in every layer) and
  1:1 / 4:3 aspects were rendered and checked on contact sheets.
- **Host integration**: a Remotion host importing the JSON directly passed `tsc --noEmit` (strict) and rendered; the
  sting part matched the standalone render at 49.1 dB mean / 42.7 dB minimum PSNR (two independent encodes).
  Appending a clip with the FFmpeg concat filter gave the expected 234 frames / 7.800 s. Mixing `sting.wav` into a
  pre-master mix with `adelay=…S` was sample-exact.
- **In the film**: the reference report's 5 fps contact sheet of the last three sections found no disc-with-rays
  composition; after the sting was added the film was re-mastered to −16.0 LUFS / −2.8 dBTP.
