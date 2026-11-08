---
name: lov-xiaonuan-style-media-creator
description: >
  依据带时间证据的晓暖说媒风格包（直播连麦定位切片），把连麦录像或新选题做成脚本、剪辑计划与包装成片，并核验风格、事实与授权边界。Use to plan or render call-in clips in this style.
license: MIT
compatibility: "Python 3.9+; jsonschema, PyYAML; FFmpeg and numpy for audio; Node.js with Remotion 4.0.517 for rendering; optional OpenCV, Pillow, librosa, swiftc (macOS Vision) for reanalysis."
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags: [video-style, call-in-clip, livestream, short-video, remotion, evidence]
---

# 晓暖说媒风格短视频

迁移参考作品的连麦定位推理、叙事结构、口语招式与包装模板（顶部双行标题、单行宋体字幕、资料卡、连麦头像窗、彩条加 1 kHz 分隔），不复制作者身份、素材或未经证实的观点。默认交付剪辑计划；用户提供自己的连麦或直播录像并取得来访者同意时，用内置模板出片。

## Triggers

### Activate when

- “用晓暖的风格，把这段连麦录像剪成切片。”
- “按晓暖说媒的连麦切片包装，给这个选题写脚本和剪辑计划。”
- “Use the 晓暖 call-in clip style to plan and render this recording.”

### Do not activate when

- 只要下载视频；把已授权链接交给下载能力（如 `lov-media-crawler`），本 Skill 不管理登录态。
- 要用原作者的视频、头像、声音、纸牌字样，或冒充她和她的服务；风格参考不构成身份授权。
- 要给真实来访者做心理诊断、承诺婚恋或职业结果，或把性别、职业刻板印象当事实输出。
- 只要通用剪辑或其他博主的风格；交给媒体制作能力或对应风格 Skill，不强套本模板。

## User Profile (cross-session)

