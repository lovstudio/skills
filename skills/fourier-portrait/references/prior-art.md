# Prior art: how "rotating circles draw a portrait" videos are made

Researched 2026-11-21 from a WeChat Channels clip titled 神奇的傅里叶：无数旋转圆环，可以画出任意轮廓
(33 s, 720×1280). Use this file when the user asks what framework such a video uses.

## What the reference clip shows

- Target: a binarized engraving of Joseph Fourier, traced as one closed line.
- Two epicycle chains. A teal chain above the drawing produces x(t); a gold chain to its left
  produces y(t). Dashed lines project each chain tip onto the pen.
- Labels: N = 1, 2, 4, 8, 24, 48, 96, 192, 384 with an error that falls from 47 % to 0.77 %.
- Closing card: x(t) = Σ a_k cos kt + b_k sin kt, y(t) = Σ c_k cos kt + d_k sin kt,
  r_k ~ k^-1.45.
- Computer Modern math type and a warm black background suggest manim or a LaTeX-based
  renderer. The white title bar was added by the uploader in an editor. The clip's own source
  code is not published, so the exact tool cannot be confirmed.

## The technique (no special framework needed)

1. Turn the image into one closed path: edge or threshold the image, collect contours,
   join them into a single loop, then resample the loop uniformly by arc length.
2. Take the discrete Fourier transform of the samples:
   - **Two real series**: FFT of x[n] and y[n] separately. Each harmonic is one rotating
     vector; the x chain uses its horizontal component and the y chain is rotated 90°.
   - **One complex series**: FFT of z[n] = x[n] + i·y[n]. Each coefficient is one circle,
     and the chain tip is the pen.
3. Sort terms by amplitude and keep the largest N. Animate t from 0 to 2π, drawing the
   circles and the trail.

## Open-source references

| Project | What it offers | License |
| --- | --- | --- |
| [3b1b/videos](https://github.com/3b1b/videos), `_2019/diffyq/part2/fourier_series.py` | The original 3Blue1Brown Fourier series scenes, made with manim; complex single-chain style | not stated (NOASSERTION) |
| [CodingTrain/Coding-Challenges](https://github.com/CodingTrain/Coding-Challenges) `130_Fourier_Transform_1/2/3` | p5.js DFT drawing. #130.1 uses the separate x/y chains seen in the reference clip | MIT |
| [taibeled/manim-fourier-series](https://github.com/taibeled/manim-fourier-series) | manim plugin that turns a closed path into rotating vectors | GPL-3.0 |
| [Grzetan/ImageToFourierSeries](https://github.com/Grzetan/ImageToFourierSeries) | Image → Canny edges → ordered points → DFT → epicycles | GPL-3.0 |
| [carolineec/informative-drawings](https://github.com/carolineec/informative-drawings) | Learned photo → line drawing model (CVPR 2022), an alternative line-art stage | MIT |

## What this Skill uses and why

- **Line art**: Apple Vision subject mask and face box, then CLAHE, bilateral filtering and
  adaptive threshold. It runs on the CPU in under a second, needs no model download, and
  removes print halftone. Its stencil look matches the engraving in the reference.
- **Path**: contours joined along a minimum spanning tree and toured depth first. Each
  connector is walked out and back, so no long diagonal crosses the face.
- **Fourier**: numpy FFT, both the xy and complex decompositions.
- **Render**: skia raster frames piped straight into ffmpeg; Computer Modern formulas via
  matplotlib mathtext, with no LaTeX install. A 39 s 1080×1920 video renders in about 15 s.

manim would give the same look but needs a LaTeX toolchain and is slower for thousands of
circles per frame. It remains the right choice when the animation must be combined with other
manim scenes.
