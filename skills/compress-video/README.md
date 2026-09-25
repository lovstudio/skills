# 视频瘦身 · Video Shrink

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把视频压到尽可能小、肉眼看不出明显损失。默认 libx265 CRF 28，保留分辨率与帧率，
AAC 96k，输出 `<原名>-compressed.mp4` 放在原文件旁边，原文件不动。

本机实测（Apple Silicon，1080p HEVC 实拍 26 秒）：

| 方式 | 结果体积 | VMAF | 用时 |
| --- | --- | --- | --- |
| 源文件 | 24.7 MB | 100 | - |
| 默认 libx265 CRF 28 | 2.2 MB（8.9%） | 93.5 | 24 s |
| `--fast` VideoToolbox q=45 | 2.2 MB（9.1%） | 84.6 | 16 s |

## 本地安装

```bash
npx skills add lov-compress-video -g -y
```

或者在本仓库根目录手动链接：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-compress-video"
```

需要 FFmpeg（含 libx265；libx264、libsvtav1、libvmaf 可选）：`brew install ffmpeg`。

## 使用

```bash
# 默认：尽量小但画质不明显损失 -> input-compressed.mp4
python3 scripts/compress_video.py input.mov

# 先看计划与 ffmpeg 命令
python3 scripts/compress_video.py input.mov --dry-run

# 画质门禁：VMAF 低于 90 就降 CRF 重编（最多两次）
python3 scripts/compress_video.py input.mov --min-vmaf 90

# 目标体积 50 MB（两遍编码）
python3 scripts/compress_video.py input.mov --target-size 50M

# 4K 压成 1080p、30fps、H.264
python3 scripts/compress_video.py input.mov --max-edge 1080 --fps 30 --codec h264

# 替换模式：写 input.mp4，原文件移到废纸篓
python3 scripts/compress_video.py input.mov --replace

# 批量到一个目录，JSON 结果
python3 scripts/compress_video.py *.MP4 --output-dir ~/compressed --json
```

示例输出：

```text
talk.mov: 24.7M, 1920x1080 hevc 0:26, audio aac
  plan: libx265 crf=28 preset=medium yuv420p, audio aac 96k
  attempt 1: libx265 crf=28 preset=medium yuv420p -> 2.2M, VMAF 93.5
  compressed: 24.7M -> 2.2M (8.9%, saved 22.5M) in 0:24, VMAF 93.5
  -> ~/Movies/talk-compressed.mp4
```

## 参数

| 参数 | 作用 |
| --- | --- |
| `--quality smallest\|small\|balanced\|high` | 质量档，默认 `small`（CRF 28） |
| `--crf N` | 显式 CRF，覆盖质量档 |
| `--codec hevc\|h264\|av1` | 编码，默认 `hevc` |
| `--preset` `--max-edge` `--fps` `--audio-bitrate` | 细调 |
| `--target-size 50M` | 两遍编码到目标体积（hevc/h264） |
| `--vmaf` / `--min-vmaf 90` | 测画质分 / 不达标自动降 CRF 重编 |
| `--fast` | VideoToolbox 硬件编码，快但体积大、画质分低 |
| `--replace` / `--permanent` | 替换原文件（进废纸篓）/ 直接删除 |
| `--output` `--output-dir` `--overwrite` `--force` | 输出位置与覆盖控制 |
| `--dry-run` `--json` `--quiet` | 只看命令 / 机器可读结果 / 静默 |

质量档对照、硬件编码取舍、像素格式与门禁规则见
[`references/encoding-guide.md`](references/encoding-guide.md)。

## 安全门禁

- 原文件默认不动；`--replace` 才替换，且先进废纸篓。
- 输出时长与源不一致（超过 0.5 秒或 1%）→ 丢弃输出。
- 输出不比源小 → 丢弃输出并提示源已够小（`--force` 保留）。
- 临时文件 `<名>.part.mp4` 在失败或中断时自动清理。

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

本 Skill 的记录：`default_quality`、`default_codec`、`default_preset`、
`audio_bitrate`、`max_edge`、`min_vmaf`、`output_dir`、`replace_original`。例如：

```bash
python3 scripts/profile_store.py record --skill-id lov-compress-video \
  --path records.default_codec --value '"h264"' --confirm
```

详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。上游可选 `lov-list-videos`
挑候选、`lov-media-creator` 出成片；下游可选 `lov-media-publisher` 上传。交接物
都是文件路径，不构成运行时依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -m unittest tests/test_compress_video.py
```

## 依赖

- Python 3.9+（脚本仅用标准库）
- FFmpeg / FFprobe，含 libx265；libx264、libsvtav1、libvmaf 按开关需要
- macOS：`--fast` 与废纸篓式 `--replace`
- PyYAML，仅 `validate_skill.py` 需要

## License

MIT
