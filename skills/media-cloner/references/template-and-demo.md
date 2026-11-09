# 包装模板与演示

## 模板做什么

`templates/remotion` 是由参数驱动的 Remotion 4.0.517 起步工程，有两个合成：

- `StyleClip`：录像分段、分隔（测试彩条、黑场、白场或任意颜色）、单一连续音轨、标题块、资料卡、画中画头像窗、字幕；
- `StyleCover`：一帧画面（视频帧、图片或纯色）加放大的标题块，可带头像窗。

所有颜色、字体、位置、字号、描边都在 `src/data/style-tokens.json`。换一个博主只改这份参数和渲染计划，不改组件。

已验证的复现结果：

- **画面。** 把晓暖 v0.1 的实测参数填进参数文件，用同一份时间线渲染 4 帧，与她的专用模板逐像素一致。
- **音轨。** 用 `scripts/build_audio.py` 按同一结构重做演示音轨，结果为 -15.71 LUFS、-4.28 dBTP，与原音轨的相关系数为 0.9998。

## 从风格包到参数

| 参数 | 来源 |
| --- | --- |
| `title.top`、`subtitle.top`、`card`、`pip` | `layout_templates` 的归一化坐标乘画幅，再移入平台安全区（默认顶部 160 px、底部 260 px），移动量记为有意偏离 |
| `colors` | `measure.py layout --colors` 的聚类结果：亮色簇是填充，最暗簇是描边，其余多为背景 |
| `fonts` | 原作精确字体未知时，选一款你有权使用、字形相近的字体（如 SIL OFL 开源字体）；把文件放进 `public/fonts/`，文件名与 `fonts.titleFile` 一致 |
| `title.advanceEm` | 该字体每个汉字的平均步进，用第一张预览实测后回填；它决定标题能否按原作比例占满画面宽度 |
| `title.stroke`、`subtitle.stroke` | 对照抽帧放大比对描边粗细 |
| `separator.bars` | 原作用测试彩条时，从分隔帧取色 |

## 预览

1. 复制模板到 `work/remotion`，安装依赖，或把 `node_modules` 软链到一份同版本依赖。
2. 先用自带的无素材示例渲染预览帧，核对版式和颜色：

   ```bash
   npx tsc --noEmit -p .
   npx remotion still src/index.ts StyleCover out/cover.png
   npx remotion still src/index.ts StyleClip out/clip-50.png --frame=50
   ```

3. 设置 `REMOTION_BROWSER_EXECUTABLE` 指向已有的 Chrome Headless Shell，可以避免首次渲染下载约 170 MB。
4. 预览帧和参考抽帧并排比对，记录与原作的差异。

## 演示成片

- **素材。** 只用用户自己拥有的素材；画面里出现的人要有书面同意，可只露头像。不使用原博主的片段、声音、头像或字样。
- **`public/` 里的文件。** 视频、音轨、字体用硬链接或复制。Remotion 打包时不跟随符号链接，软链会在渲染时 404。
- **音轨。** 写音频计划（人声片段、分隔音、可选配乐），用 `scripts/build_audio.py` 生成一条连续音轨：

  ```bash
  python3 "$SKILL_DIR/scripts/build_audio.py" --plan work/audio-plan.json --output work/remotion/public/audio/mix.m4a
  ```

  - 人声两遍 loudnorm 归一。若归一后真峰值超出目标，FFmpeg 会自动改用动态限幅。
  - 分隔音按“比人声 RMS 高多少 dB”放置，配乐按“比人声低多少 dB”放置，这两个差值取自参考测量。
  - 报告测的是交付文件：单声道上混立体声后每声道低 3 dB，整合响度不变。
  - 中间片没有音轨时，人声片段要指向分离出来的人声文件。
- **渲染计划。** 写 `src/data/render-plan.json`，时间单位是帧，各段首尾相接、不留空。
- **渲染。**

  ```bash
  npx remotion render src/index.ts StyleClip out/demo.mp4 --codec h264 --crf 18 --audio-bitrate 192k
  ```

## 验收

- 成片重新转写，核对剪口有没有吞字。
- 实测整合响度与真峰值（默认 -16 LUFS、真峰值不高于 -1 dBTP）。
- 有分隔音的，用 FFmpeg 或 `measure.py tones` 复查位置。
- 扫描黑场与长静音。
- 抽帧检查标题、字幕、资料卡、头像窗与安全区。
- 封面在 3:4 缩略尺寸下检查可读性。

模板预览、渲染完成、人工认可、对外发布是不同状态。对外发布前确认出镜者对这一版的同意。
