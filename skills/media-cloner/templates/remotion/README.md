# 风格包装模板（Remotion）

由参数驱动的起步工程。两个合成读同一套样式参数：

- `StyleClip`（默认 9:16 1080×1920）包含：
  - 录像分段，支持冻结帧补尾；
  - 分隔（测试彩条、黑场、白场或任意颜色）；
  - 单一连续音轨；
  - 标题块，多行同字号，可指定重点词；
  - 资料卡、画中画头像窗、字幕。
- `StyleCover`（默认 3:4 1080×1440）：一帧画面加放大的标题块，可带头像窗。

## 文件

- `src/data/style-tokens.json`：颜色、字体、标题/字幕/资料卡/头像窗的位置与字号、描边、分隔彩条配色。组件里不写死任何样式。
- `src/data/render-plan.json`：时间单位为帧，包含 `video`、`separators`、`audio`、`titles`、`cards`、`pips`、`subtitles`。自带示例不需要任何素材。
- `src/data/cover.json`：封面取帧（`src` + `frame`，或 `image`，或纯色 `background`）、标题行、中心高度与字号。

标题行的 `fill` 写颜色参数名（`emphasis`、`plain`、`accent`）或直接写颜色值；`accent_words` 里的词用 `accent` 色。

## 准备

1. 复制本目录到工作区，安装依赖（Remotion 4.0.517、React 19.2.3），或把 `node_modules` 软链到一份同版本依赖。
2. 素材都不进版本库：
   - 录像放 `public/media/`；
   - 音轨放 `public/audio/`，用 `scripts/build_audio.py` 生成；
   - 标题字体放 `public/fonts/`。

   这些文件必须用硬链接或复制：Remotion 打包时不跟随符号链接，软链会在渲染时 404。
3. 可选：设置 `REMOTION_BROWSER_EXECUTABLE` 指向已有的 Chrome Headless Shell。

## 渲染

```bash
npx tsc --noEmit -p .
npx remotion still src/index.ts StyleCover out/cover.png
npx remotion still src/index.ts StyleClip out/clip.png --frame=50
npx remotion render src/index.ts StyleClip out/clip.mp4 --codec h264 --crf 18 --audio-bitrate 192k
```

参数怎样从风格包得到、演示素材要满足什么条件、渲染后怎样验收，见 Skill 的 `references/template-and-demo.md`。
