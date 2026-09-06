---
name: lov-video-moments
description: >
  从课程、活动或日常视频筛选朋友圈 moments，提取最佳帧、明亮自然美化并统一组图。Use when 用户说“视频挑朋友圈照片”“课程精彩瞬间”或 “create photo moments from a video”。
license: MIT
compatibility: "Python 3.9+, Pillow 10.1+, FFmpeg and FFprobe; NumPy for photographic color processing, PyYAML for validation. Host vision required; image editing follows host rules and the user's selected method; transcription optional."
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.3.0"
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
    - video-moments
    - frame-selection
    - documentary-photo
    - wechat-moments
---

# lov-video-moments

把一个视频变成一组可直接选用的真实现场照片。负责从视频证据到候选筛选、相邻帧比较、照片美化、尺寸统一与交付回读的完整结果。以照片为主，默认不加金句、海报框或品牌签名。

## Triggers

### Activate when

- “给定一个线下课程实录，提取适合发朋友圈的 moments，并做图像美化与标准化。”
- “从这段沙龙视频挑六张好看的现场照片，色调和大小统一。”
- “Create shareable photo moments from a video and standardize the selected images.”

### Do not activate when

- 只要短视频高光混剪、字幕、章节条或视频导出；使用对应视频剪辑能力。
- 只有照片，要求加 Logo、图注或修图；使用图片编辑或 image-decorator。
- 只写朋友圈文字，不需要从视频获取画面；交给朋友圈文案能力。
- 请求直接发布朋友圈；本 Skill 只交付本地图片，发布另行授权和验收。

## Runtime context

每次读取 `skill.yaml` 与 [Profile contract](references/user-profile.md)，再运行：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-video-moments
```

解析顺序：当前请求/显式参数 → 环境 → 项目上下文 → 本 Skill records → 共享 preferences、user/brand/workspace Profile → 安全默认值。CLI 按显式参数运行；Agent 将解析后的值传给 CLI，不能假装脚本自动读取了所有 Profile 配置。

只把用户直接声明的跨会话偏好写入 `skills.lov-video-moments.records`。一次性视频路径、课程参与者身份、字幕内容和推断审美不持久化。用 `scripts/profile_store.py record --skill-id lov-video-moments --path records.aspect_ratio --value '"16:9"' --confirm` 保存长期偏好，并报告 canonical 保存位置。

`records.edit_method` 接受 `photographic` 或 `imagegen`。用户说“默认改用摄影调色”时保存 `records.edit_method=photographic`；以后在宿主允许范围内直接沿用，不重复询问同一选择，也不先生成一张 AI 样图。仅声明明亮风格不等于选择生成式编辑。Profile 偏好不能覆盖宿主工具约束。

读取 [Skill composition](references/skill-composition.md)。这是 Single Skill，脚本都在包内；相关 Skill 通过可选文件交接，不要求外部 sibling 模块。

## Workflow (MANDATORY)

### 1. 确认输入与交付标准

从请求获得本地视频、可访问且已授权的链接或已有视频工程。链接先通过宿主媒体能力落地为本地文件，不绕过登录/付费/下载限制。缺少素材只问路径，同时推进不依赖素材的准备。

只有无法自行查清且影响结果的缺失信息才使用宿主 AskUserQuestion 或等价提问工具；用户已提供视频与审美反馈时直接推进。

默认目标约六张纪实照片、同组比例和尺寸统一；数量服从素材质量，1–9 张均可。这个数量是工作流约定，不宣称平台硬限制。先读 [selection policy](references/selection-policy.md) 和 [image contract](references/image-contract.md)。

```bash
python3 "$SKILL_DIR/scripts/video_moments.py" probe "$VIDEO"
```

保留原片只读；外置盘直接随机定位，不因便利复制几十 GB。确认音轨、时长、尺寸、色彩与输出空间。`.screenstudio` 等原工程可先由宿主提取可审阅轨道，本 Skill 不重写工程。

输入为目录时先列出真实视频文件，忽略 `._*`、隐藏文件及 XML；XML 仅作为对应视频的色彩证据。逐源保留 probe、索引和时间码，不能拼造一个合并时间轴。同一相机、同一天的素材也可能混有 Log 与 Rec.709；`probe` 同时记录流的像素格式、范围、矩阵、原色、传递函数及匹配 Sony XML 的三项色彩字段。

### 2. 覆盖全片并建立候选

```bash
python3 "$SKILL_DIR/scripts/video_moments.py" index "$VIDEO" \
  --every 60 --workers 2 --output "$RUN/data/coarse"
```

查看全部 `contact-*.jpg`，记录有价值的窗口和空段。`index.json` 的 coverage 是稀疏采样范围，不能声称逐帧无遗漏。长片先 30–90 秒，短片先 5–15 秒。字幕/转录可辅助定位，但候选必须回看画面。

中断时保留已完成帧与 `progress.json`。恢复同一个视频后，以相同参数加 `--resume`；脚本用大小、时长和文件两端 fingerprint 核对输入，fingerprint 不是全文件哈希。源视频变了必须新建工作目录。

```bash
python3 "$SKILL_DIR/scripts/video_moments.py" index "$VIDEO" \
  --start 00:20:00 --end 00:21:00 --every 2 \
  --output "$RUN/data/refine-01"
