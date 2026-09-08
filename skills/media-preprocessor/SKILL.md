---
name: lov-media-preprocessor
description: >
  对实录视频做全片增强与内容分段，保留有价值内容、剔除已核验无效区间，输出素材库与源时间码。Use when 用户说“全片提亮”“智能分段”“清理课程素材”或 “preprocess and segment video”。
license: MIT
compatibility: "Python 3.9+, NumPy, OpenCV, FFmpeg/FFprobe; PyYAML for validation. Semantic judgment needs host vision and timestamped speech evidence. Optional local ASR: whisper-cli or mlx-whisper with supplied model weights."
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.2.0"
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags: [media-preprocessing, video-enhancement, semantic-segmentation, source-fidelity]
---

# 视频素材精整 · Video Prep

把原始实录准备成明亮、清楚、按内容组织的可剪辑素材库。交付经过统一增强的分段视频、连续取舍清单、源时间码映射和可选合并版本。原片只读。默认保留内容顺序、原速、原声、画幅、帧率和真实课件，不添加字幕、BGM、Logo 或海报包装。

需要从整场实录继续做独立传播切片时，用 [成片交接契约](references/creator-handoff.md) 导出经过文件与时间码核验的 `creator-handoff.json` 和可直接打开 MP4 的列表，交给 `lov-media-creator`。完整增强版不等于完成内容选片；该边界不另建 Skill。

## Triggers

### Activate when

- “这组明亮效果不错，对全片这样处理，并去掉低质量、无意义的部分。”
- “把线下课程实录提亮、分主题切段，保留有内容的讲解和演示。”
- “Help preprocess and segment this recording into enhanced, useful source clips.”

### Do not activate when

- 只挑朋友圈照片：交给 `lov-video-moments`。
- 只要字幕或章节条：使用转录或章节能力。
- 要精剪、动画、包装和发布规格的最终成片：交给 `lov-media-creator`。
- 上传或发布：另循发布授权；本 Skill 止于本地验收。

## Runtime context

每次读取 `skill.yaml` 与 [Profile contract](references/user-profile.md)，并执行：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-media-preprocessor
```

当前请求/参数 → 环境 → 项目上下文 → 本 Skill records → 共享 Profile → 默认值。只保存用户直接要求跨会话复用的视觉目标、剪辑倾向和输出偏好；单次路径、字幕、人物身份和推断值不写长期记录。

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record --skill-id lov-media-preprocessor --path records.visual_style --value '"bright-documentary"' --confirm
```

保存后报告 canonical Profile 位置。先读 [组合边界](references/skill-composition.md)：这是 Single + 独立 Python CLI，各阶段共享 source/analysis/plan 契约。外部 Skill 只通过文件交接。新增段名和说明使用 branding 门禁；转录、课件与源标识符不改写。

## Workflow (MANDATORY)

### 1. 输入与完成标准

直接使用已提供的视频和已认可的视觉参考。只有缺失信息实质影响结果时，使用宿主 AskUserQuestion 或等价提问工具；不让用户选择技术引擎。

```bash
python3 "$SKILL_DIR/scripts/media_preprocessor.py" probe "$VIDEO"
```

确认时长、音视频轨、尺寸、帧率、色彩标记、源身份和实际可用空间。大原片直接随机定位，不复制几十 GB 到系统盘。先短窗估算速度与体积，再选择足够空间的派生目录；保留源工程的独立轨道。

默认按完整内容单元分段，不固定段数和时长。必须覆盖全片；稀疏采样不能声称逐帧审阅。分别记录分析、转录、增强、语义判断和渲染的实际状态。

### 2. 校准连续视频的明亮方向

读取 [增强契约](references/enhancement-contract.md)。以已认可照片的主体清楚、肤色自然、暗部可见和投影可读为目标，选择逆光人物、白色/暗色课件等代表窗口。视频使用保持帧间稳定的摄影处理，不逐帧生图重画人物或文字。

先写含源身份、全覆盖时间线和 `grade` 的计划，用 `render --preview 12` 验证代表片段。实际回读输出帧、连续运动和音轨；黑位发灰、皮肤过曝、闪烁或课件不可读要修正。照片风格认可不能替代视频验收。

若用户同时要完整增强版，可在技术索引完成后用 `plan --enhancement-only` 生成明确不做删减的计划，并独立渲染。此步骤不依赖转录；所有区间标记 `review`，不能称为完成语义审阅。完整增强版和精简分段版分目录交付。

### 3. 全片技术索引与转录

```bash
python3 "$SKILL_DIR/scripts/media_preprocessor.py" analyze "$VIDEO" --interval 30 --workers 2 --output "$RUN/data/analysis"
```

生成源指纹、采样帧、亮度/模糊度/暗场诊断、连续音频能量窗口和单声道分析音频。`subject_luma` 是画面下部区域亮度代理，不能宣称自动定位了人脸。质量信号只标记待查窗口，不直接判定内容价值。

已有同源时间戳转录优先复用；否则使用宿主 ASR 或包内本地适配器：

```bash
python3 "$SKILL_DIR/scripts/media_preprocessor.py" transcribe "$RUN/data/analysis/audio-16k.wav" --model "$ASR_MODEL" --language zh --output "$RUN/data/transcript"
```

