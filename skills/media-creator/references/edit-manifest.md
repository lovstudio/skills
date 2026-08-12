# Edit Manifest

EDL 使用 JSON 保存剪辑判断，让粗剪、精剪、渲染和回看共享同一份时间线。路径、标题和参数都应来自当前请求或 Profile，不要在 Skill 源码中写死个人工作区。

## Minimal schema

```json
{
  "schema": "lovstudio/media-edit/v1",
  "source": {
    "video": "SOURCE_VIDEO",
    "audio": ["OPTIONAL_AUDIO"],
    "duration_seconds": 1065.877
  },
  "target": {
    "platform": "video-channel",
    "aspect_ratio": "16:9",
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "duration_target_seconds": 65
  },
  "segments": [
    {
      "id": "hook",
      "source_start": 512.4,
      "source_end": 516.8,
      "role": "result-clue",
      "speed": 1.0,
      "protected_audio": false,
      "notes": "先给出最终状态的一角"
    },
    {
      "id": "result-playback",
      "source_start": 932.2,
      "source_end": 940.6,
      "role": "final-evidence",
      "speed": 1.0,
      "protected_audio": true,
      "bgm": "duck"
    }
  ],
  "audio": {
    "bgm": "BGM_FILE",
    "duck_during": ["voice", "result-playback"],
    "target_lufs_i": -16,
    "true_peak_ceiling_dbfs": -1
  }
}
```

## 字段约束

- `source_start` 和 `source_end` 使用秒数，`source_end` 必须大于 `source_start`。
- `id` 唯一；`role` 说明这段画面在叙事中的作用，不只写“clip-1”。
- `protected_audio: true` 表示原声必须进入最终混音并在回看中单独验收。
- `speed` 只改变节奏，不改变关键按钮、输入和结果的可辨认性。
- `bgm: duck` 表示 BGM 退到氛围层；成果段可使用 `original-only` 让原声单独收束。
- 允许时间线出现有意留白，但不允许片段重叠；是否要求连续由项目目标决定。
- EDL 的 `source` 路径只存在于项目文件，不复制进可复用 Skill 源代码。

## 运行顺序

1. 先用 `media_probe.py` 获取源时长，避免引用超出边界的时间。
2. 写入 EDL 后运行 `timeline_check.py`，处理所有 overlap、无效时长和重复 ID。
3. 渲染时按 EDL 明确映射视频、原声和 BGM；不要让 FFmpeg 自动猜流。
4. 终版回看每个 `protected_audio` 片段，并把实际结果写入交付报告。
