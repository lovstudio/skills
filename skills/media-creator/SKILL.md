---
name: lov-media-creator
description: >
  把录屏和演示素材剪成可审校、可发布成片：先交内嵌可编辑 SRT 的 MKV，再以批准字幕生成
  归档母版、平台文件与真实封面图片；同时保留关键原声、混音与质检。Use when creating
  subtitle-review or publish-ready screen-recording videos and recurring series.
license: MIT
compatibility: >
  Portable Agent Skills format. Requires Python 3.8+ and FFmpeg/FFprobe.
  Optional Pillow or an image tool for new cover assets. 视频号封面（3:4）由
  `lov-channels-cover` 上游产出，不是安装依赖；开场静帧是另一个交付物，需要一张与
  成片同画幅（竖版通常 9:16）的图。
metadata:
  author: contributors
  version: "0.9.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - media-production
    - video-editing
    - ffmpeg
    - audio-mix
    - delivery-qc
    - cover-assets
    - opening-still
  compatibility: "Python 3.8+, FFmpeg/FFprobe, optional Pillow or an image tool for cover assets."
---

# lov-media-creator — 从素材到字幕审校母版与可发布成片

把录屏、演示素材、原声和 BGM 组织成两阶段视频交付：先生成可在 Subtitle Edit 中校对的软字幕 MKV，再以用户批准的 SRT 生成归档母版和平台文件；同时交付剪辑清单、正式封面图片和可回读的质检报告。叙事重点放在真实工作流和实际问题上，工具只作为过程中的一个环节出现。

## Triggers

### Activate when

- 用户说“把这段录屏剪成视频号成片，保留最后有声音的成果段”。
- 用户说“压缩上传卡顿、加 BGM、做 16:9 封面，并给我质检报告”。
- 用户希望把长录屏整理成有开场、问题、操作证据和最终结果的短视频。
- 用户说“把已经录了几期的素材、work 和成片按期整理，后面还要持续做这个栏目”。
- 用户说“先给我内嵌 SRT 的 MKV，我用 Subtitle Edit 改完再出最终成片”。
- 用户说“把封面当第一帧”“开头停一下再进正片”——要的是开场静帧，它与封面是两个交付物，且是渲染的前置条件，见 Step 1.5。
- User asks to create a publish-ready video from a screen recording while preserving the original result audio.
- User asks for an opening still frame before the video body starts.

### Do not activate when

- 用户只要生成标题、正文或社交平台文案；交给文案或内容策略能力。
- 用户只要学习字幕、词汇注释或 ASS 人物卡；交给 `lov-subtitle-freedom-skill`。
- 用户只要章节进度条、透明章节层或剪映章节包；交给 `lov-video-chapter`。
- 用户已经有字幕批准后的平台成片，只要求上传并回读发布状态；交给 `lov-publish-wechat-channels`。

## User Profile (cross-session)

每次运行都读取 `skill.yaml` 声明的 `user-profile/v1`：用户语言与时区、品牌语气、工作区输出位置、共享偏好，以及 `skills.lov-media-creator` 下的 Skill 专属记录。解析顺序是当前请求、项目上下文、Skill 记录、共享偏好、用户/品牌 Profile、默认值。

