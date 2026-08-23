# Changelog

## [0.9.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.8.2] - 2026-08-23

### Fixed

- classify FFmpeg and FFprobe as runtime requirements, not embedded Skill dependencies
- unblock self-contained WorkBuddy packaging without weakening runtime compatibility checks

## [0.8.1] - 2026-08-23

### Fixed

- require rendered cover assets for publish-ready delivery
- treat cover briefs as planning artifacts and add cover_status evidence gates

## [0.8.0] - 2026-08-23

### Added

- add semantic chapter titles and black opening cards
- recompute subtitle, audio, and delivery timestamps after inserted chapter cards
- record EP.03 sentence-boundary validation and review evidence

## [0.7.0] - 2026-08-23

### Added

- add subtitle-review MKV approval workflow
- package and verify editable SubRip tracks with subtitle_gate.py
- block platform output until the user approves the SRT
- document MKV archival and platform-specific MP4 handoff

## [0.6.0] - 2026-08-23

### Added

- 新增持续栏目的工作区契约
- 固定“顶层按期、期内按 sources / work / deliverables 分层”，并明确 shared 的提升边界
- 迁移旧工作区时要求先确认归属、不删除未知文件、修复路径，并在搬迁后回读媒体

## [0.5.0] - 2026-08-18

沉淀 EP.03 三轮返工暴露的判据，全部是「跑完全绿但成片是错的」那一类。

### Added

- references/pip-research.md：片中念到的三方产品，检索 → 官网 → 截 hero 区 → 画中画贴回去；
  位置只能量不能挑（三个候选区占比都在 30-34%，没有空区），晚于人声 0.35s 出现，必须有边框和域名条
- series-template.md 补齐响度、地址栏 OCR、多素材分块、画中画、字幕回灌等判据：
  - 响度口径：折混成单声道**只对峰值是假象**（等能量下混凭空报出削顶），**对 LUFS 是真的**（BS.1770-4 按加权能量求和，先折混再测比标准表低 3 dB）——两件事长得一样结论相反
  - 地址栏 OCR 四条判据：`--psm 12`/`--psm 6` 取并集、域名匹配按长度降序且 `i>=0`、用剩余英文单词数（≤3）判是否为地址栏行、原始 OCR 文本落盘缓存
  - 字幕回灌用 SequenceMatcher 而不是按序号（按序号会把几十条挂错画面）；按「与保留下来的人声段有没有重叠」过滤，否则被删段的 cue 会塌在切点上叠成一堆
  - 不能裁顶栏时画底板要量实际带高（菜单栏 vs 边缘空白），章节标签要排两遍并用真实字体测宽
  - 一个分块不许跨素材，成片帧数从盘上逐 clip 回读 `ffprobe` 再对总数下断言
  - 画中画裁切下界先躲第三方 IP 和真人脸（按饱和度扫，不是亮度）；单帧 PNG 输入不加 `loop=-1`，否则驱动 overlay 越过主输入结尾，编码永不停止
- 进度条颗粒度改为 3-10 幕（细章节太细只留给剪辑节奏与 B 站目录），分幕表只记起点，顶栏与发布文案读同一张表
- 身份块三面墙（字幕底板下沿 / dock 上沿 / 画面左缘）量并写成断言，dock 按亮度台阶扫（饱和度扫会被应用图标骗）

### Fixed

- 覆盖层底板一律全不透明：此前给身份块留 92% 是「它压在深色 UI 上」的假设，浅色界面下页面正文会透到标题背后
- 本期文案改成单一来源脚本读取，标题散在多个脚本各一份字面量会漏改，成片开头念旧标题而所有门禁仍是绿的
- 删用户点名内容要另立 CUT_SPEECH 表，断言方向与「防止误删」的 EXCISE 表相反，两种情况在成片里听起来完全一样
- 钩子出点：10ms 包络会漏掉比它粒度还短的句界，需要覆盖表 + 复量 + 转写反向验证
- 画中画裁切下界改成 `keep_out` 断言，不写成看似绝对行号实为分数的值，避免重抓截图后静默脱锚
- 改了 EDL 音频链或 `subs.ass` 后必须按顺序全部重跑；脚本互相不检查上游是否比自己新，改完不重跑会渲出上一版覆盖层
- 交付报告改为脚本生成，质检结论不许写死，产物缺失就印「未跑」

## [0.4.0] - 2026-08-17

### Added

