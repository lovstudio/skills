---
name: lov-video-chapter-render
description: Render a chapter project as a transparent ProRes 4444 overlay or burn it into the source video with FFmpeg. Use when the user asks to generate, export, render, encode, or press a chapter progress bar into video.
---

# Chapter Render

1. Validate the project JSON.
2. Confirm `ffmpeg`, `ffprobe`, and Python Pillow are available.
3. Run `../../scripts/render_chapter_bar.py overlay` for an alpha MOV.
4. Inspect the output pixel format and duration with `ffprobe`.
5. Run `../../scripts/render_chapter_bar.py burn` for a final MP4.
6. Confirm the final MP4 keeps audio and matches the source dimensions.

Render the progress fill continuously across duration-proportional segments.
Keep title plates chapter-specific and use the font file from project style when
provided.

