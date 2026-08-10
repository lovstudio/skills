---
name: sgc-video-chapter-plan
description: Analyze timestamped SRT/VTT subtitles and determine 3–5 natural video chapters with cue-aligned cuts, concrete titles, summaries, and platform-ready timestamps. Use when the user asks to segment a long video from subtitles or decide chapter content.
---

# Chapter Plan

1. Run `../../scripts/subtitle_chapters.py` to build the analysis pack.
2. Read every transcript window and meaningful gap.
3. Select boundaries by topic transition, completed sentence, supporting pause,
   then duration balance.
4. Start at `00:00`; align every later start to a real subtitle cue.
5. Name each chapter with a concrete 8–18 character Chinese title or an equally
   concise title in the source language.
6. Write one grounded sentence of summary per chapter.
7. List dead air, loading failures, repeated takes, and troubleshooting detours
   as optional trims rather than chapters.
8. Create the project with `../../scripts/chapter_project.py create`.

Default to 5 chapters above 20 minutes, 4 chapters for 8–20 minutes, and 3
chapters below 8 minutes unless the content strongly supports another requested
count.

