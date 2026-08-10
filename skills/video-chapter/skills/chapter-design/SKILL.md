---
name: lov-video-chapter-design
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

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
