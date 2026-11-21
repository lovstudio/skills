---
name: lov-fourier-portrait
description: >
  把一张人像照片做成傅里叶本轮绘图竖版视频：自动抠图出线稿，旋转圆逐级画出轮廓并显示误差与公式。
  Use when 用户说“用傅里叶画出我的照片”或 “turn my selfie into a Fourier epicycle video”。
license: MIT
compatibility: "Portable Agent Skills format. Requires uv (or Python 3.10+ with numpy, opencv-python-headless, scipy, skia-python, matplotlib) and ffmpeg/ffprobe. macOS 14+ with Swift adds on-device subject segmentation and face crop; other systems fall back to the full frame."
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - fourier-series
    - epicycles
    - math-animation
    - portrait
    - line-art
    - vertical-video
---

# 傅里叶画像 · Fourier Portrait

把一张人像照片变成一条竖版短视频：照片先溶解成线稿，再由一串旋转的圆（傅里叶本轮）
沿着线稿把整张脸一笔画出来；圆的数量 N 从 1 逐级加到 1024，画面同步显示重建误差，
最后揭晓完整线稿与级数公式。全程是真实计算，不是描摹动画。

## Triggers

### Activate when

- 用户说“用傅里叶级数画出我的照片”“把这张自拍做成旋转圆画脸的视频”“做一个傅里叶本轮画像”。
- 用户转来一条“无数旋转圆环画出任意轮廓”类的视频，要求“基于我的照片也做一个”。
- 用户对已出的傅里叶画像提出调整，例如“脸部线条再干净点”“换成单链那种”“标题改一下”。
- The user asks to “turn my selfie into a Fourier epicycle drawing video” or
  “draw my portrait with rotating circles like the Fourier series animation”.

### Do not activate when

- 用户只要静态线稿、黑白头像或风格化头像；使用 `lov-bw-portrait`、`lov-riso-portrait` 等头像类 Skill。
- 用户要交互式网页算法演示（可暂停、逐步）；使用 `lov-algo-viz-creator`。
- 用户只要下载那条参考视频；使用 `lov-media-crawler`。
- 用户要给成片配乐、加口播或剪进长视频；成片交给 `lov-media-creator` 处理。

## User Profile (cross-session)

Read the shared `user-profile/v1` context declared in `skill.yaml` on every run.
This Skill's durable records live under `skills.lov-fourier-portrait.records`:

| Record | Meaning |
| --- | --- |
| `photo` | default portrait photo when the request names none |
| `logo` | light (white) logo PNG for dark backgrounds |
| `title` | default title line |
| `output_dir` | where finished videos go |
| `mode` | `xy` or `complex` |

Shared fallbacks: `brand.logo` for the logo, `workspace.output_dir` for output.
When the user directly states a durable choice (“以后都用这张照片”“标题固定用……”),
persist it and report the saved path:

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record --skill-id lov-fourier-portrait \
  --path records.photo --value '"/abs/path/photo.jpg"' --confirm
```

Never store photos themselves, inferred values, or credentials in the Profile.
See `references/user-profile.md`.

## Skill Group Composition

Read `references/skill-composition.md` before calling adjacent Skills. Handoffs are
artifact-based and optional: a reference link may come from `lov-media-crawler`, and
the silent MP4 may go to `lov-media-creator` for music or editing.

## Workflow (MANDATORY)

### Step 0: Resolve root and runtime

- Use `SKILL_DIR` if provided; otherwise infer the installed directory of this Skill.
- Verify `scripts/fourier_portrait.py`, `scripts/lineart.py`, `scripts/fourier.py`,
  `scripts/render.py` and `scripts/subject_mask.swift` exist; stop and name any missing path.
- Check `uv` (preferred) and `ffmpeg`. `uv run` reads the inline dependency block of
  `fourier_portrait.py`, so no manual environment is needed. Without `uv`, use a Python 3.10+
  environment that has the five packages listed in `compatibility`.
- On macOS check `swift --version`; it enables Vision segmentation and face-based cropping.

### Step 1: Resolve inputs

Resolve in order: current request → project context → Skill records → shared Profile → defaults.

1. **Photo** — one clearly visible face, front or three-quarter view. HEIC is fine on macOS.
   If none resolves, ask once for a photo path. Use only photos the user may process.
2. **Title** — one short line of on-screen copy, or none. Treat it as audience-visible
   microcopy and apply `lov-branding-consistency`; do not invent claims about the person.
3. **Logo** — optional light PNG; skip it rather than drawing a substitute.
4. **Mode** — `xy` (default): two real series, x chain on top, y chain on the left, like the
   classic reference videos. `complex`: one chain whose tip is the pen (3Blue1Brown style);
   the portrait is roughly twice as large in a 9:16 frame. Pick `complex` when the user wants
   the face bigger or mentions the single-chain look.
5. **Output** — explicit path, else `records.output_dir`, else `./output/videos/`. Never
   overwrite an existing file; add a version suffix instead.

### Step 2: QC stills first

```bash
uv run "$SKILL_DIR/scripts/fourier_portrait.py" --photo PHOTO --workdir WORK \
  --title "TITLE" --logo LOGO --stills-only
```

View `WORK/stills_sheet.jpg` (and `WORK/lineart.png` when the face looks off). Check:

- the face is recognizable in the line art: eyes or glasses, nose, mouth, jaw and hairline;
- no large noise fields (print halftone, textured backgrounds, busy clothing prints);
- the crop keeps head and shoulders, without cut-off fragments along the bottom edge.

Tune with `references/tuning.md` (mainly `--offset`, `--min-area`, `--crop`) and repeat. The
stills render in seconds, so iterate here rather than on the video.

### Step 3: Render the video

```bash
uv run "$SKILL_DIR/scripts/fourier_portrait.py" --photo PHOTO --workdir WORK \
  --out OUTPUT.mp4 --title "TITLE" --logo LOGO [--mode complex]
```

Default timeline is about 39 s at 1080×1920, 30 fps: 3.2 s intro (photo → line art), 11 passes
with N = 1…1024, 5.5 s reveal with formulas. Rendering takes about 15 s on Apple silicon.

### Step 4: Verify the deliverable

1. `WORK/report.json` exists; `ffprobe` shows h264, 1080×1920 and the expected duration.
2. View `WORK/video_sheet.jpg`: the photo opens, the passes run from N=1 to the last stage,
   the reveal shows the cream line art with formulas, and nothing sits in the top 160 px or
   bottom 260 px safe areas.
3. The last-stage error is under 1 % (normally about 0.2 %).
4. The video is silent by design. Do not synthesize music in code; hand off to an editing
   step or ask the user for a track.

### Step 5: Report

Lead with the output path and status. Then give duration, resolution, mode, the final
N and error, the fitted decay `r_k ~ k^-p`, and the tuning used. State that the video
has no audio. When the user asked how such videos are made, summarize
`references/prior-art.md` (technique, frameworks, what this Skill uses).

## Dependencies

- `uv`, or Python 3.10+ with numpy, opencv-python-headless, scipy, skia-python, matplotlib
- ffmpeg and ffprobe
- Optional: macOS 14+ with Swift (Apple Vision subject mask and face box)
- A font with CJK glyphs for Chinese titles (`--font`; default `Songti SC`)
