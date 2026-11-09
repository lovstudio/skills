---
name: lov-media-cloner
description: >
  复刻任一博主的视频风格：冻结样本与留出拆分，全片测量、转写与 OCR，写出带时间证据的八维规则，交付可校验的风格包、说明书与包装模板，可再封装成专属 Skill。Use to clone a creator's video style, e.g. 复刻这个博主的视频风格.
license: MIT
compatibility: "Python 3.9+ with jsonschema and PyYAML; FFmpeg/FFprobe, numpy, OpenCV and Pillow for measurement; macOS swiftc (Vision) for OCR; mlx-whisper or openai-whisper for local ASR, or imported Whisper/Tingwu/SRT transcripts; optional librosa; Node.js with Remotion 4.0.517 for the template."
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags: [video-style, style-clone, creator-analysis, evidence, holdout, remotion]
---

# 视频风格复刻

给一个博主（主页链接、账号名或一组作品链接），产出一份有证据的风格包：先选样并冻结训练/留出拆分，再测量、转写、逐条阅读训练样本，写出八个维度的规则。规则里的每句原话都能在转写里逐字找到，每个数字都能回读到测量文件；画像冻结之后才打开留出样本检验。可选交付包装模板、用你自己的素材做的演示，以及该博主的专属风格 Skill。迁移的是结构与手法，不复制作者身份、素材和未经证实的观点。

## Triggers

### Activate when

- “复刻一下小红书博主「某某」的视频风格。”
- “参考这个抖音账号的 10 条视频，提炼一份可执行的风格包和剪辑模板。”
- “把这个 B 站 UP 主的包装拆出来做成模板，再用我自己的录像做个演示。”
- “Clone this creator's video style from their profile and build an evidence-backed style pack.”

### Do not activate when

- 只要下载视频：交给 `lov-media-crawler`。
- 该风格已有专属 Skill（如 `lov-xiaonuan-style-media-creator`、`lov-laozhang-style-media-creator`），只是要按它出片：直接用那个 Skill。
- 文章文风交给 `lov-style-clone`；单张图的视觉要素交给 `lov-visual-clone`。
- 没有参考风格、只要剪辑已有素材：交给 `lov-media-creator`。
- 换脸、声纹克隆、搬运原片、冒充博主或其品牌：不做。风格参考不构成身份或素材授权。

## User Profile (cross-session)

