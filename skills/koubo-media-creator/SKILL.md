---
name: lov-koubo-media-creator
description: >
  口播短片：输入一个主题，产出 AI 工具类竖版口播的调研、脚本、提词器、上屏素材与封面；作者录完口播后自动剪成上素材下出镜的成片。
  Use for 做一条口播短视频、topic to talking-head short.
license: MIT
compatibility: >
  Portable Agent Skills format. Python 3.9+; a persistent venv with numpy, pillow, mlx-whisper (Apple Silicon),
  opencc-python-reimplemented and jieba; Playwright with Chromium or system Chrome; FFmpeg/FFprobe; Node 20+, pnpm
  and Remotion 4 (assets/starter); macOS swiftc + Vision for the cover cut-out. Optional: VOICENGINE_API_KEY
  (Seed-TTS stand-in narration for animatics and aligner tests), OPENROUTER_API_KEY (Lyria music bed, about $0.08
  per track observed 2026-10).
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.3.1"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  suite: lov-film
  tags:
    - video
    - talking-head
    - short-video
    - wechat-channels
    - remotion
    - script-writing
---

# 口播短片 · Talking-head Short

输入一个主题，交付一条 AI 工具类竖版口播短片所需的一切：带出处的事实、按片型写好的口播脚本（过机械门禁）、
提词器与录制清单、上屏证据截图、封面；作者照提词器竖拍一条口播后，自动挑出每句最后念对的一遍、剪掉停顿，
排成「上半屏证据、下半屏作者、字幕压在交界」的竖版成片，配乐、封面、质检报告一起交。

片型语法从同类头部账号的公开作品量化而来（[references/style-grammar.md](references/style-grammar.md)）：
结果先行的钩子、约 6 字/秒的语速、上半屏不到 3 秒换一次证据、红框与橙色标注、黄色关键词字幕、一问收尾。
**复刻的是片型，不是人**：出镜、声音、名字、Logo、关注卡都是作者自己的。

本 Skill 是 `lov-film` 片型套件成员：片型 Skill 负责「这一类片子怎么做才对」；采访、动态图志、录屏长片、发布
各有专门 Skill（见 [references/skill-composition.md](references/skill-composition.md)）。

## Triggers

### Activate when

- 「输入一个主题，帮我做一条口播短视频，要那种 AI 博主上面放截图、下面露脸的风格」。
- 「这个选题帮我写口播稿和提词器，我自己录，录完你剪」。
- 「我录好了口播（recording/xxx.mov），按脚本剪成竖版成片，配字幕、红框和封面」。
- 「做一条『N 个 X，30 秒看懂』/『从夯到拉锐评』/『首发实测』的视频号短片」。
- Turn this topic into a vertical talking-head short: script, teleprompter, b-roll and cover; I will record.
- I recorded the script in one take with retakes; cut it into the finished short.

### Do not activate when

- 一场采访剪成短片 → `lov-interview-media-creator`；多人实录切条 → `lov-roundtable-clip`。
- 无实拍的动态设计片、编年/地图动画 → `lov-motion-media-creator`；三维 → `lov-3d-motion-media-creator`。
- Screen Studio 录屏长教程、Vlog、横版长片 → `lov-media-creator`。
- 只要公众号文章或长文 → `lov-article-creator` / `deep-tech-article`；只要改写文风 → `lov-style-clone`。
- 要用别人的脸、声音、账号名做视频，或生成数字人冒充真人：拒绝这部分，只提供片型层面的帮助。
- 只上传或发布已批准的成片 → `lov-media-publisher`。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`：作者名与账号名（水印、片尾）、官方 Logo（浅色版）、头像、
形象照、字体、默认 ASR、命名规则、输出目录，以及 `skills.lov-koubo-media-creator.records`
（默认片型、语速、TTS 音色、片尾一句话、默认平台）。顺序：当前请求 → 项目上下文 → 本 Skill 记录 → 共享偏好 →
用户/品牌 Profile → 默认值。作者直接说出的长期偏好立即写回并报告路径：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record --skill-id lov-koubo-media-creator --path records.end_line --value "关注我，一起把 AI 用进真实工作流" --confirm
```

推断值只留在本次。完整契约见 [references/user-profile.md](references/user-profile.md)。

## Authorship Integrity

口播脚本是作者稿，写之前读 [references/authorship-integrity.md](references/authorship-integrity.md)。
「烧了多少积分」「测了几天」「以前要折腾半天」这类第一人称经历与数字，只写作者给过或可核实的；没有就不写。
每个数字、版本号、价格进 `facts[]` 并带出处。

