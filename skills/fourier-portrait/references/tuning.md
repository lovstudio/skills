# Tuning the line art and timeline

Always iterate with `--stills-only` and look at `stills_sheet.jpg` and `lineart.png`.

## Line art

The ink map is an adaptive threshold: a pixel becomes ink when it is darker than its local
mean minus `--offset`. Contours of the ink blobs become the drawing path.

| Symptom | Change |
| --- | --- |
| Face reads as noisy blotches, too much ink | raise `--offset` (8 → 10–12) |
| Eyes, nostrils or mouth missing | lower `--offset` (8 → 6) |
| Many tiny specks in hair, fabric or a textured background | raise `--min-area` (60 → 100–150) |
| Lines too fragmented | raise `--blur` (2.0 → 2.5) |
| Features merge into large blobs | lower `--block` (35 → 25, keep it odd) |
| Bottom edge shows fragments of a shirt print or hands | tighten the crop, e.g. `--crop 0.05,0,0.9,0.62` |
| No face detected, or not on macOS | pass `--crop x0,y0,x1,y1` as fractions of the photo |

Auto crop: 1.6 face widths either side of the face centre, 0.9 face heights above the face
box, and 1.8 below it. Photos with a heavy colour cast are normalised by CLAHE; repeated
bilateral filtering removes printed halftone dots.

Path size: about 80–150 contours and 15–20 k px of total contour length at the 900 px work
size give a clean drawing. Much more than that needs more terms and looks busy.

## Fourier terms and timing

- `--stages` and `--stage-seconds` must have the same length. Each stage draws one full turn.
- Final error is usually under 0.5 % at N = 512 and about 0.2 % at N = 1024 (xy mode).
- Short version (about 25 s): `--stages 1,4,16,64,256,1024 --stage-seconds 1.6,2,2.6,3.4,4.4,5.4`.
- `--points` (default 8192) is the number of samples along the path. Keep it above 4 × the
  largest N.

## Modes

- `xy`: the reference look. In 9:16 the portrait takes about 40 % of the width, because the
  y chain needs horizontal room.
- `complex`: one chain over the drawing, and the portrait fills the width. The circle count
  for the same error is roughly twice that of xy (two real series of N terms ≈ 2N complex terms).

## Copy and branding

The title is the only authored text. Keep it to one line, at most about 14 CJK characters at
the default size. Use a light logo variant on the dark background.
