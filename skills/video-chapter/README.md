# Video Chapter Skill Kit

![Version](https://img.shields.io/badge/version-0.2.0-EB6637)
![License](https://img.shields.io/badge/license-MIT-green)

从字幕理解章节内容，在 React 剪辑台中调整切点和样式，再生成透明章节条、烧录成片或剪映素材包。

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## 完整流程

```text
SRT / VTT + 视频
        │
        ▼
  语义章节规划
  切点 / 标题 / 摘要
        │
        ▼
 chapter-project.json
        │
        ├── React Studio：预览、拖动切点、修改样式
        ├── Overlay：透明 ProRes 4444 MOV
        ├── Burn：带章节条的最终 MP4
        └── Package：剪映 / CapCut 可导入素材包
```

它由四个可组合子技能组成：

- `chapter-plan`：根据字幕确定 3–5 个自然章节。
- `chapter-design`：在 React Studio 中调整内容和视觉。
- `chapter-render`：渲染透明素材或烧录视频。
- `chapter-export`：生成剪映和其他剪辑软件需要的交付文件。

## 安装

```bash
git clone https://github.com/lovstudio/video-chapter-skill \
  "${LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}/sgc-video-chapter"
```

或使用 LovStudio 技能安装器：

```bash
npx lovstudio skills add video-chapter -g -y
```

基础分析只需要 Python 3.8+。渲染需要：

```bash
brew install ffmpeg
python3 -m pip install -r requirements.txt
```

React Studio 使用 Node.js：

```bash
cd studio
npm install
npm run dev
```

## 1. 根据字幕规划章节

```bash
python3 scripts/subtitle_chapters.py \
  --input "/path/to/video.srt" \
  --segments 5 \
  --output "/tmp/video-chapter-analysis.md"
```

Agent 会根据主题转折、完整语句和停顿选择切点，避免机械等分。

准备章节文本：

```text
00:00 一份完全由 AI 制作的 BP | 从最终效果说明制作目标
04:16 挑选并改造一个 BP Skill | 评估并调整现有能力
10:32 生成大纲并打磨产品定位 | 组织叙事并收紧定位
```

生成统一项目：

```bash
python3 scripts/chapter_project.py create \
  --chapters "/path/to/chapters.txt" \
  --video "/path/to/video.mp4" \
  --output "/path/to/chapter-project.json"
```

## 2. 在 React Studio 中调整

```bash
cd studio
npm install
npm run dev
```

Studio 支持：

- 导入和导出 `chapter-project.json`
- 本地选择视频并实时预览
- 点击章节跳转画面
- 拖动章节接缝调整切点
- 修改标题与摘要
- 调整颜色、位置、字号、边距和章节条尺寸
- 同时预览逐段连续填充效果

视频只在本机浏览器中读取。

## 3. 生成透明章节条

```bash
python3 scripts/render_chapter_bar.py overlay \
  --project "/path/to/chapter-project.json" \
  --output "/path/to/chapter-overlay.mov"
```

输出采用 ProRes 4444 与 Alpha 通道，适合放到剪映、CapCut、Premiere、Final Cut Pro 或 DaVinci Resolve 的最上方轨道。

## 4. 直接烧录成片

```bash
python3 scripts/render_chapter_bar.py burn \
  --project "/path/to/chapter-project.json" \
  --output "/path/to/video-with-chapters.mp4"
```

输出为 H.264 MP4，并保留源视频音频。

## 5. 生成剪映素材包

```bash
python3 scripts/render_chapter_bar.py package \
  --project "/path/to/chapter-project.json" \
  --output "/path/to/chapter-package"
```

素材包包含：

```text
chapter-overlay.mov
chapter-project.json
chapters.txt
chapters.csv
剪映导入说明.txt
```

在剪映中导入 `chapter-overlay.mov`，放到最上方视频轨道并对齐 `00:00` 即可。这属于稳定的素材级集成；直接修改剪映草稿工程保留在实验适配层。

## 项目校验

```bash
python3 scripts/chapter_project.py validate \
  --project "/path/to/chapter-project.json"
```

校验会检查时间连续性、最终时长、标题、颜色格式和视频参数。

## License

MIT
