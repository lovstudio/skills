---
name: lov-image-decorator
description: >
  为现有 PNG、JPEG 或 WebP 增加底部 caption 与右下品牌 Logo，并按艺术图片或软件截图选择带框、无框版式；适用于“给图片加说明底栏”“装饰这张截图”和 “add a caption bar to this image”。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.9+ and Pillow 9+."
allowed-tools:
  - Bash
  - Read
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.2.3"
  card_standard: lovstudio/skill-card/v1
  tags:
    - image
    - decoration
    - caption
    - branding
    - editorial
---

# 图片装帧 · Image Finishing

把一张已有图片确定性地包装成编辑式传播图：保留完整原图，为艺术图片增加 Warm
Academic 圆角外框，为软件截图使用无外框版式，并统一追加底部 caption 区和右下品牌
Logo，输出已校验的 PNG、JPEG 或 WebP。

## Triggers

### Activate when

- 用户说“给这张图片加一个说明底栏和 Logo”“把 caption 放到图片底部”。
- 用户说“参考杂志配图样式装饰这张图”“为文章图片统一加图注”。
- 用户指出截图已有窗口边界，不希望再套外框。
- The user asks to “add a caption bar to this image”, “decorate an existing image”, or “brand this image with a logo”.

### Do not activate when

- 用户要生成新图、重绘或修改图像主体；交给 `lov-image-creator` 或宿主图像编辑能力。
- 用户要制作完整知识卡、海报或信息图；分别交给 `lov-gen-card`、海报或信息图能力。
- 用户只要上传图片、改 Markdown 链接或同步到发布平台；交给上传或平台发布 Skill。

## User Profile (cross-session)

每次运行先读取 `skill.yaml` 与共享 `user-profile/v1`。caption 依次取当前请求、
`skills.lov-image-decorator.records.default_caption` 和内置 fallback；Logo 依次取
当前请求、Skill 记录、共享品牌 Profile 和内置 LovStudio Logo。

只有用户直接声明的长期默认 caption 或 Logo 路径才通过
`scripts/profile_store.py record --confirm` 保存。不得保存一次性图片内容、远程凭据
或推断值。完整约定见 `references/user-profile.md`。

## Skill Group Composition

运行前读 `references/skill-composition.md`。相邻 Skills 只通过已校验的本地图片文件
交接，不构成隐藏运行依赖。

## Required resources

运行前确认：

- `scripts/decorate_image.py`
- `assets/lovstudio-logo.png`
- `assets/NotoSansSC-VariableFont_wght.ttf`
- `references/style-contract.md`
- `references/skill-composition.md`

## Workflow (MANDATORY)

### Step 0: Resolve context and assets

1. 从当前 Skill 上下文解析 `SKILL_DIR`，读取 `skill.yaml` 与 Profile。
2. 检查 Python、Pillow、输入图片、字体和 Logo；缺少任何必需资源时停止。
3. 读取 `references/style-contract.md`，保持 caption、Logo 与布局优先级一致。

### Step 1: Resolve the visible content

- 保留原图完整画面和 EXIF 方向，不裁剪、不拉伸、不修改主体像素。
- 用户给出 caption 时逐字使用；没有 caption 时读取 Profile 记录，仍为空则使用：
  `Powered by lovstudio.ai/skill/image-decorator`。
- 用户给出本地 Logo 时使用该 Logo；否则按 Profile 与内置品牌资产顺序回退。
- 明确的空 caption 也视为未提供，必须进入 fallback，不能生成空底栏。

### Step 2: Decorate through the deterministic CLI

基本调用：

```bash
python3 "$SKILL_DIR/scripts/decorate_image.py" input.jpg \
  --caption "本期封面：作品名与作者" \
  --output output.png \
  --json
```

使用 fallback caption：

```bash
python3 "$SKILL_DIR/scripts/decorate_image.py" input.jpg \
  --output output.png \
  --json
```

默认采用 `editorial-caption` 样式：米白外框、炭黑底栏、Medium 500 浅色 caption、右下
品牌 Logo。可以显式调整 padding、圆角、底栏高度、字号、Logo 尺寸和三种颜色；
不要在用户未要求时改变默认视觉体系。

软件截图使用 `screenshot-caption`：不增加米白外框或额外圆角，自动移除截图工具产生的
透明阴影画布，并将残留透明圆角展平为截图边缘背景；UI 内容与炭黑底栏直接衔接，避免
窗口装饰与外框叠加：

```bash
python3 "$SKILL_DIR/scripts/decorate_image.py" screenshot.png \
  --caption "安装与加载链出错时，市场会一直停在‘正在加载插件’" \
  --style screenshot-caption \
  --output screenshot-decorated.png \
  --json
```

### Step 3: Verify the actual image

- 命令成功必须返回输出绝对路径、格式、尺寸、caption 来源、Logo 来源、字节数和
  SHA-256。
- 回读图片，确认尺寸与 JSON 一致，caption 未被静默截断，Logo 在底栏右侧且未变形。
- 用视觉工具检查原图完整性、caption 对比度、版式材质与移动端可读性；截图不得保留
  截图工具的透明阴影画布或叠加第二层外框，艺术图片的外框留白应保持稳定。
- 失败时保留 `context_id` 与原始错误；不得把不存在、未回读或部分写入的文件写成完成。

## Output contract

- 一个不覆盖输入文件的 PNG、JPEG 或 WebP。
- 一个机器可读结果，包含 `output`、`format`、`width`、`height`、
  `caption_source`、`logo_source`、`decoration`、`bytes` 与 `sha256`。
- 版式只追加在原图之外；`screenshot-caption` 只可裁掉透明/半透明阴影画布并展平透明
  圆角，不裁 UI 内容；不对图片主体进行 AI 生成或内容修改。

## Dependencies

- Python 3.9+
- Pillow 9+
- 不需要网络、浏览器、凭据或外部 sibling Skill。

## Runtime context (shared)

字段解析顺序为当前请求、项目上下文、Skill 记录、共享 Preferences、品牌 Profile、
安全默认值。直接声明的长期偏好才写入 Profile，并在结果中报告保存路径。
