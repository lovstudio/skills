---
name: lov-laozhang-style-media-creator
description: >
  依据带时间证据的老张心理视频风格包，把新选题和事实素材写成口播脚本、分镜与剪辑时间线，并核验风格和事实边界。Use to create evidence-grounded short videos in this reference style.
license: MIT
compatibility: "Python 3.9+; jsonschema, PyYAML; optional FFmpeg, OpenCV, numpy, Pillow and macOS Vision for reference analysis."
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags: [video-style, short-video, narration, storyboard, evidence]
---

# 老张心理风格短视频

迁移参考作品的解释路径、叙事结构、口语节奏和声画编排，不复制作者身份、未经证实的观点或未授权素材。默认交付脚本与拍摄/剪辑方案，只有用户要求且具备素材时才制作成片。

## Triggers

### Activate when

- “用老张心理风格，把这个新选题做成口播脚本和分镜。”
- “参考这些视频提取风格，给下一个 AI 一个可执行的风格包。”
- “Create a new video script and edit plan using this evidence-grounded reference style.”

### Do not activate when

- 只要下载视频；将已授权链接交给下载能力，本 Skill 不管理登录态。
- 要复制原作者人脸、声纹或冒充原作者；风格参考不构成身份授权。
- 要诊断真实人物、编造隐私、保证咨询疗效；不以风格之名生成这些断言。
- 只要通用剪辑而无需本风格；交给媒体制作能力，不强套模板。

## User Profile (cross-session)

每次运行读取 `skill.yaml`、共享 `user-profile/v1` 及本 Skill records。优先级为当前请求、项目上下文、Skill records、共享偏好、用户/品牌 Profile、安全默认值。

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-laozhang-style-media-creator --pretty
```

仅用户明确要求长期保留的偏好才通过 `scripts/profile_store.py record --confirm` 保存。凭据、私聊和推断出的心理特征不能写入 Profile。详见 `references/user-profile.md`。

## Skill Group Composition

运行前读 `references/skill-composition.md`。这是 Single Skill，提取、生成、验收共享同一风格协议。下载、ASR、拍摄、配乐、渲染与发布只做明确文件交接，不是隐藏 sibling 依赖。

## Authorship Integrity

创作前读 `references/authorship-integrity.md`。保留事实、例外和未解问题。来源中的心理推断、疗效承诺不是本 Skill 验证过的事实，不能迁移为确定结论。

## Workflow (MANDATORY)

### Step 0: Resolve and verify

绑定 `SKILL_DIR`，读取 `assets/laozhang-v0.1/style-profile.json`、`evidence.jsonl` 与 `references/creation-protocol.md`。

```bash
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" doctor
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-profile
```

画像须有版本、训练/留出拆分、证据、适用条件、例外和局限。unknown 不得补成硬规则。校验失败先修复，不绕过门禁。

### Step 1: Bind brief and facts

解析选题、受众、时长、真实事实和可用素材，使用 `assets/brief.schema.json`。
缺失会改变事实、商业承诺、人物身份或制作范围时问一个聚焦问题。无时长时说明采用样本中位数；短版本按叙事功能压缩，不照搬原片秒数。
建立事实台账，区分事实、解释、虚构演示与未知。第一人称经历、资质和来访案例只能由用户提供。
默认使用用户自己的出镜和音色；原作影视片段、照片和音乐不是新作品的已授权素材。

### Step 2: Choose a narrative variant

按画像选择案例拆解、概念训练、识别清单或后续策略型，不强塞一种开头结尾。
先建立认知张力，再从行为/场景走向机制解释，最后回到观众的选择。
“不是 A，而是 B”是解释工具，不是每段都要出现的口头禅。
前置高光、服务 CTA、系列预告有明确样本例外，不是全局必选项。
不复制原作者的商业承诺与身份；机制解释须保留反例和不确定性。

### Step 3: Generate

先写论证与叙事，再写句子，最后安排声画；参考 `references/creation-protocol.md` 和原片证据，不凭抽象形容词生成。
输出 `facts-ledger.json`、`script.md`、`edit-plan.json`、从同一时间线派生的 `storyboard.json`、`style-review.json`。
每个时间段包括起止、功能、口播、事实 ID、规则 ID、镜头、字幕、声音和素材需求。
语言容量必须与目标片长、选定语速和停顿相容。不能为凑时长篡改事实。

### Step 4: Validate and revise

```bash
uv run --with jsonschema --with pyyaml python "$SKILL_DIR/scripts/style_media.py" validate-plan --plan EDIT_PLAN --brief BRIEF
```

检查 Schema、连续时间线、正时长、事实引用、素材需求、规则引用、文本容量、字幕行数、声画触发和未知字段。
再审阅论证跳步、读心、照抄和虚构亲历。自动门禁通过不等于风格一模一样；人类盲评、听审、成片观看与用户认可分别报告，不编造分数。

### Step 5: Optional production

仅用户请求且素材权利、出镜/音色、实际渲染能力齐备时制作视频。脚本、分镜和静态预览不能称为成片。
编码后回读实际字幕、时长、声画和响度；学习组织方式，但不复现来源中超限的 True Peak，记录安全输出参数与参考样本的有意偏离。

## Refreshing references

新样本/重分析时读 `references/analysis-protocol.md`。保留原视频、清单、哈希、旧画像和拆分，更新版本。
该版本留出样本不得进入规则选择；基于留出结果修订须另开版本并重新留出。

```bash
python3 "$SKILL_DIR/scripts/analyze_media.py" --manifest SOURCES_JSON --output MEASUREMENTS_DIR
python3 "$SKILL_DIR/scripts/prepare_transcripts.py" --input TINGWU_JSON_DIR --output ALIGNED_DIR
```

外部调用前说明发送哪些公开/已授权素材。凭据只来自进程环境或系统凭据存储，不能进入包、Profile、提示词或日志。

## Dependencies

生成/审阅使用宿主 AI、内置画像与用户 brief，不依赖指定云账号。
校验需 Python 3.9+、jsonschema、PyYAML，可由 uv 提供。
重分析需 FFmpeg/FFprobe、numpy、OpenCV、Pillow；macOS Vision OCR 可选。
下载、转写、出镜、配音、音乐授权、渲染、发布不是默认已完成的隐式步骤。
