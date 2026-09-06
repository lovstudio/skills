# 摄影调色与色彩还原

适用于用户在本次请求或长期 Profile 中选择 `photographic`，且宿主允许确定性编辑的任务。目标是明亮、真实的现场照片。保留原帧与原视频；已选定组图后只修颜色与亮度，不重新挑片或改变构图。

## 先读颜色证据

每个视频单独 `probe`，不能按相机型号、目录或拍摄日期统一猜测。

| 证据 | 用途 |
| --- | --- |
| `pix_fmt` | 判断源位深与采样格式 |
| `color_range` | 区分 `pc` 全范围与 `tv` 视频范围 |
| `color_space` | YUV 到 RGB 的编码矩阵，不能拿原色名称代替 |
| `color_primaries` / `color_transfer` | 原色与传递函数 |
| Sony XML 的 `CaptureGammaEquation` / `CaptureColorPrimaries` | 识别 S-Log3 / S-Gamut3.Cine 等相机录制模式 |
| Sony XML 的 `CodingEquations` | 补充缺失的 YUV 编码矩阵 |

脚本只读取与视频同 stem 的 `.XML` 或 `M01.XML`，排除 `._` 资源文件；仅保存颜色字段与 sidecar 哈希，不复制相机序列号。多个 sidecar、冲突字段、损坏 XML、未知颜色、HDR 或未支持的 Log 组合都需要先查清。

`auto` 自动识别完整元数据；未知输入只能在检查后显式选 `--color-mode srgb|bt709|slog3-sgamut3cine`。`srgb` 仅表示已经还原的 SDR 原帧，不能用它越过已识别的 Log / HDR。支持的源视频矩阵目前为 bt709；范围缺失时可在确认后传 `--input-range pc|tv`，已有范围与参数冲突时拒绝。其他组合使用已核验的外部色彩管理流程，不把未支持写成已还原。

## 内置处理顺序

1. 校验原帧文件哈希；重新 probe 原视频并比较 bytes、duration、edge fingerprint。外置盘改路径时使用 `--source-video`，不能只比较文件名。
2. Log / Rec.709 在原选定时间码从视频解码 16-bit RGB，明确 YUV 矩阵与输入范围；sRGB 模式读取原帧并转换已有 ICC。原帧不覆盖，仍是选择与构图证据。
3. 反解传递函数。S-Log3 使用 Sony 公式，S-Gamut3.Cine 经 D65 原色矩阵转换到线性 sRGB。Rec.709 使用 BT.709 OETF 的逆函数，再输出为 sRGB 照片；这是一种明确记录的照片显示转换，不等同于任意成片 LUT 或 BT.1886 调色监视器匹配。
4. 在线性空间调整曝光（stops）与 RGB 白平衡增益；亮度超过 0.75 的区域平滑压高光，保留黑白衣层次。负的超色域值裁至 0；这是有限色域的近似处理，强饱和 LED 屏仍需视觉检查。
5. sRGB 编码后调整饱和度、对比度、亮度与 gamma。缩小可用 Lanczos，不自动放大原片。导出 RGB JPEG，quality 95、4:4:4、嵌入 sRGB ICC、无 EXIF。
6. `edits.json` 记录实际模式、源证据、参数、解码命令、时间码和双哈希；状态先为 `needs-visual-review`，不能自动通过视觉门禁。

默认曝光为 0、白平衡增益为 1；不随 Skill 固化任何课程的具体参数。原有 `--red` / `--blue` 参数仍接受，现在与新增的 `--green` 一样作用于线性 RGB；gamma/亮度/对比度/饱和度作用于 sRGB 编码值。旧脚本对未知输入的 SDR 假设已取消，旧清单会在原片可访问时重新 probe。

```bash
python3 "$SKILL_DIR/scripts/video_moments.py" photographic "$FRAMES_MANIFEST" \
  --color-mode auto --exposure 0.3 --gamma 1.1 \
  --long-edge 1920 --output "$RUN/data/edited-source-a"
```

这些数值只说明命令结构。以一张代表图校准每类模式，回看后再处理同类素材；不同灯光、时间或人物朝向仍可能需要不同参数。

## Sony 公式与依据

以下 `v` 是完成 YUV 范围解码后的 RGB 编码值，区间 0–1。不要再次把全范围压为 64–940。

```text
if v >= 171.2102946929 / 1023:
    linear = 10 ** ((v * 1023 - 420) / 261.5) * 0.19 - 0.01
else:
    linear = (v * 1023 - 95) * 0.01125 / (171.2102946929 - 95)
```

S-Gamut3.Cine 原色坐标为 R(0.766, 0.275)、G(0.225, 0.800)、B(0.089, -0.087)，白点 D65(0.3127, 0.3290)。不要误用 S-Gamut3 矩阵。代码值 95 对应黑、420 对应 18% 灰、598 约对应 90% 白，是数值回归的锚点。依据：[Sony Technical Summary for S-Gamut3.Cine / S-Gamut3 / S-Log3](https://www.sony.jp/ls-camera/knowledge/pdf/TechnicalSummary_for_S-Gamut3Cine_S-Gamut3_S-Log3_V1_00.pdf)。

## 校准与交付

- 每种录制模式先看一张完整原尺寸对比，再看全组手机缩略图。以面部、白衣、桌面与暗部为主，不能让明亮投影支配曝光判断。
- 肤色偏黄/偏绿时调白平衡，阴影偏暗时调曝光与曲线；不要为了“统一”抹平原有灯光差异。
- 需要局部柔和提亮或轻微色度降噪时，可用宿主摄影流程补充；记录区域、羽化与参数。内置 CLI 不宣称已经做了人脸局部遮罩、去噪或细节恢复。
- 逐张比较面部、手势、衣物、物品、屏幕文字及边缘。原片噪点、软焦和不可读文字仍是限制，不能重画细节补齐。
- 成图已通过后，ICC 创建日期等元数据变化不必然等于画面变化。必须比较解码 RGB 像素与尺寸，确认相同后更新文件哈希；不能删除哈希检查。像素有变化必须重看。
- 原片只读、成图新目录、原图对比在本地。多源组图逐源过门禁后再合并，具体见 [selection schema](selection-schema.md#多源组图)。
