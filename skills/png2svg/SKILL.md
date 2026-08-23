---
name: lov-png2svg
category: Document Conversion
tagline: "PNG → high-quality SVG conversion with background removal and spline curves."
description: >
  Convert PNG images to high-quality SVG with optional white-background removal,
  vtracer spline vectorization, and svgo compression. Use when the user asks
  for "PNG to SVG", "png2svg", "转 SVG", "矢量化", "去白底", logo tracing,
  or converting raster icons into editable vector assets.
license: MIT
compatibility: >
  Requires ImageMagick `magick`, vtracer, and svgo (`npx svgo` is supported).
  Works on macOS/Linux where those CLIs are installed.
metadata:
  author: contributors
  version: "1.1.0"
  tags: png svg vectorization imagemagick vtracer
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

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