## Hard gates

0. **不冒充。** 出镜、声音、名字、水印、Logo、片尾卡只用作者本人的；不用参考博主的口头禅原句、素材、截图、
   封面图；不生成数字人冒充任何真人。`check_script.py` 的禁用表与 style-grammar §0 是底线。
1. **事实有出处。** 含数字、版本、价格、用户量的句子必须引用 `facts[]` 的 id；每条事实写出处与核对日期。
   时效性信息（新模型、新功能、价格）先查一手来源；查不到就改写或删掉，不猜。
2. **脚本过门禁。** `check_script.py` 0 ERROR 才出提词器；WARN 逐条处理或在交付说明里给理由。
3. **证据是真的。** 上屏素材只来自作者自己的屏幕与操作、公开网页（截图注明来源）、本片按事实生成的数据卡；
   `capture.py term` 只渲染命令的真实输出，不手写终端内容。
4. **切点经过核验。** `align.py` 的 `review` 列表为空或逐条人工确认；句首句尾落在静音缝里，不吃字。
5. **声音过门禁。** 一条按本片内容生成或选定的音乐床，最后挂载、只挂一次；母带 −16 ±1 LUFS-I、≤ −1 dBTP。
6. **成片过质检。** `finish.py` 全部检查通过（1080×1920、30 fps、帧数 = 时间线、bt709、≤ 10 Mbps、
   重转写吃字率 ≤ 3%，CER 只作参考）；1 fps 联系表逐页看过。数字通过不等于验收。
7. **封面可读。** 3:4 在 270×360、16:9 在 480×270 下一眼读完主标题；有官方 Logo；标题不压脸。
8. **状态分明。** `animatic`（TTS 占位配音 + 占位出镜）只用于预审节奏与包装，永远不当成片交付或发布；
   状态用 `draft-script` / `awaiting-recording` / `animatic` / `rendered` / `approved` / `published`。
9. **付费先报价。** TTS、AI 配乐、云端 ASR 先说单价与本次预估，每次调用记进 `ledger/costs.jsonl`。

## Workflow (MANDATORY)

命令、产物与目录见 [references/pipeline.md](references/pipeline.md)；脚本字段见
[references/script-format.md](references/script-format.md)；「对」的标准见 [references/style-grammar.md](references/style-grammar.md)。

### Step 0: 解析运行环境

- `SKILL_DIR` = 本 Skill 目录。确认 `scripts/*.py`、`assets/starter`、`assets/tools/cutout.swift`、`assets/templates/script.example.json` 都在。
- 持久虚拟环境 `$PY`：numpy、pillow、mlx-whisper、opencc-python-reimplemented、jieba（也可每次 `uv run --with …`）。
  Whisper 模型（`mlx-community/whisper-large-v3-turbo`，约 1.6 GB）已缓存时设 `HF_HUB_OFFLINE=1`；经 SOCKS 代理下载需 `socksio`。
- ASR：先读 Profile 的默认 ASR。作者的默认是云端服务（如通义听悟）时，先用它出逐字时间戳 JSON（`[{w, s, e}]`），
  交给 `align.py --words`；那条通道实际不可用时才回退本机 Whisper，并告诉作者专名要人工核对。
- 一集一个目录（`EPISODE/`）：`work/ brand/ broll/ broll-src/ recording/ music/ deliverables/ qc/ ledger/`。
  作者原片只读；大体积媒体不放进笔记库。

### Step 1: 选题、片型与事实

- 从主题定受众与片型（list / tips / review / tier / case，见 style-grammar §2），写一句「看完能得到什么」。
- 调研：一手来源优先（官网、文档、发布说明、作者本机实测）；可交给 `lov-fact-check` / `deep-research` 做上游核查。
  每条事实写进 `script.json` 的 `facts[]`：`id`、`claim`、`source`（URL 或本机证据路径）、`checked`（日期）。
- 需要作者亲手操作的证据（录屏、真实结果）列进分镜，标 `capture.note`，录口播前后补拍。

### Step 2: 写脚本

- 按 style-grammar §3 写 `work/script.json`（字段见 script-format）：第一句就是结果并配证据画面；第二、三句立悬念或痛点；
  每个要点「操作 → 证据 → 一句评价」；结尾一问。每句 8–22 字，一句一个镜头。
