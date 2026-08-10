---
name: sgc-video-chapter
description: Turn SRT/VTT subtitles and source videos into 3–5 semantic chapters, an editable React chapter-bar project, a transparent ProRes overlay, a burned-in MP4, and editor-ready packages. Use for subtitle chaptering, video segmentation, chapter progress bars, 剪映/CapCut chapter overlays, video chapter rendering, or requests such as “基于字幕进行视频分段”, “生成章节进度条”, “把章节条压进视频”, and “create video chapters from subtitles”.
---

# Video Chapter Skill Kit

Build a complete chapter-bar workflow from semantic planning to final video.
Keep every stage connected through one `chapter-project.json`.

## Route the request

- Read `skills/chapter-plan/SKILL.md` for subtitle analysis and editorial cuts.
- Read `skills/chapter-design/SKILL.md` for React Studio editing and styling.
- Read `skills/chapter-render/SKILL.md` for transparent overlay or burned video.
- Read `skills/chapter-export/SKILL.md` for 剪映/CapCut and other editor packages.
- Run only the stages the user requests. Run all four for an end-to-end request.

## End-to-end workflow

### 1. Analyze the subtitles

```bash
python3 scripts/subtitle_chapters.py \
  --input "/path/to/subtitles.srt" \
  --segments 5 \
  --output "/tmp/video-chapter-analysis.md"
```

Read the analysis pack completely. Select semantic transitions rather than
equal-duration cuts. Start at `00:00`, align later cuts to subtitle cues, and
avoid cutting a sentence.

### 2. Create the project

Write a UTF-8 chapter list:

```text
00:00 开场与目标 | 展示成片并说明这次要完成什么
04:16 挑选并改造 Skill | 判断现有工具并完成适配
```

Create the canonical project:

```bash
python3 scripts/chapter_project.py create \
  --chapters "/path/to/chapters.txt" \
  --video "/path/to/video.mp4" \
  --output "/path/to/chapter-project.json"
```

Read `references/project-format.md` when editing project JSON directly.

### 3. Refine in React Studio

```bash
cd studio
npm install
npm run dev
```

Import `chapter-project.json`, select the local source video, edit chapter
boundaries and titles, adjust styling, then export the updated JSON. Treat the
Studio preview as the visual approval surface.

### 4. Render

Install Pillow once when needed:

```bash
python3 -m pip install -r requirements.txt
```

Create a transparent overlay:

```bash
python3 scripts/render_chapter_bar.py overlay \
  --project "/path/to/chapter-project.json" \
  --output "/path/to/chapter-overlay.mov"
```

Burn the overlay into the source video:

```bash
python3 scripts/render_chapter_bar.py burn \
  --project "/path/to/chapter-project.json" \
  --output "/path/to/video-with-chapters.mp4"
```

Create a 剪映-ready package:

```bash
python3 scripts/render_chapter_bar.py package \
  --project "/path/to/chapter-project.json" \
  --output "/path/to/chapter-package"
```

## Validation

Run before delivery:

```bash
python3 scripts/chapter_project.py validate \
  --project "/path/to/chapter-project.json"
```

Confirm:

- chapters are chronological and contiguous;
- the final chapter ends at the project duration;
- titles match the following content;
- the Studio preview matches the requested visual direction;
- the overlay contains an alpha channel;
- the burned MP4 preserves source audio;
- the editor package contains JSON, timestamps, CSV, overlay, and instructions.

## Output policy

- Prefer a transparent ProRes 4444 MOV for 剪映/CapCut.
- Use burned MP4 when the user wants a final publishable file.
- Describe transparent-video import as asset integration.
- Keep editor-specific draft writers in an experimental adapter layer.
- Preserve explicit paths; never assume a private workspace.