每次运行读取 `skill.yaml`、共享 `user-profile/v1` 及本 Skill records。优先级为当前请求、项目上下文、Skill records、共享偏好、用户/品牌 Profile、安全默认值。

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-xiaonuan-style-media-creator --pretty
```

用户明确要求长期保留的偏好（如自己的栏目名、定位关键词、标题字体）才用 `scripts/profile_store.py record --confirm` 保存，并报告保存路径。凭据、私聊、来访者个人信息不写入 Profile。详见 `references/user-profile.md`。

## Skill Group Composition

运行前读 `references/skill-composition.md`。这是 Single Skill：画像、创作、校验和包装模板共享同一份风格 JSON 与时间线协议。下载、转写、发布只通过明确的文件交接，不是隐藏依赖。

## Authorship Integrity

创作前读 `references/authorship-integrity.md`。保留事实、例外和未解问题；来源里的市场判断与刻板说法是原作者的修辞，不是本 Skill 验证过的事实，不能迁移成确定结论。

## Workflow (MANDATORY)

### Step 0: Resolve and verify

绑定 `SKILL_DIR`，读取 `assets/xiaonuan-v0.1/style-profile.json`、`evidence.jsonl` 与 `references/creation-protocol.md`。

```bash
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" doctor
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-profile
```

画像含版本、训练/留出拆分、证据、适用条件、例外与局限；unknown 不补成硬规则。校验失败先修复，不绕过门禁。

### Step 1: Bind brief, facts and consent

按 `assets/brief.schema.json` 解析选题、`format`（call_in / solo_numbered / solo_mechanism）、时长、平台、事实与素材。建立事实台账，区分事实、判断、虚构演示与未知；虚构来访者标为 `fictional_demo`。
来访者的声音、条件和形象须有书面同意（`guest.consent`），只以头像出现。缺失会改变事实、身份、授权或制作范围时问一个聚焦问题；没有时长时说明采用样本中位数（约 5.5 分钟）或用户平台惯例。

### Step 2: Choose a narrative variant

按画像在 `call_in_positioning`、`case_to_viewpoint`、`solo_numbered_answer`、`solo_mechanism` 中选择；`service_intro` 只在用户提供自己经核实的身份与服务时借结构。
连麦个案按“求定位 → 报条件 → 短问追数字 → 复述并改写真问题 → 带区间的画像与取舍 → 收束 →（可选）对观众泛化”。市场框架换成目标领域可核查的维度；判断落在选择与市场，不对人格下诊断。

### Step 3: Generate

先写论证与 beat，再写对白，最后排声画；参考 `references/creation-protocol.md` 与证据，不凭形容词生成。可用 `prompt` 子命令为宿主 AI 准备输入包：

```bash
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" prompt --brief BRIEF --output PROMPT_JSON
```

输出 `facts-ledger.json`、`script.md`、`edit-plan.json`（`assets/edit-plan.schema.json`）、`style-review.json`。剪辑计划要求：第一段 5–20 秒前置高光；第二段 0.6–1.2 秒彩条分隔；单行字幕不带标点、每行不超过 16 个文本单位；两行标题一黄（或红）一白；可选资料卡；顶部 160 px、底部 260 px 安全区；-16 LUFS、True Peak 不高于 -1 dBTP。

### Step 4: Validate and review

```bash
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-plan --brief BRIEF --plan EDIT_PLAN
```

检查 Schema、连续时间线、分隔位置、字幕单行与语速、对白与字幕一致、事实与规则引用、对话密度、标题与资料卡顺序、安全区和响度目标。再人工审阅：改写是否有依据、画像是否可执行、有无读心或刻板判断、标题能否在对话里找到。自动通过不等于风格认可。

### Step 5: Optional production

仅在用户请求、录像与授权齐备时制作。

```bash
python3 "$SKILL_DIR/scripts/build_audio.py" --plan EDIT_PLAN --voice REF=VOICE_WAV --output WORK/public/audio/mix.m4a
python3 "$SKILL_DIR/scripts/build_render_plan.py" --plan EDIT_PLAN --media REF=media/FILE.mp4 --audio audio/mix.m4a --output WORK/src/data/render-plan.json
```

把 `templates/remotion` 复制到工作目录，按其 README 放入依赖、录像、音轨与标题字体后渲染 `XiaonuanClip` 与 `XiaonuanCover34`。验收：成片重新转写核对剪口、实测响度与峰值、`separator_scan.py` 复查提示音、扫描黑场与长静音、抽帧检查叠加元素、在 3:4 缩略尺寸检查封面。prepared、validated、rendered_review、human_approved、published 是不同状态；对外发布前确认来访者对这一版的同意。

## Refreshing references

新样本或重分析时读 `references/analysis-protocol.md`。先冻结样本与训练/留出拆分，再测量和写规则；留出样本只在画像冻结后读取，基于留出的修订另开版本。

```bash
python3 "$SKILL_DIR/scripts/analyze_media.py" --manifest SOURCES_JSON --output MEASUREMENTS_DIR
python3 "$SKILL_DIR/scripts/scan_layout.py" --manifest SOURCES_JSON --output LAYOUT_DIR --partition train
python3 "$SKILL_DIR/scripts/separator_scan.py" --manifest SOURCES_JSON --output SEPARATORS_JSON
python3 "$SKILL_DIR/scripts/speaker_hint.py" --media MEDIA --transcript ASR_JSON --output HINT_TXT
```

v0.2 候选修订记录在 `assets/xiaonuan-v0.1/holdout-report.json`。外部调用前说明发送哪些公开或已授权素材；凭据只来自环境或系统凭据存储。

## Dependencies

生成与审阅使用宿主 AI 与内置画像，不依赖固定云账号。校验需 Python 3.9+、jsonschema、PyYAML。出片需 FFmpeg、numpy、Node.js 与 Remotion 4.0.517。重分析需 OpenCV、Pillow、librosa、swiftc（macOS Vision OCR）与一个带时间戳的 ASR。下载、转写、拍摄、来访者授权、发布不是默认已完成的步骤。
