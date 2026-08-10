---
name: lov-media-verification
description: >
  使用 ffprobe 验证已下载视频的可读性、时长、分辨率、编码、音轨、字幕和剧集完整性；适用于“检查下载是否完整”、"verify the downloaded media"，输出结构化验收报告。
license: MIT
metadata:
  author: contributors
  version: "0.2.0"
  tags:
    - ffprobe
    - media-validation
    - subtitle-audit
  compatibility: "Python 3.9+ and ffprobe from FFmpeg; optional exact-release subtitle handoff."
  dependencies:
    - python
    - ffprobe
---

# Media Verification

Confirm the local artifact, selected edition, and language coverage before declaring
the request complete. A missing Simplified Chinese stream opens a subtitle handoff,
while the media artifact retains its own technical verdict.

## Triggers

### Activate when

- 用户说“检查下载是否完整”“确认是不是导演剪辑版和中英字幕”。
- 下载客户端显示完成，需要验证实际本地文件。
- The user asks to verify the downloaded media or inspect its audio and subtitles.

### Do not activate when

- 用户只想搜索候选或测速，尚无完成文件。
- 用户要重新压制、转码、剪辑或翻译字幕。
- The user asks only for a plot summary or release recommendation.

## Workflow (MANDATORY)

### Step 0: Resolve expected truth

Load the acquisition report, selected candidate, expected edition runtime, requested
episode set, and preferred languages. Locate the exact final path; do not scan unrelated
user directories broadly.

### Step 1: Inspect the container

Run:

```bash
python3 "$KIT_DIR/scripts/verify_media.py" \
  --path FINAL_PATH \
  --output VERIFICATION_JSON
```

Require at least one readable video stream and positive duration. Capture container,
resolution, video codec, HDR hints, audio codecs/languages/channels, subtitle codecs
and languages, total size, and remaining partial suffixes.

### Step 2: Verify edition and completeness

Compare duration with reliable edition runtime using the configured tolerance. For
episodes, match the requested season/episode set rather than accepting a folder name.
Record conflicts between filename claims and observed duration.

### Step 3: Repair subtitle gaps

If preferred subtitle streams are absent, look for synchronized external subtitles
matching the exact release or runtime. Store beside the media using player-compatible
naming and inspect its declared language. Follow `references/subtitle-handoff.md` for
UTF-8 SRT and timing preservation, then consult `lov-subtitle-freedom-skill` only for
the requested subtitle operation. Do not label unsynchronized text as complete.

### Step 4: Issue the verdict

Use `passed`, `passed_with_warnings`, or `failed`. Report exact local path, edition
confidence, technical summary, subtitle coverage, size, and any open evidence. A client
state of 100% alone is insufficient evidence.

## Dependencies

Python 3.9+ and `ffprobe`. External subtitle repair additionally needs an available
subtitle discovery path.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
