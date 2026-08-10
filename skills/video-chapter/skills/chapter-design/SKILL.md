---
name: sgc-video-chapter-design
description: Refine chapter boundaries, titles, colors, typography, placement, and progress behavior in the bundled React video chapter editor. Use when the user wants to preview, debug, beautify, or customize a video chapter progress bar.
---

# Chapter Design

1. Open `../../studio` and run `npm install`, then `npm run dev`.
2. Import the canonical `chapter-project.json`.
3. Select the source video locally for browser preview.
4. Keep chapter widths proportional to duration.
5. Edit timestamps without creating overlaps or gaps.
6. Use the segmented splice rail as the primary editing surface.
7. Export the updated project JSON after visual approval.
8. Validate with `../../scripts/chapter_project.py validate`.

Use a restrained edit-bay visual language: precise timecode typography,
high-contrast controls, one signal color, and a clearly visible playhead. Keep
the chapter overlay readable at the final delivery resolution.