- 布局每 2–4 句换一次；`split` 占六到七成；`face` 给悬念句、判断句和收尾；`broll` 给前后对比与细节。
- 封面：`cover.headline` 2–3 行、每行 ≤ 7 字；`cover.expression` 写清封面表情，提词器会提醒作者先拍 3 秒。
- `python3 check_script.py work/script.json` 到 0 ERROR。改写不求一次过，按报错逐条改。

### Step 3: 上屏证据

- 公开网页与文档：`capture.py url`（或在 b-roll 上写 `capture.url` 后 `capture.py script` 批量补）。
- 命令或工具输出：先把真实输出存成文本，再 `capture.py term`。
- 数据卡、对比卡：按 `facts[]` 写 HTML（`broll-src/`），`capture.py url` 截成 PNG；卡上写采样日期与口径。
- `boxes` / `focus` 用归一化坐标 `[x, y, w, h]`，看过截图再定；红框只圈口播正在讲的东西。

### Step 4: 录制包与样片

- `teleprompter.py` → `deliverables/teleprompter.html`（空格开始、←→ 换句、↑↓ 语速、M 镜像）、`script.md`、`shotlist.md`。
- 建议先出 animatic 给作者预审：`tts.py`（占位配音，先 `--dry-run` 报字数）→ `align.py` → `setup_project.py` →
  `build.py --still <形象照> --placeholder --animatic` → `mix.py` → `finish.py`。小尺寸形象照只按原尺寸放在占位框里，不拉伸。
- 交付录制包与 animatic，状态 `awaiting-recording`，**停下等作者的录像**。

### Step 5: 录后对齐

- 作者交来一条竖拍原片（放进 `recording/`，只读）。`align.py work/script.json recording/<原片> --out work/takes.json`。
- 看输出：每句 `ok/low/missing`、选中的那一遍、`discarded`。`low/missing` 逐条回听确认，必要时请作者补录这一句。
- 抽一帧看作者的脸在画面里的高度，作为 `build.py --face-y`（脸中心 / 画面高，常见 0.28–0.38）。

### Step 6: 构建、封面与配乐

- `setup_project.py EPISODE`（首次）→ `build.py … --recording recording/<原片> --logo <浅色官方 Logo>`；
  缺素材时可先 `--allow-missing` 预览。
- 封面人像：从开头 3 秒封面表情里挑一帧（`ffmpeg -ss … -frames:v 1`），`cutout` 抠成透明 PNG，写进 `cover.cutout`；
  `cover.cards` 选 1–2 张本片证据截图。
- 配乐：写一句音乐简报，`gen_bgm.py` 生成 1–2 个候选（先报价）；选一条，`mix.py --bgm …`。

### Step 7: 渲染与质检

- `finish.py EPISODE --name <命名规则> --version v0.x`：渲染成片与 3:4、16:9 封面，写 `qc/report-<版本>.json`。
- 逐页看 `qc/sheet-*.jpg`（布局切换、红框位置、字幕不压脸、标注不撞字幕）和封面缩略图；有问题改数据或模板后重渲。
- 需要时 `npx remotion studio` 实播检查一段含多个切点的区间。

### Step 8: 交付

- 交付说明：状态、成片与封面路径、时长、质检结果、事实清单与出处、AI 生成内容清单（TTS、配乐、生成卡片）、费用汇总、
  未验证项（例如配乐未人工试听）。
- 发布交给 `lov-media-publisher`，只在作者批准成片后进行。

踩过的坑见 [references/pitfalls.md](references/pitfalls.md)。

## Dependencies

- Python 3.9+：numpy、pillow、mlx-whisper、opencc-python-reimplemented、jieba；Playwright（Chromium 或系统 Chrome）。
- FFmpeg / FFprobe；Node 20+、pnpm、Remotion 4.0.517（`assets/starter`，`pnpm-workspace.yaml` 已放行 esbuild 构建）。
- macOS `swiftc` + Vision（`assets/tools/cutout.swift`，封面人像抠图）。
- 字体：一款支持 900 字重的中文无衬线（如 Noto Sans SC 可变字体），可选展示字体（如 Smiley Sans）。
- 可选：`VOICENGINE_API_KEY`（Seed-TTS 2.0 占位配音）、`OPENROUTER_API_KEY`（Lyria 配乐），只从环境变量读。

## Validation

```bash
python3 scripts/validate_skill.py .
for s in check_script teleprompter capture align tts build setup_project mix finish gen_bgm; do
  python3 scripts/$s.py --help >/dev/null || echo "FAIL $s"
done
python3 scripts/check_script.py assets/templates/script.example.json   # 示例只演示字段：时长 ERROR 属预期
```