每次运行读取 `skill.yaml`、共享 `user-profile/v1` 与本 Skill records。优先级为当前请求、项目上下文、Skill records、共享偏好、用户/品牌 Profile、安全默认值。

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-media-cloner --pretty
```

本 Skill 的 records：`projects_root`（工作区根目录）、`logged_in_browser`（读取需要登录的平台用的浏览器）、`asr`（转写后端与模型）、`split`（默认样本数与留出数）。用户明确说要长期沿用的值，用 `scripts/profile_store.py record --confirm` 保存并报告路径；凭据、Cookie、私聊和被分析博主的信息不写入 Profile。详见 `references/user-profile.md`。

## Skill Group Composition

运行前读 `references/skill-composition.md`。这是 Single Skill：取样、测量、规则、冻结、留出与模板共用一个工作区和同一套 Schema。下载、登录态读取、精剪、发布与封装都只通过文件交接，不是隐藏依赖。

## Authorship Integrity

写风格说明书和规则正文前读 `references/authorship-integrity.md`。每个判断都要追到规则、证据或测量；原作里的观点、市场判断和刻板说法是作者的修辞，不是本 Skill 验证过的事实；例外、留出未中和未知项必须保留。

## Workflow (MANDATORY)

所有命令都打印 JSON，失败时退出码非零。下文 `PY` 指带依赖的解释器：

```bash
PY="uv run --with jsonschema --with pyyaml --with numpy --with opencv-python-headless --with pillow python"
```

### Step 0: Resolve and resume

绑定 `SKILL_DIR`，运行 `$PY "$SKILL_DIR/scripts/cloner.py" doctor` 查看能力矩阵（OCR 需要 macOS 与 swiftc，本地转写需要 mlx-whisper 或 openai-whisper，没有时改用导入）。已有工作区先跑 `cloner.py status --project DIR`，从它给出的阶段继续，不重做已完成的步骤。

### Step 1: Scope the creator and the boundary

确认平台、主页、显示名和要复刻的格式期（封面、标题、包装换过版时只取当前格式，除非用户另有要求）。初始化工作区：

```bash
$PY "$SKILL_DIR/scripts/cloner.py" init --slug SLUG --creator "博主显示名" --platform xiaohongshu --profile-url URL --root PROJECTS_ROOT
```

默认交付风格包、说明书和模板预览；演示成片只在用户提供自己的素材并取得出镜者同意时做。会改变结果的未知项（格式期有歧义、要不要演示）只问一个问题。

### Step 2: Inventory and select samples

读 `references/sampling-and-platforms.md`。用登录态浏览器列出候选作品写入 `research/candidates.json`，在当前格式期内按子类型和互动量分层选 10–12 条，**在看任何测量之前**定下 2 条留出，写进 `research/sources.json`（`era_scope`、`selection`、每条的 `partition`）。

### Step 3: Download, register, freeze the split

授权链接交给 `lov-media-crawler` 下载并保留下载报告。登记哈希与参数后冻结拆分：

```bash
$PY "$SKILL_DIR/scripts/cloner.py" register --sources research/sources.json
$PY "$SKILL_DIR/scripts/cloner.py" freeze-split --sources research/sources.json
```

冻结后改动样本或拆分，所有工具都会拒绝运行；要换样本就开新版本。

### Step 4: Measure and transcribe the training set

读 `references/analysis-protocol.md` 与 `references/dimensions.md`。测量工具默认只处理训练集，留出集在画像冻结前是封存的。

```bash
M="$SKILL_DIR/scripts/measure.py"; S=research/sources.json
$PY "$M" media --manifest $S --out research/measurements
$PY "$M" layout --manifest $S --out research/layout --discover --colors
$PY "$M" tones --manifest $S --out research/tones/tones.train.json
$PY "$M" transcribe --manifest $S --raw research/transcripts/raw --out research/transcripts/normalized
$PY "$SKILL_DIR/scripts/cloner.py" metrics --sources $S --measurements research/measurements --transcripts research/transcripts/normalized --tones research/tones/tones.train.json --out research/training-metrics.json
```

已有转写（Whisper JSON、听悟 JSON、SRT）用 `measure.py import`。版式区域先用 `--discover` 看文字框分布，再按博主重写 `--zones`（默认值见 `assets/layout-zones.vertical.json`）。多人对话可用 `measure.py speakers` 做声学提示，角色仍以阅读判断为准。

### Step 5: Read, annotate, draft rules

完整阅读每条训练转写，看接触表与抽帧，必要时听 `audio-sample.mp3`；把阶段标注写进 `research/per-video-analysis.json`。按 `references/rules-and-evidence.md` 写 `research/rules-draft.json`：八个维度各有摘要，每条规则写观察、生成指令、强度、适用分母、置信、范围、例外、验收方式与证据。引文只给时间提示和原话片段，由脚本去转写里定位；不改写 ASR 原文，不补造例句或支持数。

```bash
$PY "$SKILL_DIR/scripts/cloner.py" build --draft research/rules-draft.json --sources $S --transcripts research/transcripts/normalized --out style-pack/SLUG-v0.1 --per-video research/per-video-analysis.json --project-root .
$PY "$SKILL_DIR/scripts/cloner.py" verify --pack style-pack/SLUG-v0.1 --sources $S --transcripts research/transcripts/normalized
```

构建失败时看 `research/rules-draft.build-report.json`：找不到的引文附有附近原文，留出证据、分母小于支持数都会被拒绝。

### Step 6: Freeze, then test on the holdout

```bash
$PY "$SKILL_DIR/scripts/cloner.py" freeze --pack style-pack/SLUG-v0.1 --sources $S --transcripts research/transcripts/normalized
$PY "$M" transcribe --manifest $S --partition holdout --frozen style-pack/SLUG-v0.1 --raw research/transcripts/raw --out research/transcripts/normalized
$PY "$SKILL_DIR/scripts/cloner.py" holdout-init --pack style-pack/SLUG-v0.1
$PY "$SKILL_DIR/scripts/cloner.py" holdout-check --pack style-pack/SLUG-v0.1 --write-summary
```

冻结后才读留出样本全文与抽帧，按写好的规则逐条记录 hit / partial / miss / not_applicable，每个“规则 × 留出样本”都要有结果；冻结前已在日志里见过的数值标 `contaminated`。修订意见写进 `suggested_revisions`，进入下一版，不回改冻结包。

### Step 7: Write the style guide

按 `references/deliverables.md` 在 `deliverables/` 写风格说明书：一句话本质、样本与方法、八维规则（带支持数与证据 ID）、叙事与版式模板、留出结果（含覆盖与污染）、禁用清单、未知项。先过 `lov-branding-consistency` 的读者可见文本门禁；引文与数字保持原样。

### Step 8 (optional): Template preview and demo

读 `references/template-and-demo.md`。把 `templates/remotion` 复制到 `work/remotion`，用画像里的 `layout_templates` 与颜色测量填 `src/data/style-tokens.json`，先渲染无素材的预览帧核对版式。演示只用用户自己的素材：`scripts/build_audio.py` 做连续音轨，写渲染计划，渲染后复查响度、真峰值、剪口与抽帧。

### Step 9 (optional): Package as a creator style Skill

用户要求封装时读 `references/packaging.md`，把冻结包、模板与案例交给 `lov-skill-creator`，生成 `lov-SLUG-style-media-creator`。发布只在用户要求时交给 `lov-skill-publisher`。

## States and reporting

`sampled`、`split_frozen`、`measured`、`drafted`、`verified`、`frozen`、`holdout_checked`、`guide_written`、`template_previewed`、`demo_rendered`、`packaged`、`published` 是不同状态，分别报告。自动校验通过不等于风格认可；不编造相似度分数、盲评或听审结论。留出结果按覆盖率、独立命中与受污染项分开写。

## Dependencies

核心台账只需 Python 3.9+、jsonschema 与 PyYAML。测量需 FFmpeg/FFprobe、numpy、OpenCV、Pillow；OCR 需 macOS Vision（swiftc 编译 `scripts/ocr_frames.swift`）；本地转写需 mlx-whisper（Apple Silicon）或 openai-whisper，首次运行会下载模型；说话人提示需 librosa；模板需 Node.js 与 Remotion 4.0.517。下载、登录态读取、精剪、发布与封装由相邻能力负责，不是默认已完成的步骤。
