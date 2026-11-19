# Changelog

## 0.1.0

- Port the video2ppt desktop pipeline (ffmpeg sampling, 16-bin RGB histogram
  intersection, timestamp overlay) to a standalone Python CLI.
- Add PPTX export with timestamp notes, a contact sheet and `manifest.json`.
- Add `--method pixel`, `--crop`, `--settle` and `--min-duration` for talks with
  speaker insets, subtitles and crossfades; defaults keep desktop behaviour.
- Add `pack` to drop or add slides after review and rebuild every output.
