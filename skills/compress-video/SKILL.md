---
name: lov-compress-video
description: >
  把指定视频压到尽可能小且画质不明显下降：默认 HEVC CRF 28 保留分辨率，可选质量
  档、目标体积、VMAF 画质门禁与替换原文件模式。Use when 用户说“把这个视频压小”
  “压缩到 50M 以内”或 “compress this video as small as possible”。
license: MIT
compatibility: "Portable Agent Skills format. Requires Python 3.9+ and FFmpeg with libx265 (libx264, libsvtav1, libvmaf optional). --fast and Trash-based --replace need macOS."
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - video
    - compression
    - hevc
    - ffmpeg
    - vmaf
---

# 视频瘦身 · Video Shrink

把一个或多个视频文件压缩成体积尽可能小、肉眼看不出明显损失的 MP4。默认策略是
libx265 CRF 28、保留分辨率与帧率、AAC 96k，输出 `<原名>-compressed.mp4` 放在原
文件旁边，原文件不动。质量档、目标体积、VMAF 门禁和替换模式都是可选开关。

## Triggers

### Activate when

- “把这个视频压小一点，发微信用。”
- “这条 4K 素材压到 1080p，尽量小。”
- “压缩到 50M 以内。”
- “压完直接替换原文件。”
- “Compress this video as small as possible without visible quality loss.”
- “Shrink these MP4s to fit in an email.”

### Do not activate when

- 只是问 HEVC、H.264、ProRes 的区别或该选哪个 → 直接回答，不跑编码
- 要先找出电脑上有哪些视频 → `lov-list-videos`
- 要剪辑、加字幕、拼接、调色 → `lov-media-creator`
- 要对课程实录做增强与分段 → `lov-media-preprocessor`
- 要压缩图片 → `baoyu-compress-image`

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

本 Skill 读取的长期记录（都可选）：

| 记录 | 含义 |
| --- | --- |
| `records.default_quality` | `smallest` / `small`（默认）/ `balanced` / `high` |
| `records.default_codec` | `hevc`（默认）/ `h264` / `av1` |
| `records.default_preset` | x264/x265 preset，默认按质量档选 |
| `records.audio_bitrate` | AAC 码率 kbit/s，默认按质量档选 |
| `records.max_edge` | 长边像素上限，默认不缩放 |
| `records.min_vmaf` | 画质门禁分数，设置后每次都会测 VMAF 并按需重编 |
| `records.output_dir` | 固定输出目录，默认放原文件旁边 |
| `records.replace_original` | `true` 时默认替换原文件；只有用户明确说过才可写入 |

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- 必须确认 `scripts/compress_video.py`、`scripts/profile_store.py`、
  `references/encoding-guide.md`、`references/skill-composition.md` 均存在。
- `ffmpeg -encoders` 里必须有 `libx265`；缺 `libvmaf` 时不能用 `--vmaf` /
  `--min-vmaf`，缺 `libsvtav1` 时不能用 `--codec av1`。
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-compress-video"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 确认输入文件路径存在，多文件用 `--output-dir` 或替换模式。
- 把用户话语映射到参数，不要先跑一遍再问：
  - “尽量小 / 默认” → 不加参数（`small`：CRF 28）
  - “画质要好一点” → `--quality balanced` 或 `high`
  - “越小越好，画质无所谓” → `--quality smallest`（CRF 32、slow、长边 1080、64k 音频）
  - “压到 XX M 以内” → `--target-size XXM`（两遍码率模式）
  - “要发给 Windows 老电脑 / 网页播放” → `--codec h264`
  - “快点，别等太久” → `--fast`（VideoToolbox，体积大约多两成，画质分更低）
  - “压完替换原文件” → `--replace`；原文件进废纸篓，`--permanent` 才直接删除
- 用户没有明确说替换时，一律保留原文件。替换是高影响操作，需要用户本轮明确
  授权或 Profile 里由用户亲口设定的 `replace_original`。
- 用户在意画质或素材珍贵时加 `--min-vmaf 90`：脚本会测分并在不达标时降 CRF
  重编，最多两次。VMAF 测量约等于再解码一遍两条视频，长片要先告知耗时。

### Step 1.5: Analyze nearby Skills before implementation

- 先读 `references/skill-composition.md`。批量场景的上游是 `lov-list-videos`
  （先列出候选再压），下游是 `lov-media-publisher`（压完上传）。
- 不要在本 Skill 里做剪辑、字幕或增强，那些各有归属。

### Step 2: Execute the workflow

1. 先看计划再跑（大文件尤其如此）：

```bash
python3 "$SKILL_DIR/scripts/compress_video.py" input.mov --dry-run
```

2. 默认压缩，输出到原文件旁边：

```bash
python3 "$SKILL_DIR/scripts/compress_video.py" input.mov
```

3. 常见变体：

```bash
# 画质门禁：VMAF 不到 90 就降 CRF 重编
python3 "$SKILL_DIR/scripts/compress_video.py" input.mov --min-vmaf 90

# 目标体积 50 MB（两遍编码）
python3 "$SKILL_DIR/scripts/compress_video.py" input.mov --target-size 50M

# 4K 压成 1080p、30fps、H.264，给兼容性优先的场景
python3 "$SKILL_DIR/scripts/compress_video.py" input.mov --max-edge 1080 --fps 30 --codec h264

# 批量：输出到一个目录，JSON 结果供后续统计
python3 "$SKILL_DIR/scripts/compress_video.py" *.MP4 --output-dir ~/compressed --json

# 替换模式：写 <原名>.mp4，原文件移到废纸篓
python3 "$SKILL_DIR/scripts/compress_video.py" input.mov --replace
```

4. 进度显示在 stderr：百分比、速度倍数与 ETA。长片可以直接告诉用户预计时长
   （1080p 在 Apple Silicon 上 libx265 medium 约 3 到 6 倍速，即 1 小时视频
   10 到 20 分钟）。

5. 用户说出长期偏好时写回 Profile，例如“以后都用 h264”：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-compress-video \
  --path records.default_codec \
  --value '"h264"' \
  --confirm
```

### Step 3: Validate the deliverable

- 脚本自带门禁：输出时长与源相差超过 0.5 秒或 1% 会丢弃输出并报
  `duration-mismatch`；输出不比源小会丢弃并报 `skipped-larger`（`--force` 保留）。
  两种情况下替换模式都不会动原文件。
- 回读 stderr 摘要：源大小、结果大小、百分比、节省量、用时、VMAF（若测）。
  报告给用户时给出这几个数字和输出路径；替换模式还要说明原文件去了废纸篓。
- 输出文件用 ffprobe 复核编码、分辨率、时长；`--json` 里已包含这些字段。
- 编码失败时保留 ffmpeg 最后 15 行错误，不重试相同命令；常见原因是源文件损坏、
  4:2:2 ProRes 未被 VideoToolbox 支持（去掉 `--fast`）或磁盘空间不足。
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as the
  standard trust bundle for this Skill.

## Dependencies

- Python 3.9+（仅标准库）
- FFmpeg 与 FFprobe，含 libx265；`--codec h264` 需 libx264，`--codec av1` 需
  libsvtav1，`--vmaf` / `--min-vmaf` 需 libvmaf；Homebrew 的 ffmpeg 默认全部包含
- `--fast` 与废纸篓式 `--replace` 依赖 macOS（VideoToolbox、Finder）
- 无外部 Skill 依赖；交接见 `references/skill-composition.md`
