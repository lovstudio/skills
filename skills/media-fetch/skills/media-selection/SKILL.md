---
name: sgc-media-selection
description: >
  比较媒体候选的剪辑版本、画质、编码、体积、音轨、字幕、活跃度与证据，自动选出最合适版本；适用于“哪个版本最值得下”、"choose the best compact release"。
license: MIT
metadata:
  author: contributors
  version: "0.2.0"
  tags:
    - release-ranking
    - video-quality
    - subtitle-selection
  compatibility: "Python 3.9+; consumes the Media Fetch candidate JSON schema and separates advertised from observed health."
  dependencies:
    - python
---

# Media Selection

Choose for viewing value, not label prestige: confirm the cut, then balance useful
detail, efficient encoding, size, language coverage, current health, and evidence.
Treat advertised seeders as a discovery hint and observed throughput as an acquisition
signal; retain both in the decision for later review.

## Triggers

### Activate when

- 用户说“哪个版本最值得下”“画质尽量高但不要太大”。
- 用户希望导演剪辑版、加长版、原版或完整版，并偏好中英字幕。
- The user asks to choose the best compact release or compare multiple cuts.

### Do not activate when

- 用户只给出一个链接且明确不要比较其他版本。
- 用户要求开始下载但尚未完成磁盘容量预检。
- The user asks only to inspect a completed local file.

## Workflow (MANDATORY)

### Step 0: Load policy and inputs

Read `$KIT_DIR/references/quality-policy.md`,
`$KIT_DIR/references/candidate-schema.md`, and resolved preferences. Validate the
candidate JSON before ranking.

### Step 1: Verify identity before quality

Reject or penalize candidates for the wrong title, year, season, episode, or cut.
Edition labels supported only by filenames remain provisional. Compare candidate
duration to reliable edition runtimes when available.

### Step 2: Rank deterministically

Run:

```bash
python3 "$KIT_DIR/scripts/rank_candidates.py" \
  --input CANDIDATES_JSON \
  --output DECISION_JSON
```

Apply explicit user caps before defaults. Prefer efficient 2160p when its size and
source quality are credible; otherwise prefer strong 1080p HEVC/AV1. Penalize tiny
files with implausible quality claims and oversized remuxes in balanced mode.

### Step 3: Handle editions as a content decision

Director's cut, extended, uncut, complete, restored, and theatrical editions are not
interchangeable quality levels. Ask the user to choose when the cuts contain materially
different scenes or intent and no preference resolves the difference.

### Step 4: Handle subtitles and audio

Prefer verified embedded Simplified Chinese and English subtitles. Bilingual filename
markers improve discovery rank but do not count as verified streams. Prefer original
audio; treat dubs as additional value rather than a replacement unless requested.

### Step 5: Produce a concise decision

- Auto-select when `choice_required=false`.
- When choice is needed, present at most three options with edition, resolution/codec,
  size, subtitle status, runtime evidence, and health.
- Preserve the complete scored list in `DECISION_JSON` for acquisition fallback.
- Preserve a subtitle gap as an explicit warning. Missing `zh-Hans` may open the
  exact-release subtitle branch after media verification; it does not silently lower
  the release identity claim.

## Dependencies

Python 3.9+. No network dependency after the candidate manifest and edition evidence
are complete.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