```

围绕候选按 1–3 秒细筛，必要时按 0.2–0.5 秒比表情。筛选内容价值、人物状态、摄影质量、组图差异和真实证据。音频未核对时标注 `selection_basis=visual`，不编造课程金句或学习效果。

### 3. 提取原始帧并锁定组图

```bash
python3 "$SKILL_DIR/scripts/video_moments.py" extract "$VIDEO" \
  --at 00:20:14 00:45:32 01:10:08 --output "$RUN/data/originals"
```

时间码仅为命令示例，实际必须来自已查看的索引。全分辨率 PNG 与 `frames.json` 保留源视频身份、时间码、尺寸与 SHA-256。相同动作只选最佳一帧；不为凑六张重复同一画面。

### 4. 美化并统一

先查看每张原图，解析当前请求与 `records.edit_method`，再按宿主允许的路径执行。按 [image contract](references/image-contract.md) 保留人物、课件、人数、手势与空间关系。已选摄影调色时进行确定性处理；使用生成式编辑时逐张生成并保存实际 prompt。两条路径都保存参数/候选、采用一致的视觉方向并实际回读。

默认采用已验证的 [bright-documentary 明亮自然方向](references/approved-bright-look.md)。这是视觉目标，按每份源片校准，不机械套用固定曝光值。用户已认可的图像作为本轮基准保留；后续修改只作用于指定问题。

逆光课程优先检查人物面部与现场暗部，不能由明亮投影拉高的全图平均亮度判断曝光。用户反馈偏暗时，实际提亮人物、减轻偏色，并回看手机缩略尺寸和人物局部；只有改了文件名或轻微处理到几乎不可见，不算回应了美化反馈。

摄影调色先完整读取 [摄影调色与色彩还原](references/photographic-workflow.md)。已有当前或长期选择即可使用包内 `photographic`；先按每种录制模式校准一张代表帧，再逐源处理：

```bash
python3 "$SKILL_DIR/scripts/video_moments.py" photographic "$RUN/data/originals/frames.json" \
  --color-mode auto --exposure 0.3 --gamma 1.1 --long-edge 1920 --output "$RUN/data/edited"
```

参数是起点而非通用滤镜。`auto` 支持有证据的 S-Log3 / S-Gamut3.Cine、Rec.709 和 sRGB；未知色彩不能当 SDR 直接增亮。Log 与 Rec.709 从同一时间码的原视频解码为 16-bit RGB，再浮点还原、校正与编码为 sRGB JPEG；先还原再提亮，不能用 gamma 代替 Log 变换。默认白平衡增益中性，不凭相机型号猜白平衡。曝光、肤色和高光逐图校准，不把某次课程参数写成全局预设。

若生成编辑改变小脸或投影文字，拒收。已选摄影调色时继续按该路径完成；不要把失败 AI 样图的重绘当作美化规范。无可用保真编辑能力时保留原图并如实报告未完成。候选留在独立本地对比页，不能填写虚假的通过字段或调用 `package` 冒充合格成品。

默认无文字。确需短 caption 时使用 `lov-branding-consistency` 的可见文案门禁；时间码、分数、挑选理由、生成过程只留在本地审阅页/manifest，不印在照片里。逐字金句保留源句，并有音频/转录核验。

### 5. 逐图回读，交付可溯源结果

按 [selection schema](references/selection-schema.md) 写入 `selection.json`，填写实际视觉验收、原图和成图的文件路径及哈希。选择后修改任意像素，必须再次查看并更新哈希。

```bash
python3 "$SKILL_DIR/scripts/video_moments.py" package "$RUN/data/selection.json" \
  --output "$RUN/photos-v0.1"
python3 "$SKILL_DIR/scripts/video_moments.py" verify "$RUN/photos-v0.1"
```

脚本只复制已经美化/标准化且通过视觉验收的图片，不暗中修图。拒绝时间码越界、重复 ID/时间/成图、未核验引文、未填视觉验收、哈希不符和尺寸混用。

`package` 一次只接受一个源视频的 selection。多源组图先分别通过原有门禁，再按 [多源交付契约](references/selection-schema.md#多源组图) 合并编号与来源清单，不修改门禁来容纳虚构来源。交付哈希核对实际文件字节；ICC 创建时间可能使文件哈希不同，只有解码像素完全一致才可判定画面未变，不能跳过最终文件哈希更新。

交付 `images/` 按顺序编号的图片、`overview.jpg` 总览、`gallery.html` 本地审阅页、`manifest.json` 时间码和理由。源帧、编辑 prompt 与候选资料留在 `data/`。所有导出路径都来自请求/Profile，不把私有路径写进 Skill 源。

最终回复给出图片预览与可点击目录/文件链接，说明数量、实际规格、筛选依据和未完成项。只说本地已完成，不写已发布。全部图片均为原帧时明确“原帧精选”，不写“美化完成”。

## Dependencies and validation

Python 3.9+、Pillow 10.1+、FFmpeg/FFprobe；摄影调色需要 NumPy，PyYAML 用于 Skill 校验。宿主 vision 负责内容判断，转录是知识类 moments 的可选上游。核心 CLI 无网络和凭据依赖。

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/check_workflow.py"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "$SKILL_DIR/tests" -v
```

真实案例见 [cases](cases/cases.json)。合成测试只验证工程边界，不替代真实视频的审美或语义验收。