用户直接说出的长期剪辑偏好或品牌事实，通过 `scripts/profile_store.py record --confirm` 写回 Profile，并在结果中报告保存路径。源代码保持可移植，不写入个人绝对路径、凭据或临时素材位置。完整契约见 [`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

运行前阅读 [`references/skill-composition.md`](references/skill-composition.md)。相邻 Skill 只通过文件、JSON、字幕或成品视频交接，不作为此 Skill 的隐藏运行依赖。

## Workflow (MANDATORY)

**必须按以下顺序执行。**

### Step 0: 解析运行环境

- 使用环境中的 `SKILL_DIR`；没有时从当前 Skill 上下文推断安装目录。
- 先验证 `$SKILL_DIR/scripts/media_probe.py`、`$SKILL_DIR/scripts/timeline_check.py`、`$SKILL_DIR/scripts/audio_qc.py`、`$SKILL_DIR/scripts/check_opening_still.py`、`$SKILL_DIR/scripts/subtitle_gate.py`、`$SKILL_DIR/scripts/profile_store.py` 是否存在。
- 再验证 `$SKILL_DIR/references/media-workflow.md`、`$SKILL_DIR/references/edit-manifest.md`、`$SKILL_DIR/references/audio-mix.md`、`$SKILL_DIR/references/cover-and-title.md`、`$SKILL_DIR/references/delivery-contract.md` 是否存在。
- 持续栏目或已有多期素材时，另外验证并读取 `$SKILL_DIR/references/project-workspace.md`。
- 视频检查或渲染需要 `ffprobe` 与 `ffmpeg`。封面生成只在明确需要新图时启用 Pillow 或图像工具。
- 永远不覆盖源视频、源音频或原字幕；输出先落到独立的 `deliverables` 或用户指定目录。

手工运行脚本时：

```bash
export SKILL_DIR="/path/to/lov-media-creator"
```

每次调用都解析 `context.profile`。若用户明确提出要长期保留的剪辑原则、音频偏好或品牌事实，调用 `scripts/profile_store.py record` 并带 `--confirm`，随后简短报告保存路径。

### Step 1: 明确输入与成片目标

如果工作区里已经混有多期素材、根级 `work` / `output` 或不明归属的旧成片，先按
[`references/project-workspace.md`](references/project-workspace.md) 做只读盘点，再移动文件。
默认结构是**顶层按期、每期内按生命周期分层**；不要在“全部按期”和“全部按媒介”之间二选一。
移动后必须更新工程代码、交付报告与质检 JSON 里的旧路径，并对现有成片做可读/解码回读。

记录以下事实，不替用户臆造内容：

1. 源视频、补充片段、原声轨、BGM、截图和已有封面；输入可为单个录屏或多个素材。
2. 目标平台、画幅、预期时长、受众、发布标题、封面文案和字幕是否需要烧录或平台 CC。
3. 必须保留的证据段，尤其是最终结果播放、真实声音、状态回读或失败反馈。
4. 交付文件：审校 MKV + 外置 SRT、批准后的归档母版、平台成片、封面、剪辑清单、音频/编码质检报告，以及可选的发布交接信息。

默认输出规格为 16:9、1920×1080、30fps、H.264、AAC 48kHz；明确请求或 Profile 有其他设置时，以当前请求为准。

**这是系列片的第 N 期（N>1）时，先读 [`references/series-template.md`](references/series-template.md)，
再读前一期留下的工程代码。** 那份文件是每期都要过的成片标准（钩子、片名卡、片尾资源卡、
章节进度条、字幕位置、气口处理、重点词、配乐同源、响度口径）。上一期的版式常量、配乐
合成器、进度条实现都在它自己的仓库里，**复用不是重写**——直接 import 前作的脚本，只换数据。

不做这一步的后果是可预期的：只做「删空档 + 烧字幕」就交付，会被判为粗糙初剪，然后整期重做。

有一项不能默认、必须问：**封面是并列交付物，还是成片的第一帧**。它决定执行顺序
（详见 Step 1.5），事后改主意等于重渲染，所以用 AskUserQuestion 一次问清，连同
画幅一起确认：

```text
问：开头要不要停一帧静态画面？
  A. 不要（默认）——封面只做主页/分享卡片，与渲染并行，之后换封面不用重渲染
  B. 要——需要另做一张与成片同画幅（竖版通常 9:16）的首帧图，且必须先定稿
```

选 B 且现有封面画幅与成片不一致时，在这里就说清代价（另做一张同画幅首帧 / 接受裁切 /
放弃首帧），不要等渲染完再谈。视频号的封面槽是 3:4，竖版成片通常 9:16，**默认就是不一致**。

### Step 1.5: 读取相邻能力与交接边界

先看 `references/skill-composition.md`，判断是否需要可选交接：

- 章节条：交给 `lov-video-chapter`，输入为已确认的成品或字幕，输出为章节项目/透明层。
- 学习字幕：交给 `lov-subtitle-freedom-skill`，输入为成片或原字幕，输出为保持原时间轴的 SRT/ASS。
- 视频号封面：交给 `lov-channels-cover`，输入为标题钩子与人像素材，输出为风格锁定的 `cover_3x4.png` / `cover_4x3.png` 与 `spec.json`。
- 通用配图或非视频号封面：交给 `lov-image-creator`，输入为封面方向 JSON 或文字 brief，输出为 PNG/可编辑 HTML。
- 视频来源获取：交给 `lov-media-fetch`，输入为检索需求，输出为经过核验的本地素材。
- 微信视频号发布：交给 `lov-publish-wechat-channels`，输入为字幕已批准且已质检的平台成片，输出为发布状态与回读证据。

本 Skill 负责最终成片的编辑判断、音频完整性和交付门禁；可选下游不得替代这些验收。

#### 开场静帧：这一条会改变执行顺序

**封面和开场静帧是两个交付物，不是同一张图的两种用法。** 视频号把它们分给了不同场景：
封面服务主页九宫格与分享卡片（2026-08-17 实测创建页只有一个槽，标签「个人主页和分享
卡片(3:4)」），视频画面服务信息流全屏播放（竖版普遍 1080×1920）。平台本就不期待两者
同比例。

封面默认是**并列交付物**，可以在渲染之后再出，互不阻塞。但用户要求「开头停一下再进
正片」时，那一帧变成**渲染的前置条件**——它就是成片的第一帧，没定稿就没法渲染，改它
等于重渲染。

所以这一条必须在 Step 1 就问清（用 AskUserQuestion，不要替用户默认）：

| 用户选择 | 后果 |
| --- | --- |
| 不要开场静帧（默认） | 封面只做卡片，可与渲染并行，改封面不重渲染 |
| 要 | 需另做一张与成片同画幅的图，先定稿；每次改它都要重渲染 |

把 3:4 封面直接当 9:16 首帧要裁掉左右 25%，标题组必然被切到。这不是工具缺一个比例档，
而是**拿错了素材**——`lov-channels-cover` 只负责封面，不该为此长出 9:16 档。三条路，
按代价从低到高：

1. 另做一张与成片同画幅的开场静帧，与封面共用视觉语言但各自适配安全区；
2. 接受裁切，但裁完必须目视确认标题组完整，并把裁掉的比例写进交付报告；
3. 放弃开场静帧，只交封面（默认，多数情况下是对的——封面已经承担了让人停下来的职责）。

**不要在本 Skill 里用 scale/pad 硬凑**：补边或拉伸会毁掉第一印象，而且渲染完才看得出来。

### Step 2: 扫描素材并建立编辑清单

先运行：

```bash
python3 "$SKILL_DIR/scripts/media_probe.py" \
  --input SOURCE_VIDEO \
  --output WORK_DIR/source-probe.json \
  --pretty
```

读取时长、分辨率、帧率、编码、音频声道、采样率和字幕流。长录屏先按真实内容找出“结果/承诺、问题、关键操作、证据、最终结果”几个节点，再写入 [`references/edit-manifest.md`](references/edit-manifest.md) 所定义的 EDL；不要按固定时长机械切段。

```bash
python3 "$SKILL_DIR/scripts/timeline_check.py" \
  --input WORK_DIR/edit-manifest.json \
  --duration SOURCE_DURATION \
  --output WORK_DIR/timeline-check.json \
  --pretty
```

上传弹窗、等待、卡住的文件选择器等低信息段应被压缩到能交代状态的长度；若它们遮挡了真实结果，直接跳过。为最终结果和原声设置 `protected_audio: true`，后续所有剪辑与混音都不得误删。

### Step 3: 设计叙事、标题与封面

阅读 [`references/media-workflow.md`](references/media-workflow.md) 与 [`references/cover-and-title.md`](references/cover-and-title.md)：

- 主角是工作流解决的实际问题，以及“终于跑通”的证据；工具名称只在确实帮助理解时出现。
- 保留信息差和悬念，但不虚构速度、权限、成功率或发布状态；“一键”“秒发”“完全自动”只有在有对应证据时才能使用。
- 用户给出标题时原样尊重。标题与封面承担不同职责：标题说明事件，封面让人看出结果线索。
- 章节标题必须从该段真实口播、画面与结果证据中归纳，并在分幕数据里保留一句命名依据；
  不用“参与开源”“共创风格”这类过程词代替该幕真正讲的“背景”“自定义 Prompt”等主题。
- 避免模板化的 AI 句式、空泛的“重新定义效率”和过量大字。封面优先展示状态、界面证据或前后对照。
- 剪辑节奏先服务理解，再服务刺激；成果段出现后，隐藏解释性字幕和多余顶栏，让真实画面与原声完成收束。

封面走 `lov-channels-cover` 时，标题钩子由那个 Skill 的门禁判定，本 Skill 不重复
评分，也不绕过它改常量；本 Skill 只负责**封面声称的事实与成片是否一致**——封面上
的数字、平台状态、结果承诺必须在片子里真的出现过。Step 1.5 选了要开场静帧时，那张图
必须在进入 Step 5 之前定稿。

**`cover-brief.md` 只是计划，不是封面交付。** 一旦目标包含发布或 `platform-ready`，必须拿到
当前平台实际槽位需要的 PNG/JPEG，并逐张核对尺寸、四边条带、安全区和目视构图；只有 brief、
prompt、方向稿或生成脚本时，`creative_status` 仍是 `blocked-on-cover-render`。不得因为视频、
字幕和文案都已通过，就把缺封面的交付写成完成。

### Step 4: 编辑画面并保护关键原声

系列片在这一步逐条对照 [`references/series-template.md`](references/series-template.md) 的硬性清单；
以下是通用部分。

**节奏：气口不是重点，死气才是。** 用户说「剪掉语气词」时，真正拖节奏的通常不是那些词。
实测账目（EP.02）：语气词 + 句尾拖音合计 9.0s，而没人说话、屏幕也没动的段落有 216s。
所以停顿检测要用 **10ms 粒度扫整条包络**，不要只枚举「≥1.2s 的大空档」。处置分两类：
静止停顿剪到 0.14s（章节交界留 0.40s），**有画面动作的停顿抽帧不删**——演示片删掉就断了。

拼接密度上去之后（几百处人声拼接），淡入淡出要跟着缩短到 ~6ms，30ms 的斜坡会磨掉短句的
首尾辅音；前提是每个切点已吸附到附近最静的 10ms 窗口。

1. 先按 EDL 做粗剪，再做一次连贯性检查；转场、加速和裁切都要服务信息密度。
2. 上传弹窗只保留必要的进入、选择和完成信号；卡顿段短暂呈现即可，不让等待成为视频主体。
3. BGM 是氛围层，不是主角。有人声、点击反馈或最终视频播放时，降低 BGM；成果段需要听清原声时可暂时只保留原声。
4. BGM 采用淡入淡出和 ducking，避免循环接缝、突兀起音与尾部截断。具体滤镜和参数见 [`references/audio-mix.md`](references/audio-mix.md)。
5. 若源素材本身没有可用原声，标记这一事实，不用 BGM 冒充真实反馈。
6. **系列片的配乐必须与前作同源**：import 前作的合成脚本，把段落表当数据重新绑定，
   不要复制一份改。两期用不同音色 = 两个栏目。
6b. **片中念到的三方产品要做 research 再贴回画面**（检索 → 官网 → 截 hero 区 → 画中画停
   几秒）。流程、位置怎么量、以及 `$ego-browser` 的两个坑见
   [`references/pip-research.md`](references/pip-research.md)。
7. **重点词强调要设上限**：同一个词有次数上限、每行最多一处、半数句子都出现的高频词
   不进表；配套音效按「每 N 秒最多一次」稀释。满屏都是重点等于没有重点。
8. **系列长视频每章正文前插入独立黑幕标题卡**：推荐 0.9–1.4s，显示“第 N 章 + 语义标题”；
   卡片必须落在口播句界或 EDL 片段边界，期间暂停人声，可延续低声配乐和轻转场声。第一章也要有，
   放在总片名卡之后、正文之前。插卡会改变后续字幕与章节时间码，必须由同一映射函数累计偏移。

### Step 5: 先渲染字幕审校母版，再封装最终成片

字幕存在时默认执行两道门，**第一遍不生成 MP4，也不把文件称为最终成片**。

#### Step 5A: 生成无旁白硬字幕的画面母版

使用 FFmpeg 统一重编码一次，避免多次有损导出。片名卡、章标题卡、章节条、身份块和非字幕图形可以留在
画面中；需要作者校对的旁白字幕不得烧入这一版。常用画面母版参数：

```bash
ffmpeg -y -hide_banner \
  -i SOURCE_VIDEO \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,fps=30" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -an WORK_DIR/video-master-no-subs.mp4
```

若涉及多段画面、原声与 BGM，使用 `filter_complex` 显式映射视频与音频；不要依赖默认流选择。源素材保持原位。

#### Step 5B: 封装审校 MKV

把无旁白硬字幕的画面母版、最终音频和成片时间轴 SRT 封装为 MKV，同时把同一份 SRT 单独放在
`deliverables/`。Subtitle Edit 可直接打开 MKV；外置 SRT 让作者无需抽轨就能校对。两者的
SHA-256 必须同时写入报告。

```bash
python3 "$SKILL_DIR/scripts/subtitle_gate.py" review \
  --video WORK_DIR/video-master-no-subs.mp4 \
  --audio WORK_DIR/audio-master.wav \
  --srt DELIVERABLE_DIR/review-v0.1.srt \
  --output DELIVERABLE_DIR/review-v0.1.mkv \
  --report DELIVERABLE_DIR/subtitle-review.json
```

此时只能记录：

```yaml
render_status: review-ready
subtitle_status: awaiting-review
delivery_status: blocked-on-subtitle-approval
```

不得生成或交接平台 MP4，不得写 `final`、`approved` 或 `publish-ready`。用户可以在 Subtitle Edit
中改文字、断句和时间码；保存后的 UTF-8 SRT 是后续唯一权威字幕源。

**作者所有权门禁（强制）**：审校 MKV/SRT 一旦交给作者，就成为不可变的作者输入。自动化不得再向
同一路径导出字幕，也不得从 transcript、旧 timeline 或 ASR 结果重建并覆盖它；重跑审校包装必须换
新的 review 版本号。作者校对后如果又插入章标题卡、片头或删改 EDL，必须把作者 SRT 通过显式时间
映射迁移到新时间轴，输出新的 approved SRT，并报告迁移前后文字是否逐字保留。禁止用重新转写替代迁移。

#### Step 5C: 字幕批准后封装归档母版与平台文件

只有用户明确确认字幕通过后，才运行批准门禁：

```bash
python3 "$SKILL_DIR/scripts/subtitle_gate.py" approve \
  --review DELIVERABLE_DIR/review-v0.1.mkv \
  --srt DELIVERABLE_DIR/subs-approved-v0.2.srt \
  --expect-edits \
  --output DELIVERABLE_DIR/master-v0.2.mkv \
  --report DELIVERABLE_DIR/subtitle-approved.json
```

用户明确说“字幕已经改过”时，`--expect-edits` 是必选项：若批准 SRT 与审校 MKV 内嵌字幕逐条完全
相同，门禁必须失败，先查 Subtitle Edit 自动备份或作者保存路径，不得把相同文件复制成 `approved`。
批准报告必须记录 review MKV、approved SRT 的路径、mtime、SHA-256、条数和
`changed_from_review`；有时间轴迁移时还要附迁移报告。即使作者只改了断句或时间码，也属于有效差异。

脚本验证 UTF-8、时间码、正时长、顺序、无重叠、成片边界和内嵌字幕回抽一致性，并以 stream copy
替换字幕轨；视频和音频不再有损编码。`master.mkv` 是归档母版，不自动等于平台上传文件。

平台容器每次以当前上传界面为准。默认策略：

- B 站即使允许 MKV，也优先交 H.264/AAC MP4，并把批准 SRT 作为平台 CC 字幕上传；如果用户要求字幕始终可见，则从无字幕画面母版烧录一次。
- 微信视频号优先交 H.264/AAC MP4；平台没有明确承诺保留 MKV 内嵌字幕轨时，使用批准 SRT 烧录的 MP4。
- 只需要换容器且视频/音频已是 H.264/AAC 时使用 `-c copy -movflags +faststart`，不要把 MKV 再转码一次；只有烧字幕才重编码视频。

平台“接受 MKV”不等于“保留 MKV 里的字幕轨”。报告必须分别记录容器支持证据、字幕交付方式
（`embedded` / `platform-cc` / `burned-in`）和验证日期。每个派生平台文件还必须记录
`subtitle_source_sha256`，并与本次 approved SRT 的 SHA-256 相同；视频号烧录版须从最终文件抽取
至少三张命中作者修改点的实帧，目视确认修改文字和字幕样式后才可交给发布 Skill。

#### 开场静帧：先判画幅，再渲染

Step 1.5 选了要开场静帧时，渲染前必须跑一次只读判定，**不要直接 `-loop 1` 拼上去**：

```bash
# --still 传的是与成片同画幅的静帧图，不是主页卡片用的 3:4 封面
python3 "$SKILL_DIR/scripts/check_opening_still.py" \
  --still DELIVERABLE_DIR/opening-still-1080x1920.png \
  --video WORK_DIR/body.mp4 \
  --hold 1.5 --json
```

画幅一致时它返回 `ok: true` 和可直接执行的 `ffmpeg_command`。画幅不一致时**默认退出码 1**，
必须由你显式选一条路：`--allow-crop`（裁掉画面边缘）或 `--allow-pad`（首帧带黑边）。
这个门禁的意义是把「裁掉多少」变成一个写进交付报告的决定，而不是渲染几分钟之后才
从画面里发现。裁切损失超过 12% 或需要放大超过 1.05x 时它会另外告警——此时标题组
很可能已经被切到，裁完必须目视确认第一帧，不能只看退出码。

音频侧要垫一段与首帧等长的静音，否则 `concat` 之后整条声画会前移，成果段的原声会
和画面错开；脚本给出的命令已经包含 `anullsrc`。成片无音轨时改成 `-an` 并删掉音频链。

首帧停留默认 1.5s，低于 0.6s 会告警：观众来不及读完标题，等于白留一帧。

### Step 6: 做媒体与音频质检

```bash
python3 "$SKILL_DIR/scripts/media_probe.py" \
  --input REVIEW_OR_APPROVED_OUTPUT \
  --output DELIVERABLE_DIR/final-probe.json \
  --pretty

python3 "$SKILL_DIR/scripts/audio_qc.py" \
  --input REVIEW_OR_APPROVED_OUTPUT \
  --output DELIVERABLE_DIR/audio-qc.json \
  --pretty

ffmpeg -v error -i REVIEW_OR_APPROVED_OUTPUT -f null -
```

逐项回看开头、每张章标题卡、每个关键切点、最终结果连续播放和结尾。至少确认：章标题概括实际内容、
黑幕卡没有切进一句话、卡片之后音画与字幕同步、最终段仍有声音、BGM 没盖住人声、画面没有非设计黑帧
或意外静帧、上传弹窗没有占据主体、正式封面缩略图仍能读出主题。封面必须打开实际图片目视检查；
`spec.json`、生成日志、文件名和 `cover-brief.md` 都不能替代看图。审校版还要确认 MKV 中恰有一个默认
SubRip 字幕轨，并回抽与外置 SRT 逐条一致。目标响度参考 `-16 LUFS-I ±1.5`，True Peak 控制在
`-1 dBFS` 以下；实际值以报告为准。

做了开场静帧时另外抽出第一帧目视确认，**不能以脚本退出码 0 代替看图**：

```bash
ffmpeg -y -v error -i REVIEW_OR_APPROVED_OUTPUT -vframes 1 DELIVERABLE_DIR/first-frame.png
```

看三件事：标题组完整没被裁掉、四边没有黑条、首帧到正片的切换不突兀。另外确认音频
没有整体前移——首帧那一段应当是静音，正片第一句话的位置与 `body.mp4` 里一致。

### Step 7: 交付与发布交接

持续栏目中，交付物落到本期 `deliverables/`，过程文件落到本期 `work/`，原始素材留在
本期 `sources/`；跨两期以上复用的背景、字体说明或栏目级模板才提升到根级 `shared/`。
报告优先写相对本期目录的路径，避免工作区改名或迁移后证据链接整体失效。

按 [`references/delivery-contract.md`](references/delivery-contract.md) 生成交付报告，分别写清：

- `render_status`：成片是否导出且通过解码与参数检查；
- `subtitle_status`：`awaiting-review` / `approved`；只有用户确认后才能写 `approved`；
- `delivery_status`：是否仍被字幕批准门禁阻塞，或已经 `platform-ready`；
- `audio_status`：原声、BGM、响度和峰值是否通过；
- `creative_status`：标题、封面、叙事和证据段是否完成；
- `publish_status`：是否交给发布 Skill、是否已发布、是否有线上回读。

“审校版已渲染”“字幕已批准”“平台文件已生成”“已上传”“已发布”“已回读”是六个不同状态。只有出现真实平台回读证据时，才把 `publish_status` 写成 `published`。

发布型交付另外记录 `cover_status`：`missing` / `brief-only` / `rendered` / `approved`。
`creative_status=passed` 只能与 `cover_status=approved` 同时出现；`rendered` 仅表示图片已生成，
还没有完成尺寸、安全区、四边条带和目视检查。用户明确表示本期不要封面时才可记
`cover_status=waived-by-user`，不得由执行者自行豁免。

做了开场静帧时，`creative_status` 另外记三项，因为它们决定了这版成片还能不能改那一帧：

| 字段 | 内容 |
| --- | --- |
| `opening_still` | `true` |
| `opening_still_source` | 静帧图的文件路径与版本号 |
| `opening_still_fit` | `match` / `crop:<裁掉比例>` / `pad`，以及停留秒数 |

写清一条前提：**这版成片的第一帧绑定了这一版静帧图**，换图必须重渲染。静帧与封面是两个
文件，应共用同一套视觉语言，否则观众在列表页看到的封面和点开后的第一帧像两个来源。

## Validation

完成前运行：

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/media_probe.py" --help
python3 "$SKILL_DIR/scripts/timeline_check.py" --help
python3 "$SKILL_DIR/scripts/audio_qc.py" --help
python3 "$SKILL_DIR/scripts/check_opening_still.py" --help
python3 "$SKILL_DIR/scripts/subtitle_gate.py" --help
```

同时检查 `skill-card.yaml`、`skill-card.md`、`cases/cases.json` 和 `pricing-card.yaml`。至少保留一个真实 Input → Prompt → Output 案例，记录三项以上有证据的质量维度，并标明免费/付费渠道状态。

## Dependencies

- Python 3.8+ 标准库；`PyYAML` 用于 Skill 结构验证。
- FFmpeg 与 FFprobe 用于视频解码、转码、帧提取和音频质检。
- 可选 Pillow、Playwright 或图像生成能力，用于新封面资产；已有封面时不强制安装。
- 可选的字幕、章节和视频号发布 Skill 只通过交付文件交接，不是本 Skill 的安装依赖。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
