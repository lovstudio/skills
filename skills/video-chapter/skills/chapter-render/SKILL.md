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

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
