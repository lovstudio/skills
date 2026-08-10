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

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
