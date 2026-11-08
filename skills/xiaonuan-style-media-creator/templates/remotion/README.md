# 晓暖连麦切片 · Remotion 包装模板

两个合成，读同一份渲染数据：

- `XiaonuanClip`：9:16 1080×1920。录像分段、彩条分隔、单一连续音轨、顶部双行标题、资料卡、单行宋体字幕、右下连麦头像窗。
- `XiaonuanCover34`：3:4 1080×1440 封面。取录像一帧，两行标题放大压在胸口，可把一个词标红，保留连麦窗。

布局常量在 `src/style.ts`，来源是风格包 `layout_templates.live_callin_9x16`，并已移入平台安全区（顶部 160 px、底部 260 px）。

## 准备

1. 把本目录复制到项目工作区，安装依赖（Remotion 4.0.517、React 19.2.3），或把 `node_modules` 软链到一份已有的同版本依赖。
2. 放入素材（都不进版本库）：
   - `public/media/`：录像（与剪辑计划里 `source.ref` 对应）；
   - `public/audio/`：`scripts/build_audio.py` 生成的音轨；
   - `public/fonts/title.ttf`：标题字体，推荐 Smiley Sans Oblique（得意黑，SIL OFL 1.1）；缺失时回退到系统黑体。
3. 用 `scripts/build_render_plan.py` 生成 `src/data/render-plan.json`；手改 `src/data/cover.json` 的取帧位置与标题。
4. 可选：设置 `REMOTION_BROWSER_EXECUTABLE` 指向已有的 Chrome Headless Shell，避免首次渲染下载约 170 MB。

字幕与资料卡使用 macOS 的 Songti SC；在其他系统上安装一款宋体（如 Noto Serif SC）并修改 `FONT.serif`。

## 渲染

```bash
npx tsc --noEmit -p .
npx remotion render src/index.ts XiaonuanClip out/clip.mp4 --codec h264 --crf 18 --audio-bitrate 192k
npx remotion still src/index.ts XiaonuanCover34 out/cover-3x4.png
```

`src/data/render-plan.json` 与 `cover.json` 目前是演示案例的数据，换成自己的计划前请先覆盖。

## 验收

成片重新转写核对剪口；实测响度（默认 -16 LUFS）与 True Peak（不高于 -1 dBTP）；用 `scripts/separator_scan.py` 复查提示音；扫描黑场与长静音；抽帧检查标题、资料卡、字幕与连麦窗；封面在 3:4 缩略尺寸检查可读性。