模型使用当前可用的质量档及显式参数，不因长片暗中换快档。CLI 不自动下载模型或上传私有课程。云端遵循宿主授权、费用与数据边界。本地适配器按带上下文的音频块运行 whisper-cli，保留原始输出、模型/音频哈希与进度。

Apple Silicon 可使用同模型的 MLX 本地实现：在装有 `mlx-whisper` 的 Python 环境中加入 `--backend mlx --model "$MLX_MODEL_DIR"`，目录须包含配置与实际权重，CLI 不隐式下载。只对分析音轨规范响度、关闭跨块重复提示，并保留原始模型输出和低置信度信息；原片原声不因此改动。

长静音和远处谈话导致循环幻觉时，可加 `--vad`（需 `silero-vad`）。它仅为 ASR 选择保守的疑似人声窗口，保留 1 秒前后余量、模型哈希和原时间戳。被跳过的窗口仍在完整视频索引中，不能视为已确认无内容或直接删除。

`analyze`、`transcribe` 中断可加 `--resume`，只复用源/模型/参数匹配的结果。明确复用旧转录时可传 `--reuse-asr "$OLD_ASR_RUN"`：音频、模型和块坐标必须一致，逐块验证哈希并保留导入来源；未完成块不导入。转录 `status=complete` 前不能声称完成全片语义分析。

### 4. 智能取舍与语义分段

读取 [分段契约](references/segmentation-contract.md)。Agent 阅读完整转录、查看全片采样与异常窗口。按观点、问题、方法、演示、结果、答疑和分享者变化组织完整内容；不能均分视频或只取声音最大的部分。

- `keep`：有独特信息、有效演示或必要上下文；质量差但内容重要时优先增强保留。
- `drop`：经内容、画面与边界核验的无效等待、废弃尝试或不可用空场，且无独有有效内容。
- `review`：证据不足或可用性不确定，默认保留并标注，不能静默删除。

写 `media-preprocess-plan/v1` 全覆盖时间线，再校验：

```bash
python3 "$SKILL_DIR/scripts/media_preprocessor.py" plan "$RUN/data/analysis/analysis.json" --decisions "$RUN/data/decisions.json" --output "$RUN/data/plan.json"
```

不带 `--decisions` 只生成技术提案。每个删除项记录具体证据和实际 review，不为过校验填虚假布尔值。剪口检查原声证据和前后语义，保留词头词尾；静音、ASR 标点和质量分数不能单独落刀。宿主不能直接听审时，使用完整转录、词级时间估计、连续波形及剪口画面保守定位，并明确记录未听审；证据冲突或可能损失有效内容时扩大保留范围或设为 review。

### 5. 顺序渲染与源时间映射

```bash
python3 "$SKILL_DIR/scripts/media_preprocessor.py" render "$VIDEO" --plan "$RUN/data/plan.json" --output "$RUN/videos" --concatenate
```

默认高质量 CPU H.264；平台支持时可显式选 `--codec h264_videotoolbox --bitrate-mbps 14`，短窗回读课件与肤色后再处理全片。编码参数不宣称无损。每段 grade 稳定，可在明确场景变化后重新校准，不追逐每帧曝光。

macOS 已安装 Swift 编译工具时，可加 `--engine metal --codec h264_videotoolbox`。包内原生后端将数值增强采样为 65³ 色彩查找表，由 Core Image 处理连续帧；必须先对照 FFmpeg 样片，并验证片段音画同步。跨平台默认仍为 FFmpeg。编译产物和日志只写入运行目录，源码包不含二进制。

已完成整片增强、随后才完成内容计划时，可用 `--prepared-run "$FULL_ENHANCED_RUN"` 复用同源、完整、同 grade 的增强主片，以 FFmpeg 精确重编码分段。工具核验主片哈希及全覆盖源映射，且不会再次提亮；这是二次编码，需要适当码率与回读，不宣称无损。不能用普通 stream copy 掩盖 B 帧剪口的帧数或时长偏差。

导出 `keep` 与 `review`。删除段仍保留在原片和计划中。源起止与新时间线写入 manifest；可将已编码段无再次压制地合并为 `prepared.mp4`。`--resume` 验证源、计划、参数和完成文件哈希，不覆盖不明成片。

### 6. 最终回读与交接

```bash
python3 "$SKILL_DIR/scripts/media_preprocessor.py" verify "$RUN/videos" --decode
```

核对文件解码、时长、音轨、起始同步、尺寸、哈希和源时间映射；实际看代表片段、场景变化与所有高风险剪口。有听审能力时抽听拼接处；否则对照原声波形与输出音轨，记录实际手段及限制，不宣称人工听审。精细口水词删除需逐字对齐和剪口重转写，不以粗分段代替精剪。

交付编号视频、可选合并版、`gallery.html`、`manifest.json`、`plan.json` 和验证报告。素材库使用一个播放器、主题搜索和可用/待复核筛选，不同时加载几十个视频。报告源时长、保留/剔除/待复核时长、段数、实际规格、依据与限制。只有完成全片渲染和回读才能说全片处理完成；仅样片验证时如实说明。

下游通过文件交接：照片精选读取增强段与源映射，正式剪辑读取段文件/原声/时间线，章节条读取定稿时间线。每个下游承担自己的验收，不替代本 Skill 的画质与内容完整性验收。

## Validation

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/check_workflow.py"
```

合成测试只验证工程边界，不能伪装用户案例。真实输入输出见 [案例](cases/cases.json)。
