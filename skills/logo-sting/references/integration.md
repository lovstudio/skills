# Integration

How to put the sting at the end of a film. Route A is a Remotion host project; route B is any other pipeline
(FFmpeg, 剪映/CapCut, Premiere, DaVinci). The data contract is `spec-contract.md`; the checks are in `qc.md`.

Files, wherever they end up:

| file | made by | route A | route B |
| --- | --- | --- | --- |
| `spec.json` | `scripts/logo_spec.py` | `src/data/logo-sting-spec.json` | input of `render_sting.py` |
| `timing.json` | `scripts/sting_timing.py` | `src/data/logo-sting-timing.json` | input of `render_sting.py` |
| `sting.wav` | `scripts/sting_audio.py` | `public/sfx/logo-sting.wav`, or into the host's pre-master mix | input of `render_sting.py` |
| `LogoSting.tsx` | `assets/remotion/` | `src/` (any folder) | copied by `render_sting.py` |
| `logo-sting-<aspect>.mp4` | `scripts/render_sting.py` | not needed | appended to the film |

## Beat sync

Beat `k` of the default grid is `round(k * fps * 60 / bpm)` (half up). With `N` strokes the strokes land on beats
`1..N`, the wordmark on beat `N+1` (`bar`), the breathing pulses on the next three beats before the cut, and the
sting ends on beat `N+5` (`dur`). `gate = bar - round(3 fps / 30)` starts the suck-out; `cut = dur - round(4 fps / 30)`
is the hard cut to black.

| input | hits | bar | pulses | dur | cut | gate |
| --- | --- | --- | --- | --- | --- | --- |
| 30 fps, 100 bpm, N 3 (reference) | 18 36 54 | 72 | 90 108 126 | 144 | 140 | 69 |
| 25 fps, 120 bpm, N 3 | 13 25 38 | 50 | 63 75 88 | 100 | 97 | 47 |
| 60 fps, 100 bpm, N 2 | 36 72 | 108 | 144 180 216 | 252 | 244 | 102 |
| 30 fps, `--beats 0,18,36,72,90,108,126 --dur 144`, N 2 | 18 36 | 72 | 90 108 126 | 144 | 140 | 69 |

- **Standalone** (no score under the ending): `--fps <film fps>`, keep `--bpm 100` unless the film has a tempo of
  its own. A tempo too fast for the suck-out is refused; lower `--bpm`.
- **On the film's score**: take the score's beat grid (from the music analysis or the edit's beat map), keep the
  beats at or after the sting's first frame `S`, subtract `S`, and pass them as `--beats` (the first must be `0`, so
  the sting starts on a beat). Give at least `N + 6` beats, or `N + 2` plus `--dur`.
- **Wordmark on the bar line**: with three strokes in 4/4, beat `N+1 = 4` is the next downbeat. With another
  stroke count, `--beats` may skip beats (any strictly increasing list is accepted), e.g. two strokes in 4/4:
  `0,18,36,72,…` puts the wordmark on the downbeat at 72 (tested: renders and sounds as expected).
- **Where the score stops**: cut the score so it ends exactly on the bar line where the sting starts, and leave
  nothing under the sting; the sting's own sound carries the end. The reference film edited its score to whole bars,
  put the logo card on a bar line and kept the music silent under it.

## Route A: Remotion host

1. Copy `assets/remotion/LogoSting.tsx` into the host's `src/`. It imports only `react` and `remotion` (tested with
   Remotion 4.0.534, React 19.1.0, TypeScript 5.8.3 strict).
2. Put `spec.json` and `timing.json` in `src/data/` and enable `"resolveJsonModule": true` in `tsconfig.json`. The
   exported types accept the JSON as imported, no cast needed.
3. Put `sting.wav` in `public/` (for the direct-audio mode below).
4. Mount the sting as the last Sequence. The composition's fps must equal `timing.fps`; its length is
   `start + timing.dur`.

```tsx
import {LogoSting} from './LogoSting';
import spec from './data/logo-sting-spec.json';
import timing from './data/logo-sting-timing.json';

// inside the film component; START = first frame of the sting in the film
<Sequence from={START} durationInFrames={timing.dur}>
  <LogoSting spec={spec} timing={timing} audioSrc="sfx/logo-sting.wav" />
</Sequence>
```

This exact pattern (a 60-frame scene collapsing to a point, then the sting at frame 60, 1080×1920, 30 fps) passed
`tsc --noEmit` and rendered 204 frames; the sting part matched the standalone render at 49.1 dB mean / 42.7 dB
minimum Y/U/V PSNR, which is the spread of two independent CRF 16 encodes.

### Sound: direct or in the host's final mix

- **Direct**: pass `audioSrc` (a path under `public/` or a URL). The component plays `sting.wav` from frame 0 to
  `dur` at `gain` (default 0.95) with a 1-frame fade-in and a fade-out over the black frames.
- **Host with one final mix** (stems rendered, mixed and mastered outside Remotion, then one master WAV mounted in
  the composition): do not pass `audioSrc`. Mix `sting.wav` into the pre-master mix at the sting's start, sample
  exact, at 0.95, then master. At 48 kHz the offset is `round(START / fps * 48000)` samples (1600 per frame at 30 fps):

