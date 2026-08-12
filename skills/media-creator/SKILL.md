---
name: lov-media-creator
description: >
  将录屏、演示视频和音频素材整理为结构清晰、保留关键原声、完成混音与封面交付的可发布成片；触发语包括“制作视频号成片”“剪这个录屏”和“create a publish-ready video”。
license: MIT
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - media-production
    - video-editing
    - ffmpeg
    - audio-mix
    - delivery-qc
    - cover-direction
  compatibility: "Python 3.8+, FFmpeg/FFprobe, optional Pillow or an image tool for cover assets."
  dependencies:
    - ffmpeg
    - ffprobe
---

# lov-media-creator — 从素材到可发布成片

把录屏、演示素材、原声和 BGM 组织成可发布的视频成片，同时交付剪辑清单、封面方向和可回读的质检报告。叙事重点放在真实工作流和实际问题上，工具只作为过程中的一个环节出现。

## Triggers

### Activate when

- 用户说“把这段录屏剪成视频号成片，保留最后有声音的成果段”。
- 用户说“压缩上传卡顿、加 BGM、做 16:9 封面，并给我质检报告”。
- 用户希望把长录屏整理成有开场、问题、操作证据和最终结果的短视频。
- User asks to create a publish-ready video from a screen recording while preserving the original result audio.

### Do not activate when

- 用户只要生成标题、正文或社交平台文案；交给文案或内容策略能力。
- 用户只要学习字幕、词汇注释或 ASS 人物卡；交给 `lov-subtitle-freedom-skill`。
- 用户只要章节进度条、透明章节层或剪映章节包；交给 `lov-video-chapter`。
- 用户已经有最终 MP4，只要求上传并回读发布状态；交给 `lov-publish-wechat-channels`。

## User Profile (cross-session)

每次运行都读取 `skill.yaml` 声明的 `user-profile/v1`：用户语言与时区、品牌语气、工作区输出位置、共享偏好，以及 `skills.lov-media-creator` 下的 Skill 专属记录。解析顺序是当前请求、项目上下文、Skill 记录、共享偏好、用户/品牌 Profile、默认值。

