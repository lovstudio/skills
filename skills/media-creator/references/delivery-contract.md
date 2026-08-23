# Delivery Contract

成片交付由文件、字幕批准、参数、创意判断和状态证据共同组成。审校 MKV 不代表字幕已批准，单独存在的 MP4 也不代表已经发布。

## Required deliverables

- `review-vN.mkv`：第一遍审校母版；画面不烧旁白字幕，内嵌一个默认 SubRip 字幕轨；
- `review-vN.srt`：与审校 MKV 同源的 UTF-8 外置字幕，供 Subtitle Edit 直接修改；
- `subtitle-review.json`：审校 MKV/SRT 的流信息、条数、状态和 SHA-256；
- `subs-approved-vN.srt`：用户批准后的唯一权威字幕源；批准前不得出现；
- `master-vN.mkv`：以批准 SRT 替换字幕轨的归档母版，视频/音频 stream copy；
- `platform-<name>-vN.mp4`：目标平台文件；按平台采用批准字幕烧录或平台 CC；
- `cover_<ratio>.png` / `.jpg`：目标平台每个实际封面槽所需的正式图片；必须记录尺寸、哈希、
  安全区与目视结论。`cover-brief.md` 只能作为规划附件，**不能替代正式封面，也不能让
  `creative_status` 通过**；
- `first-frame.png`：仅在做了开场静帧时——从成片抽出的实际第一帧，用于目视确认；
- `edit-manifest.json`：源素材、时间线、保护段和混音策略；
- `final-probe.json`：当前阶段媒体的视频、音频、字幕、时长、尺寸、帧率和编码信息；
- `audio-qc.json`：响度、峰值、采样率、声道和检查状态；
- `timeline-check.json`：**由脚本从 EDL 生成**的结构与时间码（片头分镜、片名卡、逐章黑幕
  标题卡、各章正文、片尾，加细章节与资源的成片时间码）。每张章标题卡记录语义标题、命名依据、
  起止帧和正文起点；报告和发布文案里的每个时间码都从这里抄，不手写、
  不从上一版文档抄——改片头长度会让全部时间码同时静默失效；
- `delivery-report.md`：人类可读的判断、证据和剩余缺口。

## Status fields

```yaml
render_status: review-ready
subtitle_status: awaiting-review
delivery_status: blocked-on-subtitle-approval
audio_status: passed
creative_status: passed
cover_status: approved
publish_status: not-requested
readback_evidence: []

# 仅在做了开场静帧时出现，缺一项就说明这版成片的首帧来源不可追
opening_still: true
opening_still_source: output/covers/e01/opening-still-1080x1920.png · v0.5
opening_still_fit: match  # match / crop:<比例> / pad
opening_still_hold: 1.5s
```

状态解释：

- `render_status=review-ready`：审校 MKV 存在、可解码，且内嵌 SRT 与外置 SRT 回抽一致；
- `render_status=passed`：批准后的归档母版或平台文件存在、可解码，且媒体参数符合目标；
- `subtitle_status=awaiting-review`：字幕仍可编辑，不能称为最终成片；
- `subtitle_status=approved`：用户明确确认了报告所列 SHA-256 对应的 SRT；
- `delivery_status=blocked-on-subtitle-approval`：平台文件不得生成或交接；
- `delivery_status=platform-ready`：批准字幕已按目标平台方式封装或烧录并通过质检；
- `audio_status=passed`：原声保护、混音、响度和峰值检查通过；
- `creative_status=passed`：标题、封面、叙事结构和证据段完成；
- `cover_status=missing`：没有封面图片；`brief-only`：只有方向稿；`rendered`：已出图但尚未完成
  尺寸、安全区、四边条带和目视检查；`approved`：所有目标槽位的正式图片均已验收；
- 发布型交付中，`creative_status=passed` 必须同时满足 `cover_status=approved`。用户明确不要
  封面时才可记 `cover_status=waived-by-user`；执行者不得用 brief、prompt、脚本或默认抽帧自行豁免；
- `publish_status=uploaded`：平台已接收文件，但线上可见性或回读尚未确认；
- `publish_status=published`：有平台回读证据支持，例如对象 ID、状态字段和成功标志；
- `publish_status=not-requested`：本次只制作成片，没有启动发布交接。

## Report minimum

报告至少记录：

1. 输入文件的可识别名称、源时长和源媒体参数；
2. 当前阶段（review / approved master / platform）、目标规格与实际输出规格；
3. 被压缩、被跳过和被保护的时间段；
4. BGM 文件名、ducking 规则和高潮段原声处理；
5. 视频解码、时间线、响度、峰值和人工回看的结论；
6. 标题、封面文案、每个目标比例的正式图片路径/尺寸/SHA-256、目视结论和未验证假设；
7. 做了开场静帧时：静帧图路径与版本、画幅适配方式（裁掉多少 / 是否补边）、停留时长，
   以及一条明确前提——**这版成片的第一帧绑定了这一版静帧图，换图必须重渲染**；
8. 审校 MKV、外置 SRT、批准 SRT 的 SHA-256，以及字幕批准人/确认时间（如果已批准）；
9. 平台容器支持证据、验证日期和字幕交付方式（embedded / platform-cc / burned-in）；
10. 发布对象、回读时间和原始状态字段（如果发生发布）。
11. 有逐章黑幕卡时：每张卡的序号、语义标题、命名依据、停留时长、卡片起点和正文起点；另记
    “没有切进 cue / 音画字幕累计偏移一致”的验证结论。

## Handoff boundary

交给发布 Skill 时只发送 `subtitle_status=approved`、`delivery_status=platform-ready` 且
`cover_status=approved` 的平台文件、正式封面图片、标题、简介/标签、批准 SRT（平台支持 CC 时）
和交付报告。只有 `cover-brief.md` 时不得进入发布交接。审校 MKV 不得进入发布交接。账号、
Cookie、验证码和平台内部令牌留在运行时，不进入源目录或报告。发布 Skill 返回的状态与回读
证据再写入交付报告的 `publish_status` 区域。

做了开场静帧时多一条约束：**上传的封面与首帧必须共用同一套视觉语言**。它们是两个不同
画幅的文件，不可能是同一张图，但观众会连着看到——列表页一张、点开第一帧另一张——两者
风格不统一就像两个来源。在报告里点名两个文件的路径与版本，不要只写「已附封面」。

上游边界在「封面已定稿」。视频号封面的钩子公式、风格锁定与整墙一致性属于
`lov-channels-cover`；本 Skill 不复制它的评分，也不改它的门禁常量。

**首帧不是封面的一个比例档**：平台把封面（3:4，主页九宫格与分享卡片）和视频画面
（竖版普遍 9:16）分给了不同场景，本来就不期待同比例。需要首帧时单独设计一张 9:16 图，
不要为此给 `lov-channels-cover` 加比例档。
