# Skill Group Composition

## Nearby Skills Inspected

| Skill | 路由合同 | 与本 Skill 的关系 |
| --- | --- | --- |
| `lov-media-creator` | 录屏 / Screen Studio / Vlog / 长片的精剪、混音、母带、双画幅、交付契约 | **not composed（可选参考）**：录屏长教程、横版长片归它；本 Skill 的混音与质检是自带的轻量版本，不调用它的脚本 |
| `lov-interview-media-creator` | 一场采访 → 一条 ≤4 分钟竖版采访短片 | **overlap 已划界**：同为竖版短片，但输入是采访实录、叙事按原话重排；本 Skill 输入是主题、作者按脚本口播。`gen_bgm.py` 从它改写（同作者，MIT），起步工程沿用其字体加载与 Remotion 版本 |
| `lov-motion-media-creator` | 无实拍动态图志 | **not composed**：没有真人出镜；TTS 请求格式参考了它的 `narration.py` |
| `lov-roundtable-clip` | 多人实录切条 | **not composed** |
| `lov-style-clone` / `lov-writing-style` | 文章文风画像与改写 | **upstream（可选）**：作者想让口播更像自己的文字口吻时，可先用它们定稿语气，再写进 `script.json` |
| `lov-fact-check` / `deep-research` | 事实核查、多源调研 | **upstream（可选）**：Step 1 的事实可以交给它们查，产物是带出处的结论，写进 `facts[]` |
| `lov-image-creator` / `baoyu-image-gen` | 生图 | **upstream（可选）**：需要概念示意图或封面背景时生成，落到 `broll/` 或 `cover.bg` |
| `lov-media-crawler` | 下载单条公开视频 | **not composed**：参考样本分析时用过同类下载；本 Skill 运行时不下载他人作品 |
| `lov-voice2srt` | 录音转字幕 | **not composed**：本 Skill 的字幕从脚本出字、从对齐出时间；作者默认的云端 ASR 结果经 `align.py --words` 接入 |
| `lov-media-publisher` | 发视频号 / B 站 / 小红书 | **downstream**：交付已批准的成片、3:4 与 16:9 封面、标题；发布与回读归它 |
| `lov-branding-consistency` | 读者可见文本的品牌门禁 | **依赖**：标题、封面字、片尾一句话、标注都过它 |

## Atomic Handoffs

| 方向 | 交接物 | 验收归属 |
| --- | --- | --- |
| 上游调研 → 本 Skill | 带出处的事实条目 | 本 Skill：`facts[]` 每条有 `source` 与 `checked` |
| 作者 → 本 Skill | 一条竖拍口播原片（含 3 秒封面表情） | 本 Skill：`align.py` 的 `review` 为空或已确认 |
| 外部 ASR → 本 Skill | 逐字时间戳 JSON（每项含 w、s、e 三个字段） | 本 Skill：对齐分数与切点 |
| 本 Skill → 发布 | `deliverables/<版本>/` 成片、两张封面、`script.json.title`、质检报告 | 发布方：平台回读；本 Skill 只交 `rendered` / `approved` |

## Overlap Decisions

- 采访短片与本 Skill 都出竖版短片，保持分开：采访片的核心是「从别人的原话里找结构」，本片的核心是「先写脚本再拍」。
  两边共享的是做法（单条连续中间轨、BGM 最后挂载、封面缩略图验收），不共享 EDL 格式。
- 混音只做一条音乐床加人声的静态增益母带，足够这种片型；需要多首配乐、人声分离、SMR/CER 门禁的复杂混音时，转给 `lov-media-creator`。

## Composition Decision

Single Skill。主题 → 脚本 → 录制包 → 对齐 → 成片是同一个用户结果的连续阶段，共用一份 `script.json`，
拆成 Kit 会让每个模块都要重新理解同一份脚本。相邻 Skill 全部是可选的文件级交接，没有隐藏依赖。
