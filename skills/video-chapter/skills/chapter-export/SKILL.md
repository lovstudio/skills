---
name: lov-video-chapter-export
description: Package chapter overlays, timestamps, CSV metadata, and project JSON for 剪映/CapCut and other video editors. Use when the user asks for editor integration, transferable chapter assets, or a ready-to-import chapter package.
---

# Chapter Export

Run:

```bash
python3 ../../scripts/render_chapter_bar.py package \
  --project "/path/to/chapter-project.json" \
  --output "/path/to/chapter-package"
```

For 剪映/CapCut:

1. Import `chapter-overlay.mov`.
2. Place it on the top video track at `00:00`.
3. Keep scaling at 100% and match the project frame rate.
4. Trim only the tail when the editor rounds duration.

Use `chapters.txt` for platform chapter fields and `chapters.csv` for editor
automation. Treat direct draft-file writing as an experimental adapter because
editor project formats can change independently.

