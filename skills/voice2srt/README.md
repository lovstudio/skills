# 语音成字幕 · Voice to Subtitles

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

把音频、录音或视频转成带有效时间戳的 SRT/JSON/TXT，并用 OpenLess 或
`lov-personal-vocabulary` 词库提高产品名、技术名和英文缩写的识别率。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR"   "$SKILL_SKILLS_INSTALL_DIR/lov-voice2srt"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

先检查时长、模型、词库条数与预计费用，不发起 API：

```bash
python3 scripts/voice2srt.py input.mp4 \
  --output-dir ./work/transcript \
  --provider dashscope \
  --vocabulary "$HOME/Library/Application Support/OpenLess/dictionary.json" \
  --dry-run
```

确认本次费用后生成字幕包：

```bash
python3 scripts/voice2srt.py input.mp4 \
  --output-dir ./work/transcript \
  --provider dashscope \
  --vocabulary /path/to/vocabulary.json \
  --confirm-cost
```

主要输出是 `transcript.srt`、`transcript.json`、`transcript.txt` 与
`report.json`。详见 [`references/provider-contracts.md`](references/provider-contracts.md)。

无可用云端凭据时，可显式选择 `--provider whisper-cpp`；模型路径通过
`WHISPER_CPP_MODEL` 或 `--model` 提供。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit；外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/test_voice2srt.py
python3 scripts/voice2srt.py --help
python3 scripts/rebuild_dashscope.py --help
```

## 依赖

- Python 3.9+
- PyYAML
- FFmpeg / FFprobe
- DashScope 或 Volcengine ASR credential（仅运行时读取）

## License

MIT
