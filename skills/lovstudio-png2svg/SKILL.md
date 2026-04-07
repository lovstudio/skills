---
name: lovstudio:png2svg
description: 将 PNG 转换为高质量 SVG（去白底+样条曲线+压缩）
allowed-tools: [Bash, Read]
---

# PNG to SVG Skill

将 PNG 图片转换为高质量矢量 SVG，支持去除白色背景。

## 工具链

```
PNG → magick (去白底+alpha阈值) → vtracer (样条曲线) → svgo (压缩) → SVG
```

- **ImageMagick** (`magick`): 去除白色背景 + alpha 阈值处理
- **vtracer**: 样条曲线矢量化（比 potrace 更平滑）
- **svgo**: SVG 路径压缩优化

## 调用方式

当需要将 PNG 转换为 SVG 时，按以下步骤执行：

### 输入

- `INPUT_PNG`: 输入 PNG 文件路径（必需）
- `OUTPUT_SVG`: 输出 SVG 路径（默认：同名 .svg）
- `KEEP_BG`: 是否保留背景（默认：false，去除白色背景）

### 执行步骤

#### Step 1: 预处理（去白底）

如果需要去除背景（KEEP_BG=false）：

```bash
magick INPUT_PNG \
  -fuzz 15% -transparent white \
  -channel A -threshold 50% +channel \
  INPUT_PNG.temp.png
```

#### Step 2: 矢量化

```bash
vtracer --input INPUT_PNG.temp.png --output OUTPUT_SVG \
  --mode spline \
  --filter_speckle 8 \
  --color_precision 8 \
  --corner_threshold 120 \
  --segment_length 6 \
  --path_precision 5
```

#### Step 3: 压缩优化

```bash
npx svgo OUTPUT_SVG -o OUTPUT_SVG --multipass
```

#### Step 4: 清理

```bash
rm -f INPUT_PNG.temp.png
```

### 输出

返回生成的 SVG 文件路径，并报告文件大小。

```
✓ PNG → SVG 转换完成

输入: {INPUT_PNG}
输出: {OUTPUT_SVG}
大小: {file_size}
```

## 依赖

首次使用前确保已安装：

```bash
brew install imagemagick
cargo install vtracer
npm install -g svgo  # 或使用 npx
```

## 参数调优

| 参数 | 作用 | 调大效果 |
|-----|------|---------|
| `filter_speckle` | 过滤小斑点 | 更干净 |
| `corner_threshold` | 角点阈值 | 更平滑 |
| `segment_length` | 线段长度 | 更平滑 |
| `color_precision` | 颜色精度 | 更准确 |