- series-template.md 清单补到 14 条：**13 封面第二行（锚点条）永远是系列名**——它是系列在信息流里唯一稳定的识别锚点，主标题超宽也不许拿本期概括去换；**14 交付时间码由脚本从 EDL 重算**，不手抄上一版
- series-template.md 新增「交付时间码必须由脚本生成」：给出 src→out 映射的实现与两条断言，以及验证映射本身的办法（用上一版的 `body_out_start` 跑一遍必须精确复现上一版全部数字）
- series-template.md 新增「测响度不要让 ffmpeg 折混成单声道」：`-ac 1` 的下混是等能量的，dual-mono 母版会读高恰好 3.01 dB 并凭空报出削顶
- cover-and-title.md 新增两行文案的归属与「门禁拦下用户指定文案时写本期包装脚本」：monkeypatch `MAX_VISUAL_WIDTH` / `DISPLAY_TIERS` 后 `runpy` 调 render_cover，新字号档按可用列宽推导（`928 / 7.12em = 130px`），不改 skill 常量
- delivery-contract.md 交付清单加入 `timeline-check.json`

### Changed

- 清单第 1/2 条按 EP.02 修正：冷开场用 **2–3 个**高光镜头（一句 2.5s 撑不住 19 分钟演示片），片名卡从「1–2s」改为 **≥2.5s**（1–2s 读不完系列名 + EP 号 + 本期标题三行）

## [0.3.0] - 2026-08-17

### Added

- references/series-template.md：系列片每期都要过的成片标准清单（12 条硬性项）。写它的直接原因是 EP.02 初剪只做了「删空档 + 烧字幕 + 章标」就交付被退回——上一期的规范当时只活在那个仓库的代码里，规范不进 Skill 就等于没有规范
- Step 1 增加前置动作：系列片第 N 期（N>1）先读 series-template.md，再读前一期的工程代码；配乐/版式/进度条一律 import 复用而非重写
- Step 4 补进剪辑节奏口径：停顿检测用 10ms 粒度扫包络而不是只枚举大空档（实测语气词值 9.0s，死气值 216s）；静止停顿剪到 0.14s，有画面动作的停顿抽帧不删
- Step 4 补进重点词强调的上限规则与配乐同源要求

### Fixed

- 拼接密度高时（几百处人声切点）淡入淡出应缩到 ~6ms，30ms 会磨掉短句首尾辅音

## [0.2.1] - 2026-08-17

### Fixed

- 纠正首帧与封面的关系：两者是平台分开的两个交付物，不是一张图的两种比例
- 删掉「让 lov-channels-cover 增加 9:16 比例档」这条错误指引：视频号封面槽是 3:4（服务主页九宫格与分享卡片），视频画面竖版普遍 9:16（服务信息流全屏），平台本就不期待同比例，需要首帧应单独设计一张 9:16 图
- 标注 9:16 是主流与推荐而非硬门槛（4:3/16:9 也能发但在竖屏容器里被放大裁切），封面 3:4 则为创建页实测
- 术语与接口随之改名，避免名字本身教人拿错素材：`check_cover_frame.py` → `check_opening_still.py`，`--cover` → `--still`；交付字段 `cover_as_first_frame` / `cover_source` / `first_frame_fit` / `first_frame_hold` → `opening_still` / `opening_still_source` / `opening_still_fit` / `opening_still_hold`
- 画幅不一致的报错文案点明「若传的是 3:4 主页封面，那是拿错了素材」

## [0.2.0] - 2026-08-17

### Added

- 支持把封面作为成片首帧，并把 lov-channels-cover 定为视频号封面上游
- 新增 scripts/check_cover_frame.py：渲染前判定封面与成片画幅，不一致时默认拒绝，逼调用方显式选裁切/补边/回上游
- Step 1 用 AskUserQuestion 问清封面是并列交付物还是成片首帧；选首帧时封面成为渲染的前置条件
- references/cover-and-title.md 新增封面两种位置对照、画幅不匹配的三条路、音频垫等长静音、首帧停留下限
- 交付契约新增 cover_as_first_frame / cover_source / first_frame_fit / first_frame_hold 与 first-frame.png
- skill-composition 记录 lov-channels-cover 为视频号封面上游，边界在封面已定稿；新比例档属于那个 Skill
- 补齐 frontmatter compatibility 与 description 触发语，修 README 安装段

## 0.1.0

- Added a portable media-production workflow for screen recordings, demos, source audio and BGM.
- Added timeline, media-probe and audio-QC helpers with FFmpeg/FFprobe integration.
- Added a verified video-channel case covering protected result audio, shortened upload UI, BGM ducking and publish read-back.
