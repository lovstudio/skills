---
name: lov-video-chapter-plan
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

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
