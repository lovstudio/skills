# lov-media-creator

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把录屏和演示素材整理成可发布成片，保留关键原声，完成 BGM 混音、封面方向、编码检查和交付报告。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-media-creator"
```

初始化器会自动生成同样的本地链接。发布到远程仓库、目录或渠道属于独立的发布流程。

## 使用

示例一：

> 把这段录屏剪成视频号成片，保留最后有声音的成果段；上传弹窗短一点，BGM 只做氛围，给我 MP4、封面和质检报告。

输入是源视频、可选 BGM 和明确的关键证据段；输出是成片、EDL、封面方向、媒体探测 JSON、音频质检 JSON 和交付报告。

示例二：

> Create a publish-ready 16:9 video from this screen recording. Keep the real result audio and separate rendered, audio, creative, and publish status.

## Profile 契约

`skill.yaml` 声明 `user-profile/v1`。运行时读取用户、品牌、工作区、偏好和 `skills.lov-media-creator` 专属记录；长期偏好通过 `scripts/profile_store.py` 原子写回。源代码不保存个人绝对路径、凭据或临时素材位置。详见 [`references/user-profile.md`](references/user-profile.md)。

## 交付质量门

- 成片可解码，画幅、帧率、编码和音频流符合目标平台。
- 最终结果段连续且有原声；BGM 不遮挡人声或关键反馈。
- 上传弹窗、等待和卡顿只保留必要信息，不占据主体。
- 封面与标题分别承担“主题说明”和“结果线索”，不把工具品牌做成叙事主角。
- 报告分开记录 `render_status`、`audio_status`、`creative_status` 和 `publish_status`。

## 原子组合

每个新 Skill 都带有 [`references/skill-composition.md`](references/skill-composition.md)，记录相邻能力、文件级交接和 Single Skill 决策。章节、学习字幕、封面生成、媒体获取和视频号发布都保持可选，不作为隐藏依赖。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)：用途、负责人、依赖、风险、输出与维度地图。
- [`cases/cases.json`](cases/cases.json)：真实 Input → Prompt → Output 证据。
- [`pricing-card.yaml`](pricing-card.yaml)：价值锚点、免费边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/media_probe.py --help
python3 scripts/timeline_check.py --help
python3 scripts/audio_qc.py --help
```

## 依赖

- Python 3.8+
- PyYAML（仅验证 Skill 结构时需要）
- FFmpeg 与 FFprobe（媒体处理与音频质检时需要）
- Pillow、Playwright 或图像工具（仅新封面资产需要）

## License

MIT
