# lov-media-creator

![Version](https://img.shields.io/badge/version-0.8.1-CC785C)

把录屏和演示素材整理成两阶段交付：先做内嵌可编辑 SRT 的 MKV 审校母版，再以批准字幕生成归档母版、平台文件和正式封面图片；同时保留关键原声，完成 BGM 混音、编码检查和交付报告。

## 安装

从公开仓库全局安装：

```bash
npx skills add lovstudio/media-creator-skill -g -y
```

开发当前源码时，也可以在本仓库根目录用本地路径安装：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
npx skills add "$SKILL_SOURCE_DIR"
```

## 使用

示例一：

> 把这段录屏剪成视频号成片，保留最后有声音的成果段；第一遍只给我内嵌 SRT 的 MKV 和外置 SRT，我用 Subtitle Edit 改完确认后，再生成平台 MP4。

输入是源视频、可选 BGM 和明确的关键证据段；第一阶段输出审校 MKV + 外置 SRT，第二阶段才输出批准字幕归档母版、平台成片、EDL、各平台槽位的正式封面图片、质检 JSON 和交付报告。

## 字幕审校门

有字幕时，`review` 阶段的画面不烧旁白字幕，只把 SRT 作为 MKV 的默认 SubRip 轨封装；状态是
`review-ready / awaiting-review`。作者可在 Subtitle Edit 中改文字、断句和时间码。只有明确确认后，
`approve` 阶段才以 stream copy 替换字幕轨生成归档 MKV，并按平台生成 MP4 或平台 CC 字幕。

```bash
python3 scripts/subtitle_gate.py review --help
python3 scripts/subtitle_gate.py approve --help
```

MKV 是内部审校与归档容器。即使平台允许上传 MKV，也不等于会保留内嵌字幕轨；平台交付默认使用
兼容性更稳的 H.264/AAC MP4，字幕按平台选择 CC 或批准后烧录。

示例二：

> Create a publish-ready 16:9 video from this screen recording. Keep the real result audio and separate rendered, audio, creative, and publish status.

## Profile 契约

`skill.yaml` 声明 `user-profile/v1`。运行时读取用户、品牌、工作区、偏好和 `skills.lov-media-creator` 专属记录；长期偏好通过 `scripts/profile_store.py` 原子写回。源代码不保存个人绝对路径、凭据或临时素材位置。详见 [`references/user-profile.md`](references/user-profile.md)。

## 封面，和可选的开场静帧

**这是两个交付物**，平台把它们分给了不同场景，本来就不期待同比例：封面出现在主页九宫格
和聊天分享卡片（视频号 3:4），视频画面出现在信息流全屏播放（竖版通常 9:16）。

要不要在开头停一帧静态画面，在开始前就会问你，因为它改变执行顺序：

- **不要（默认）**：封面只做卡片，与渲染并行，之后换封面不用重渲染。
- **要**：需另做一张与成片同画幅的图，它成为渲染的输入，必须先定稿，改它等于重渲染。

视频号封面交给 `lov-channels-cover` 出图；开场静帧不是它的一个比例档，把 3:4 封面当
9:16 首帧要裁掉左右 25%，标题组必然被切到。选「要」时，本 Skill 在渲染前跑
`scripts/check_opening_still.py` 判画幅，不一致时默认退出码 1，逼你显式选裁切、补边，
或另做一张同画幅的图，而不是渲染几分钟后从画面里发现。

## 交付质量门

- 成片可解码，画幅、帧率、编码和音频流符合目标平台。
- 审校 MKV 恰有一个默认 SubRip 字幕轨，回抽后与外置 SRT 逐条一致；批准前不生成平台文件。
- 最终结果段连续且有原声；BGM 不遮挡人声或关键反馈。
- 章节标题由该幕实际内容证据归纳；系列长视频每章正文前有独立黑幕标题卡，且不切进一句话。
- 上传弹窗、等待和卡顿只保留必要信息，不占据主体。
- 封面与标题分别承担“主题说明”和“结果线索”，不把工具品牌做成叙事主角。
- `cover-brief.md` 只算方向稿；发布型交付必须存在平台各槽位的真实封面图片，并通过尺寸、
  安全区、四边条带与目视检查，才能写 `cover_status=approved / creative_status=passed`。
- 做了开场静帧时，抽出第一帧目视确认标题组完整、四边无黑条、音频没有整体前移。
- 报告分开记录 `render_status`、`audio_status`、`creative_status` 和 `publish_status`；
  开场静帧另记 `opening_still`、`opening_still_source` 和 `opening_still_fit`。

## 原子组合

做系列片的第二期及以后，先读 [`references/series-template.md`](references/series-template.md)：钩子、片名卡、逐章黑幕标题卡、片尾资源卡、章节进度条、字幕位置、气口处理、重点词、配乐同源、响度口径，每期逐条过。前一期的版式常量与配乐合成器直接 import 复用，不重写。

每个新 Skill 都带有 [`references/skill-composition.md`](references/skill-composition.md)，记录相邻能力、文件级交接和 Single Skill 决策。章节、学习字幕、封面生成、媒体获取和视频号发布都保持可选，不作为隐藏依赖。

## 系列工作区

栏目持续录多期时采用混合结构：顶层按 `episodes/epNN-topic/` 分期，每期内部固定
`sources/`、`work/`、`deliverables/`；真正跨两期以上复用的资产才进入根级 `shared/`。
这让一期可以整体归档，也让输入、过程和成品的生命周期保持清楚。

迁移旧工作区前先按内容、报告和媒体探测确认归属，不凭文件夹名猜；不明文件进入
`sources/legacy-*` 或 `work/legacy-*`，不在整理时删除。移动完成后更新脚本、报告和质检 JSON
里的旧路径，并回读既有成片。完整规则见 [`references/project-workspace.md`](references/project-workspace.md)。

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
python3 scripts/check_opening_still.py --help
python3 scripts/subtitle_gate.py --help
```

## 依赖

- Python 3.8+
- PyYAML（仅验证 Skill 结构时需要）
- FFmpeg 与 FFprobe（媒体处理与音频质检时需要）
- Pillow、Playwright 或图像工具（仅新封面资产需要）

## License

MIT