用户直接说出的长期剪辑偏好或品牌事实，通过 `scripts/profile_store.py record --confirm` 写回 Profile，并在结果中报告保存路径。源代码保持可移植，不写入个人绝对路径、凭据或临时素材位置。完整契约见 [`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

运行前阅读 [`references/skill-composition.md`](references/skill-composition.md)。相邻 Skill 只通过文件、JSON、字幕或成品视频交接，不作为此 Skill 的隐藏运行依赖。

## Workflow (MANDATORY)

**必须按以下顺序执行。**

### Step 0: 解析运行环境

- 使用环境中的 `SKILL_DIR`；没有时从当前 Skill 上下文推断安装目录。
- 先验证 `$SKILL_DIR/scripts/media_probe.py`、`$SKILL_DIR/scripts/timeline_check.py`、`$SKILL_DIR/scripts/audio_qc.py`、`$SKILL_DIR/scripts/profile_store.py` 是否存在。
- 再验证 `$SKILL_DIR/references/media-workflow.md`、`$SKILL_DIR/references/edit-manifest.md`、`$SKILL_DIR/references/audio-mix.md`、`$SKILL_DIR/references/cover-and-title.md`、`$SKILL_DIR/references/delivery-contract.md` 是否存在。
- 视频检查或渲染需要 `ffprobe` 与 `ffmpeg`。封面生成只在明确需要新图时启用 Pillow 或图像工具。
- 永远不覆盖源视频、源音频或原字幕；输出先落到独立的 `deliverables` 或用户指定目录。

手工运行脚本时：

```bash
export SKILL_DIR="/path/to/lov-media-creator"
```

每次调用都解析 `context.profile`。若用户明确提出要长期保留的剪辑原则、音频偏好或品牌事实，调用 `scripts/profile_store.py record` 并带 `--confirm`，随后简短报告保存路径。

### Step 1: 明确输入与成片目标

记录以下事实，不替用户臆造内容：

1. 源视频、补充片段、原声轨、BGM、截图和已有封面；输入可为单个录屏或多个素材。
2. 目标平台、画幅、预期时长、受众、发布标题、封面文案和是否需要字幕。
3. 必须保留的证据段，尤其是最终结果播放、真实声音、状态回读或失败反馈。
4. 交付文件：成片、封面、剪辑清单、音频/编码质检报告，以及可选的发布交接信息。

默认输出规格为 16:9、1920×1080、30fps、H.264、AAC 48kHz；明确请求或 Profile 有其他设置时，以当前请求为准。

### Step 1.5: 读取相邻能力与交接边界

先看 `references/skill-composition.md`，判断是否需要可选交接：

- 章节条：交给 `lov-video-chapter`，输入为已确认的成品或字幕，输出为章节项目/透明层。
- 学习字幕：交给 `lov-subtitle-freedom-skill`，输入为成片或原字幕，输出为保持原时间轴的 SRT/ASS。
- 新封面图：交给 `lov-image-creator`，输入为封面方向 JSON 或文字 brief，输出为 PNG/可编辑 HTML。
- 视频来源获取：交给 `lov-media-fetch`，输入为检索需求，输出为经过核验的本地素材。
- 微信视频号发布：交给 `lov-publish-wechat-channels`，输入为已质检成片，输出为发布状态与回读证据。

本 Skill 负责最终成片的编辑判断、音频完整性和交付门禁；可选下游不得替代这些验收。

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
- 避免模板化的 AI 句式、空泛的“重新定义效率”和过量大字。封面优先展示状态、界面证据或前后对照。
- 剪辑节奏先服务理解，再服务刺激；成果段出现后，隐藏解释性字幕和多余顶栏，让真实画面与原声完成收束。

### Step 4: 编辑画面并保护关键原声

1. 先按 EDL 做粗剪，再做一次连贯性检查；转场、加速和裁切都要服务信息密度。
2. 上传弹窗只保留必要的进入、选择和完成信号；卡顿段短暂呈现即可，不让等待成为视频主体。
3. BGM 是氛围层，不是主角。有人声、点击反馈或最终视频播放时，降低 BGM；成果段需要听清原声时可暂时只保留原声。
4. BGM 采用淡入淡出和 ducking，避免循环接缝、突兀起音与尾部截断。具体滤镜和参数见 [`references/audio-mix.md`](references/audio-mix.md)。
5. 若源素材本身没有可用原声，标记这一事实，不用 BGM 冒充真实反馈。

### Step 5: 渲染成片

使用 FFmpeg 在最终阶段统一重编码，避免多次有损导出。常用输出参数：

```bash
ffmpeg -y -hide_banner \
  -i SOURCE_VIDEO \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,fps=30" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -movflags +faststart OUTPUT_MP4
```

若涉及多段画面、原声与 BGM，使用 `filter_complex` 显式映射视频与音频；不要依赖默认流选择。输出成片、封面、EDL 和报告放在同一交付目录，源素材保持原位。

### Step 6: 做媒体与音频质检

```bash
python3 "$SKILL_DIR/scripts/media_probe.py" \
  --input OUTPUT_MP4 \
  --output DELIVERABLE_DIR/final-probe.json \
  --pretty

python3 "$SKILL_DIR/scripts/audio_qc.py" \
  --input OUTPUT_MP4 \
  --output DELIVERABLE_DIR/audio-qc.json \
  --pretty

ffmpeg -v error -i OUTPUT_MP4 -f null -
```

逐项回看开头、每个关键切点、最终结果连续播放和结尾。至少确认：最终段仍有声音、BGM 没盖住人声、画面没有黑帧或意外静帧、上传弹窗没有占据主体、封面缩略图仍能读出主题。目标响度参考 `-16 LUFS-I ±1.5`，True Peak 控制在 `-1 dBFS` 以下；实际值以报告为准。

### Step 7: 交付与发布交接

按 [`references/delivery-contract.md`](references/delivery-contract.md) 生成交付报告，分别写清：

- `render_status`：成片是否导出且通过解码与参数检查；
- `audio_status`：原声、BGM、响度和峰值是否通过；
- `creative_status`：标题、封面、叙事和证据段是否完成；
- `publish_status`：是否交给发布 Skill、是否已发布、是否有线上回读。

“已渲染”“已上传”“已发布”“已回读”是四个不同状态。只有出现真实平台回读证据时，才把 `publish_status` 写成 `published`。

## Validation

完成前运行：

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/media_probe.py" --help
python3 "$SKILL_DIR/scripts/timeline_check.py" --help
python3 "$SKILL_DIR/scripts/audio_qc.py" --help
```

同时检查 `skill-card.yaml`、`skill-card.md`、`cases/cases.json` 和 `pricing-card.yaml`。至少保留一个真实 Input → Prompt → Output 案例，记录三项以上有证据的质量维度，并标明免费/付费渠道状态。

## Dependencies

- Python 3.8+ 标准库；`PyYAML` 用于 Skill 结构验证。
- FFmpeg 与 FFprobe 用于视频解码、转码、帧提取和音频质检。
- 可选 Pillow、Playwright 或图像生成能力，用于新封面资产；已有封面时不强制安装。
- 可选的字幕、章节和视频号发布 Skill 只通过交付文件交接，不是本 Skill 的安装依赖。
