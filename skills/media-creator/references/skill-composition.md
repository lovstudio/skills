# Skill Group Composition

这个记录把相邻媒体能力和本 Skill 的最终验收边界分开，避免因为名称相近而形成隐藏依赖。

## Nearby Skills Inspected

| Skill | 实际输入 → 输出 | 关系 |
| --- | --- | --- |
| `FFmpeg Video Editor` | 自然语言编辑请求 → 单条 FFmpeg 命令 | 可参考的上游原子；本 Skill 负责完整流程、EDL、音频门禁和报告，不只返回命令。 |
| `lov-video-chapter` | SRT/视频 → 章节项目、透明层、烧录视频和编辑包 | 下游可选能力；接收已确认的成品或字幕，不参与本 Skill 的核心剪辑判断。 |
| `lov-subtitle-freedom-skill` | 视频/SRT + 学习者 Profile → 保持时间轴的 SRT/ASS | 下游可选能力；只在明确要求学习字幕时交接。 |
| `lov-channels-cover` | 标题钩子 + 人像素材 → `cover_3x4.png`、`cover_4x3.png`、`spec.json` | **视频号封面的上游**，只管封面（卡片场景），不管开场静帧；两者是不同画幅的两个交付物。 |
| `lov-image-creator` | 图像 brief → PNG、HTML 或外部模型 Prompt | 上游/下游均可；非视频号封面走它。视频号封面优先 `lov-channels-cover`，因为风格锁定与钩子门禁在那边。 |
| `lov-media-fetch` | 检索需求 → 已下载并核验的本地媒体 | 上游可选能力；只负责取得素材，不负责剪辑与成片验收。 |
| `lov-publish-wechat-channels` | 字幕已批准的平台媒体 → 发布状态与平台回读 | 下游可选能力；只接收 `platform-ready` 文件和交付报告，最终发布状态由发布能力负责。 |

## Atomic Handoffs

- `SOURCE_VIDEO`、音频和字幕流 → `media_probe.py` → `source-probe.json`：本 Skill 自己拥有输入完整性判断。
- EDL JSON → `timeline_check.py` → `timeline-check.json`：本 Skill 自己拥有时间线不重叠和 protected segment 门禁。
- 无旁白硬字幕画面 + 音频母带 + SRT → `subtitle_gate.py review` → 审校 MKV + 回抽证据：本 Skill 拥有字幕审校门禁。
- 审校 MKV + 用户批准 SRT → `subtitle_gate.py approve` → 归档 MKV：视频/音频 stream copy，不重复有损编码。
- 平台文件 → `media_probe.py`、`audio_qc.py` 和 FFmpeg decode smoke test → `final-probe.json`、`audio-qc.json`：本 Skill 自己拥有渲染与音频验收。
- `subtitle_status=approved` 且 `delivery_status=platform-ready` 的文件 + 交付报告 → `lov-publish-wechat-channels`：发布 Skill 拥有账号交互、发布和线上回读；本 Skill 只记录交接状态。
- 已确认成片或字幕 → `lov-video-chapter` / `lov-subtitle-freedom-skill`：这些能力拥有章节或学习字幕输出；本 Skill 不复制其专门逻辑。
- 封面方向 brief → `lov-image-creator`：图像能力拥有生图/渲染；本 Skill 负责封面在标题、主题和成片证据中的位置。
- 标题钩子 + 人像 → `lov-channels-cover` → `cover_3x4.png` / `cover_4x3.png` / `spec.json`：钩子门禁、风格锁定与整墙一致性归它；本 Skill 只判定封面声称的事实与成片是否一致。
- 定稿开场静帧 + `body.mp4` → `check_opening_still.py` → 画幅判定与 FFmpeg 片段：**做开场静帧时方向被反转**，那张图成为渲染的输入而非产物。画幅不一致时脚本默认退出码 1，逼调用方显式选 crop / pad / 另做一张同画幅的图，不允许静默 scale-pad。

## Overlap Decisions

- 与 `FFmpeg Video Editor` 有命令级重叠，保留其作为参考，不把本 Skill 缩减成命令生成器，因为用户要的是从素材到成片的完整闭环。
- 与 `lov-video-chapter`、`lov-subtitle-freedom-skill`、`lov-image-creator` 只在文件级交接，不复制章节、学习字幕或生图实现。
- 与 `lov-channels-cover` 的边界在「封面已定稿」：钩子公式、字号档位、整墙一致性全在那边，本 Skill 不复制评分、不改它的门禁常量。反过来，成片画幅、首帧停留时长和声画同步在本 Skill，那边不管。
- **首帧不是封面的一个比例档。** 视频号把封面（3:4，主页九宫格与分享卡片）和视频画面（竖版普遍 9:16）分给了不同场景，本来就不期待同比例。所以不要为了首帧去给 `lov-channels-cover` 加 9:16 档——需要首帧就单独设计一张 9:16 图，也不在本 Skill 里用 `scale`/`pad` 把 3:4 硬凑成 9:16。
- 与 `lov-media-fetch` 的边界在“素材已可读”；媒体获取失败时交回上游，不在此 Skill 内加入下载器。
- 与 `lov-publish-wechat-channels` 的边界在“字幕已批准，平台文件已通过质检”；审校 MKV 不得发布，发布失败或回读缺失也不得倒写成片状态。

## Composition Decision

选择 **Single Skill**。用户可见的结果是一个经过编辑、混音和质检的成片，扫描、剪辑规划、渲染、音频检查和交付报告共享同一份项目上下文；它们拆成独立 Skill 只会增加交接成本。相邻 Skill 通过明确的文件与状态交接保持可选，不作为源目录外的硬依赖。
