# Changelog

## 0.1.0 — 2026-11-21

- Photo → line art: Apple Vision subject mask and face-based bust crop (macOS), CLAHE,
  bilateral halftone removal, adaptive threshold and speck cleanup.
- Line art → one closed path: contours joined along a minimum spanning tree with
  out-and-back connectors, uniform arc-length resampling.
- Fourier analysis in two modes: two real series (x and y chains) or one complex series.
- skia renderer piped into ffmpeg: 1080×1920 vertical video with photo intro, staged N passes,
  error labels, reveal with Computer Modern formulas and a fitted `r_k ~ k^-p`, title and logo,
  platform safe areas.
- QC stills, contact sheets and `report.json`.
