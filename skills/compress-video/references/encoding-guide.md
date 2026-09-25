# 编码策略 · Encoding Guide

`scripts/compress_video.py` 的默认值和各开关背后的取舍。改默认值前先读这里。

## 为什么默认是 libx265 CRF 28

- 同画质下 HEVC 比 H.264 小三到五成，Apple 全平台与 Windows 10 以后都能播。
- CRF 是恒定质量模式：画面复杂就多给码率，静态就少给，比固定码率更省。x265 的
  CRF 28 对绝大多数实拍与屏幕录制内容是“肉眼基本看不出”的边界，实测 VMAF 在
  90 到 95 之间。
- preset `medium` 是速度与体积的平衡点；`slow` 再省 5% 到 10% 体积但慢一倍。
  `smallest` 档才切到 `slow`。
- 保留分辨率与帧率。缩放是不可逆的信息损失，只有用户要求或 `smallest` 档才做。

## 质量档映射

| 档 | x265 CRF | x264 CRF | SVT-AV1 CRF | VideoToolbox q | preset | 音频 | 长边上限 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| smallest | 32 | 28 | 44 | 35 | slow | 64k | 1080 |
| small（默认） | 28 | 25 | 38 | 45 | medium | 96k | 无 |
| balanced | 25 | 22 | 33 | 55 | medium | 128k | 无 |
| high | 22 | 19 | 28 | 65 | medium | 160k | 无 |

VMAF 门禁触发重编时，x265/x264 每次降 3，SVT-AV1 降 5，VideoToolbox 的 q 升 8。

## 硬件编码为什么不是默认

Apple VideoToolbox 快两到四倍，但它是为实时录制设计的，同体积下画质明显更低。
本机实测同一段 1080p HEVC 片段：libx265 CRF 28 得 2.2 MB / VMAF 93.5，
VideoToolbox q=45 得 2.2 MB / VMAF 84.6。所以 `--fast` 只在用户明确要速度时用。
硬件解码则默认开启（`-hwaccel videotoolbox`），失败会自动回退软件解码。

## 音频

- 源是 AAC 且码率不高于目标的 1.15 倍 → 直接 `copy`，不重编。
- 否则转 AAC，按质量档给码率；超过双声道时降混到立体声。
- 不处理字幕与数据流（`-sn -dn`）；章节与全局元数据保留。

## 像素格式与色深

- 8 bit 源统一输出 `yuv420p`。ProRes 422、部分相机的 4:2:2 源如果不降到 4:2:0，
  很多播放器无法解码。
- 10 bit 源保留 10 bit（`yuv420p10le`，HEVC Main10），避免 banding；VideoToolbox
  用 `p010le` 并加 `main10` profile。

## 目标体积模式

`--target-size` 用两遍编码：视频码率 = 目标 × 8 / 时长 × 0.97 − 音频码率。只支持
libx265 与 libx264；SVT-AV1 与 VideoToolbox 的两遍支持不稳定。码率低于 50 kbit/s
直接拒绝，避免产出无法观看的文件。

## 门禁与安全

- 输出先写 `<名>.part.mp4`，成功后再改名；失败或中断时删除临时文件。
- 输出时长与源相差超过 0.5 秒或 1% → 丢弃并报 `duration-mismatch`。
- 输出不比源小 → 丢弃并报 `skipped-larger`，`--force` 可保留。
- 替换模式先把原文件移到废纸篓（macOS 走 Finder，失败回退 `~/.Trash` 同卷改名），
  都不行就保留两份文件并提示；只有 `--permanent` 才直接删除。上面两种丢弃情况下
  原文件都不会被动。

## 编码时间参考（Apple Silicon）

| 内容 | libx265 medium | libx265 slow | VideoToolbox |
| --- | --- | --- | --- |
| 1080p 实拍 | 3 到 6 倍速 | 1.5 到 3 倍速 | 10 倍速以上 |
| 4K 实拍 | 1 到 2 倍速 | 0.5 到 1 倍速 | 4 到 8 倍速 |

VMAF 测量另外需要约等于实时 1 到 3 倍速的时间，因为要同时解码两条视频。
