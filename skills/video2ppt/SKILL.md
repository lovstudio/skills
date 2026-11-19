---
name: lov-video2ppt
description: >
  从演讲、课程或录屏视频提取去重幻灯片，导出 PNG、PDF 与 PPTX，支持裁出幻灯片区域、跳过过渡帧和复核增删。Use when 用户说“视频转PPT”“把视频里的幻灯片扒下来”或 “extract slides from a video”.
license: MIT
compatibility: "Python 3.9+, Pillow, ffmpeg and ffprobe on PATH; python-pptx for PPTX output. Remote links need a downloader such as lov-media-crawler or yt-dlp."
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  upstream: MarkShawn2020/video2ppt
  tags:
    - video2ppt
    - slide-extraction
    - pptx
    - pdf
    - ffmpeg
---

# 视频转 PPT · Video2PPT

把一段带幻灯片的视频（会议演讲、网课、产品演示、录屏）还原成一份可翻阅的 PPTX
和 PDF，每页一张去重后的关键帧，备注里写着它在视频中的时间点。核心算法移植自
video2ppt 桌面应用：ffmpeg 按固定帧率采样，与上一页相似度低于阈值时开新页。

## Triggers

### Activate when

- “视频转 PPT”“把这个演讲视频的幻灯片扒下来”“从网课里导出课件 PDF”。
- 用户给出本地视频或视频号、B 站、YouTube 链接，并要幻灯片、课件、PPT 或关键帧合集。
- “extract slides from this talk”, “turn this lecture video into a PDF deck”, “video to pptx”.

### Do not activate when

- 只要下载视频本身：交给 `lov-media-crawler`。
- 要从文字、Markdown 或网页**生成**新幻灯片：交给 `lov-any2deck` 或 `baoyu-slide-deck`。
- 已经有幻灯片图片，只差打包成 PPTX/PDF：交给 `slide-to-pptx`。
- 要挑适合朋友圈的好看画面，而不是逐页课件：交给 `lov-video-moments`。
- 要按字幕给视频分章节：交给 `lov-video-chapter`。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`：用户语言、工作区输出位置，以及
`skills.lov-video2ppt.records` 下的长期偏好（`output_dir`、`method`、`similarity`、
`fps`）。解析顺序：当前请求 → 项目约定 → Skill 记录 → 共享偏好 → 安全默认值。
用户直接说出长期偏好（如“以后都输出到某目录”“默认用 pixel 方法”）时，用
`scripts/profile_store.py record ... --confirm` 写回并报告保存路径。完整契约见
[references/user-profile.md](references/user-profile.md)。

## Skill Group Composition

运行前阅读 [references/skill-composition.md](references/skill-composition.md)。
本 Skill 只负责“本地视频 → 已复核的幻灯片包”这一段；链接下载是可选上游交接，
不是隐藏依赖。

## Workflow (MANDATORY)

**按顺序执行。** 所有命令都以 `SKILL_DIR` 为根：

```bash
export SKILL_DIR="/path/to/lov-video2ppt"
```

### Step 0: 检查运行时

```bash
command -v ffmpeg ffprobe
python3 -c "import PIL, pptx"
```

缺 ffmpeg 时提示 `brew install ffmpeg`（Linux 用包管理器）；缺 Python 包时用
`python3 -m pip install pillow python-pptx`，或改用
`uv run --with pillow --with python-pptx python "$SKILL_DIR/scripts/video2ppt.py" ...`。

### Step 1: 拿到本地视频

- 本地文件：直接用。
- 视频号、抖音、小红书、B 站等链接：装了 `lov-media-crawler` 时按它的流程下载，取其
  `verified` 报告里的 `output_path`；YouTube 等站点可用 `yt-dlp`。都不可用时请用户提供本地文件。
- 下载得到的文件放在独立目录，只作为参数传给脚本，不在该目录里运行任何代码。

### Step 2: 看清画面布局，决定是否裁剪

抽 2–3 帧（开头、中段、结尾附近）看一眼：

```bash
ffmpeg -hide_banner -loglevel error -ss 00:03:00 -i VIDEO -frames:v 1 /tmp/probe-180.png
```

- **整屏就是幻灯片**（录屏、纯课件）：不裁剪。
- **幻灯片嵌在画面里**（讲者小窗、台标、底部字幕）：量出幻灯片矩形，传
  `--crop W:H:X:Y`（ffmpeg 像素语法）。字幕和讲者动作会不断制造伪“换页”，裁掉后才能
  稳定去重，输出也只剩干净的幻灯片。用一帧裁剪结果核对边界：
  `ffmpeg -ss 00:03:00 -i VIDEO -frames:v 1 -vf crop=W:H:X:Y /tmp/crop-check.png`。

### Step 3: 选参数并提取

| 场景 | 推荐参数 |
|---|---|
| 桌面版兼容（整屏大切换） | 默认：`--method hist --similarity 0.6` |
| 演讲 / 网课 / 白底幻灯片 | `--method pixel --similarity 0.985 --settle 3 --min-duration 2` |
| 动画多、只要终态 | 同上，复核时删掉中间态 |

```bash
python3 "$SKILL_DIR/scripts/video2ppt.py" extract VIDEO OUTPUT_DIR \
  --method pixel --similarity 0.985 --settle 3 --min-duration 2 \
  --crop W:H:X:Y --name DECK_NAME --json
```

参数含义与实测对比见 [references/tuning.md](references/tuning.md)。脚本拒绝覆盖已有产物，
确需重跑时加 `--overwrite`。输出目录结构：`frames/`、`DECK_NAME.pptx`、`DECK_NAME.pdf`、
`contact-sheet.jpg`、`manifest.json`。

### Step 4: 看联系表复核（必须）

打开 `contact-sheet.jpg`（每格标注 `#序号 时间`），逐项检查：

1. **页数量级**：十几分钟的演讲通常 20–60 页。明显过少说明阈值太松或没裁剪，回到 Step 3
   调参重跑；明显过多说明阈值太紧或字幕没裁掉。
2. **重复页**：同一页只因缩放、轻微动画重复出现 → 记下序号删除。
3. **逐步出现的中间态**：后一页完整包含前一页时，默认只保留终态。
4. **过渡帧**：两页叠化的半透明画面 → 删除。
5. **漏页**：时间轴上有长空档、或内嵌演示视频被 `--min-duration` 滤掉 → 用 `--add 时间` 补抓。

```bash
python3 "$SKILL_DIR/scripts/video2ppt.py" pack OUTPUT_DIR --drop 6,16,23 --add 00:08:50
```

`pack` 把删除的帧移到 `dropped/`（可恢复），按时间重新编号，并重建 PPTX、PDF、联系表和
`manifest.json`。最多复核两轮；仍拿不准的页保留，并在报告里列出。

### Step 5: 验收并交付

- 回读 `manifest.json`：`frames_kept` 应等于 PPTX 页数和 PDF 页数。
- 用 `python3 -c "from pptx import Presentation as P; print(len(P('DECK.pptx').slides))"` 核对 PPTX。
- 首句给出状态和 PPTX 路径；再列页数、源视频时长、所用参数、删了哪些页及原因、补了哪些页，
  以及仍有的风险（例如内嵌演示视频只截了一帧）。

## Dependencies

- 必需：Python 3.9+、Pillow、ffmpeg/ffprobe。
- PPTX 输出：python-pptx。
- 链接输入（可选）：`lov-media-crawler`（视频号等国内平台）或 `yt-dlp`。

## Validation

```bash
python3 scripts/validate_skill.py .
python3 tests/test_video2ppt.py
```

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