```bash
# START = 60 frames at 30 fps -> 96000 samples; the pre-master mix must already run to the film's end
ffmpeg -i mix-pre.wav -i sting.wav -filter_complex \
  "[1:a]volume=0.95,adelay=96000S:all=1[s];[0:a][s]amix=inputs=2:duration=longest:normalize=0[a]" \
  -map "[a]" -c:a pcm_s24le mix-pre-with-sting.wav
```

  Tested: the result is sample-exact (`0.95 × sting` from sample 96000, max error 0.0 in float).

### Intro: point or black

- `intro="point"` (default): frame 0 is a centred point of light (at a 1080-px short side: about a 6 px white core,
  a 58 px white glow and a short white horizontal flare on black) that grows warm, then implodes into the first
  stroke. Use it when the previous scene ends by collapsing to a point at the frame centre on black: scale the last
  scene's content down to that point over its final frames so the cut is invisible.
- `intro="black"`: frames `0 .. hits[0] - 1` are pure black and the sound's swell carries that beat. Use it after a
  fade to black or any scene that does not end on a centred point.

## Route B: other pipelines

```bash
python3 "$SKILL_DIR/scripts/render_sting.py" --spec spec.json --timing timing.json --audio sting.wav \
  --aspect 9x16,16x9 --out clips/ [--node-modules <existing remotion 4.0.534 node_modules>] [--intro black]
```

- Output per aspect: `clips/logo-sting-<aspect>.mp4`, H.264 CRF 16 yuv420p, AAC 320 kb/s 48 kHz stereo, tagged
  bt709, `dur` frames at `timing.fps`; the script refuses an output inside the skill dir and checks each file with
  ffprobe. Two aspects take about 17 s on an Apple Silicon Mac with an existing install.
- Without `--node-modules` the first run does `npm install` once into `~/.cache/lov-logo-sting/remotion-4.0.534`
  (network), later runs reuse it.
- Pick the aspect of the film; for another size with the same aspect ratio, scale in the concat filter below.

### Append with FFmpeg (one re-encode)

Use the concat **filter**, not the concat demuxer with `-c copy`: the two parts come from different encoders, and
one re-encode from the film's master (not from a platform-compressed upload copy) keeps quality and timing clean.

```bash
ffmpeg -i film-master.mp4 -i clips/logo-sting-9x16.mp4 -filter_complex \
"[0:v]fps=30,format=yuv420p,setsar=1[v0];[1:v]fps=30,format=yuv420p,setsar=1[v1];\
[0:a]aresample=48000,aformat=channel_layouts=stereo[a0];[1:a]aresample=48000,aformat=channel_layouts=stereo[a1];\
[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
  -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart film-with-sting.mp4
```

Tested on a 3 s 1080×1920 host clip: 90 + 144 = 234 frames, 7.800 s video and audio. Replace `fps=30` with the
film's rate (the timing must use the same fps), and add `scale=W:H` to `[1:v]` when the film is not 1080/1920 px.
At some frame rates Remotion's AAC runs up to about 20 ms past the last frame (60 fps: 4.821 s audio for 4.800 s
video); with the sting last this is harmless, otherwise trim it with `atrim=end=<dur/fps>` on `[1:a]`.

剪映/CapCut and other editors: import the MP4, put it right after the last frame of the film on the timeline,
no transition (the sting starts and ends on its own), then re-measure as below.

## Mixing and loudness

- `sting.wav` is normalised to −1 dBTP; measured −13.9 LUFS integrated, LRA 0.7 LU. The rendered clip (gain 0.95,
  AAC) measured −14.5 LUFS, −1.6 dBTP.
- In the reference film the sting's loudest short-term moment sits about 3.5 LU above the score's loudest bars
  (sting at gain 0.95: −13.15 LUFS short-term; the score's loudest bars at the music level used between narration
  lines: −16.6; ebur128 short-term, before mastering). Keep that relation: the sting may be a little louder than the
  music it ends, not a jump. Adjust `--gain` (route B) or the mix gain (route A), not the WAV.
- **Always re-measure the whole film after adding the sting**, on the final encoded file:

```bash
ffmpeg -nostdin -hide_banner -i film-with-sting.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^ +(I|LRA|Peak):"
```

  The sting's transients survive mastering and grow in AAC encoding. In the reference film the encoded file's true
  peak went above 0 dBFS after the sting was added; the master target was lowered to −2.5 dBTP with a limiter at
  0.70 (FFmpeg `loudnorm=I=-16:TP=-2.5:LRA=11` two-pass, then `alimiter=limit=0.70`) and the film re-mixed, ending at
  −16.0 LUFS / −2.8 dBTP. If the measured true peak is above the delivery target, lower the master's true-peak target
  or limiter and re-master; do not clip or re-normalise the sting on its own.
- Ownership: the sting's picture, sound and timing belong to this Skill; where it sits in the film, the film's mix,
  loudness and true-peak acceptance belong to the host's video Skill.
