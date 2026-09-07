---
name: lov-gen-logo
description: 根据项目用途制作版本化 Logo 草稿及应用图标，并按确认范围接入。支持明确输入与结果回读。Use to create a logo and
  application icon.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 5.1.2
  tags:
  - logo
  - app-icon
  - brand-design
  - image-generation
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
---

# Gen Logo

迭代生成 Logo，保留每一版原稿，并将“品牌标志”和“应用图标”作为不同产物处理。

## Triggers

### Activate when

- 用户说“生成 Logo”“设计应用图标”“去掉 Logo 白底”或“放大图标主体”。
- 用户要求迭代、选用或发布某一版 Logo。
- The user asks to create, refine, select, or publish a logo or app icon.

### Do not activate when

- 用户只想查找已有官方 Logo；交给 Logo 查找类 Skill。
- 用户只想压缩、裁剪或转换普通图片，且不涉及品牌标志设计。

## 核心原则

- **不覆盖**：每次生成保存为新版本 `v{N}-{描述}`。
- **项目驱动**：根据产品功能、使用场景和品牌气质设计，不按项目名字面联想。
- **分离产物**：透明品牌标志、应用图标和平台派生资源分别制作，禁止相互冒充。
- **视觉占比优先**：用可见图形边界判断大小，不用源文件画布或透明留白判断。
- **真实场景验收**：在 favicon、桌面、Dock、主屏幕等最终使用环境验证视觉重量。
- **确认发布**：用户确认后再写入正式位置；仅在 `--publish` 时提交。

## 参数

```text
/lov-gen-logo [concept] [--use vN] [--publish vN]
```

- `concept`：设计概念或迭代反馈。
- `--use vN`：选用第 N 版并更新正式资产，不提交。
- `--publish vN`：选用第 N 版、完成平台验证并提交。

## 产物模型

为每版保留以下文件；按项目实际用途省略不需要的派生项：

```text
assets/logo-drafts/
├── vN-desc-raw.png            # 生成器原图，永不覆盖
├── vN-desc-mark.png           # 紧边界透明标志
├── vN-desc-mark.svg           # 矢量标志
├── vN-desc-app-icon-mark.png  # 1024 方形透明布局稿，用于测量主体占比
├── vN-desc-app-icon.png       # 1024 方形、不透明、满铺底色的应用图标
└── vN-desc-preview.png        # 小尺寸与明暗背景预览
```

区分以下语义：

| 产物 | 背景 | 留白 | 用途 |
|---|---|---|---|
| `mark.png/svg` | 透明 | 紧边界或少量光学留白 | 网站、文档、组合品牌 |
| `app-icon-mark.png` | 透明 | 主体长边通常占画布 62%–74% | 测量和合成中间稿 |
| `app-icon.png` | 不透明且铺满画布 | 不在外缘留透明或白色边框 | iOS、桌面应用图标 |
| Android adaptive icon | 前景与背景分层 | 遵循平台安全区 | Android 启动器 |

除非设计明确要求白色底板，否则不要把白底视为 Logo 的组成部分。iOS 圆角由系统裁切，不要预先烘焙圆角或透明四角。

## 工作流程

### Step 0：发现项目与版本

1. 读取 `package.json`、`README.md` 和现有品牌资产。
2. 搜索平台事实源，例如 `app.json`、`Info.plist`、asset catalog、PWA manifest、Electron/Tauri 图标配置。
3. 检查 `assets/logo-drafts/` 的最大版本号，使用下一版本。
4. 记录现有正式 Logo 路径，禁止默认假设一定存在 `assets/` 或 `public/`。

```bash
mkdir -p ./assets/logo-drafts
find ./assets/logo-drafts -maxdepth 1 -type f -name 'v[0-9]*-*' \
  -print | sort -V | tail -1
```

### Step 1：分析项目与设计概念

首次生成时读取：

- `package.json` 的名称、描述、关键词和依赖；名称只作标识。
- `README.md` 的核心功能、目标用户和差异化价值。
- 当前界面的形状语言、颜色、圆角、图标密度和相邻品牌资产。

按项目类型选择方向：

| 类型 | 识别特征 | 推荐方向 |
|---|---|---|
| Web 框架/Starter | next、react、vue、angular | 几何抽象、模块、网格 |
| CLI 工具 | commander、yargs、`bin` | 光标、尖锐线条、技术感 |
| 桌面/移动应用 | electron、tauri、expo、原生工程 | 单一强轮廓、应用图标构图 |
| 库/SDK | 无 UI 依赖、纯逻辑 | 极简符号、数学感 |
| AI/ML | openai、langchain、模型依赖 | 连接、流动、智能但避免通用星芒 |

迭代版本应先总结上一版的明确问题，例如“主体只占画布 46%，在主屏幕上显小”，再把改进目标写进 Prompt。不要只写“更大”或“更好看”。

### Step 2：生成原稿

```bash
${IMAGE_GENERATOR_COMMAND:-image-generator} \
  "PROMPT" -o ./assets/logo-drafts/v{N}-{desc}-raw.png -q high
```

Prompt 需要明确：

- 只生成独立标志，不含文字、展示样机、边框、卡片和预制圆角底板。
- 使用 2–3 个主要几何形状，在 16×16 仍可辨认。
- 保持轮廓完整、边缘干净、构图居中。
- 生成器不稳定支持透明度时，使用与标志颜色明显不同的纯色背景，后续提取；不要让背景成为设计元素。
- 应用图标的底色、渐变和光效在标志提取后确定性合成。

优先读取 Profile 的 `brand.colors.primary` 或项目已有品牌色；二者都缺少时，先询问本次视觉方向需要的颜色，不在 Skill 内设定某个品牌专属默认色。

### Step 3：提取透明标志并矢量化

保留 `raw.png`，只对副本去背景。优先从四角连通区域移除背景，避免使用全局 `-transparent white` 误删标志内部的白色区域。

```bash
cd ./assets/logo-drafts

magick v{N}-{desc}-raw.png -alpha on \
  -bordercolor white -border 1 -fuzz 5% -fill none \
  -draw 'alpha 0,0 floodfill' -shave 1x1 \
  -trim +repage PNG32:v{N}-{desc}-mark.png

magick v{N}-{desc}-mark.png -channel A -threshold 50% +channel temp.png
vtracer --input temp.png --output v{N}-{desc}-mark.svg \
  --mode spline --filter_speckle 8 --color_precision 8 \
  --corner_threshold 120 --segment_length 6 --path_precision 5
npx svgo v{N}-{desc}-mark.svg -o v{N}-{desc}-mark.svg --multipass
rm -f temp.png
```

背景不是白色时，将 `-bordercolor white` 替换为实际角落背景色。提取后放大检查轮廓，不接受白色毛边、半透明光晕、断裂细节或棋盘格伪透明。

### Step 4：构建应用图标

从透明 `mark.png` 确定性合成应用图标，不直接把带透明留白的 Logo 当作 App Icon。

```bash
$SKILL_DIR/scripts/build_app_icon.sh \
  --mark ./assets/logo-drafts/v{N}-{desc}-mark.png \
  --output ./assets/logo-drafts/v{N}-{desc}-app-icon.png \
  --layout-output ./assets/logo-drafts/v{N}-{desc}-app-icon-mark.png \
  --background '#0C150F' \
  --occupancy 0.68
```

以可见主体长边占画布 `68%` 为起点，根据视觉重量在 `62%–74%` 内调整：

- 细线、镂空、尖角或浅色标志取较大值。
- 密实、圆润、高对比标志取较小值。
- 低于 `60%` 通常会在主屏幕上显小；高于 `78%` 通常会显拥挤。
- 比较相邻常见应用图标的视觉重量，不只比较几何宽高。

为渐变背景传入 `--background-image PATH`。保持背景满铺到四角，输出 PNG 必须为 1024×1024、RGB、无 alpha。

Android 项目应另外生成 adaptive icon 的前景和背景层，并在圆形、方形、圆角方形遮罩下预览；不要直接复用 iOS 合成图。

### Step 5：质量门禁与展示

生成预览并同时检查：

- 透明标志置于浅色、深色和棋盘格背景。
- 应用图标以 16、32、60、120、256 像素显示。
- 应用图标与 2–3 个同平台常见图标并排，检查主体视觉重量。
- 背景铺满四角；非刻意白底时不存在白色方块或白边。
- SVG 与 PNG 的形状、方向、颜色一致。

执行基础检查：

```bash
magick identify -format '%f %wx%h %[channels]\n' \
  v{N}-{desc}-mark.png v{N}-{desc}-app-icon.png

magick v{N}-{desc}-app-icon.png \
  -format 'corners: %[pixel:p{0,0}] %[pixel:p{1023,0}] %[pixel:p{0,1023}] %[pixel:p{1023,1023}]\n' \
  info:
```

使用图像查看工具展示 `mark.png`、`app-icon.png` 和 `preview.png`，再反馈版本、主体占比、背景语义和改进点。

```text
✓ v{N}-{desc} 生成完成
主体长边占画布：{ratio}%
产物：透明标志 / 不透明应用图标 / 场景预览

继续迭代可直接描述具体问题；确认后执行 /lov-gen-logo --publish v{N}
```

### Step 6：选用与发布

执行 `--use` 或 `--publish` 时：

1. 读取平台配置，建立“草稿产物 → 正式事实源”的明确映射。
2. 只写入项目真实存在或配置引用的路径；禁止无条件创建 `assets/logo.*` 和 `public/logo.*`。
3. 运行项目原有的图标生成流程，验证最终打包资源而不只验证源 PNG。
4. Web 项目验证 favicon、PWA manifest 和浅深色背景。
5. 桌面应用验证 Dock、任务栏、菜单栏和安装包图标。
6. 移动应用构建并安装到真实设备，在主屏幕与相邻图标并排验证；安装成功不等于图标验收完成。
7. 用户确认版本后，`--publish` 仅提交本次 Logo 相关文件。

```bash
git status --short
git add <本次确认的正式资产> <对应草稿版本>
git commit -m "docs: update logo to v{N}-{desc}"
```

### Step 7：生成 Tray Icon（Tauri）

存在 `src-tauri/icons/` 时，从紧边界透明标志生成模板图标：

```bash
magick ./assets/logo-drafts/v{N}-{desc}-mark.png -trim +repage \
  -resize 38x38 -gravity center -background transparent -extent 56x44 \
  -colorspace gray -fill white -colorize 100% \
  src-tauri/icons/tray-icon.png
```

在 macOS 明暗菜单栏分别检查，不把彩色应用图标直接缩小作为菜单栏模板图标。

## 依赖

- `python3` 与图像生成后端
- ImageMagick 7（`magick`）
- `vtracer`
- `svgo`

## 附带脚本

- `scripts/build_app_icon.sh`：按可见主体占比构建 1024×1024 的透明布局稿和不透明应用图标，并校验尺寸与 alpha。




## Execution boundary

自然语言请求即可触发；无需旧 slash 路径、参数插值或指定助手。明确解析当前请求中的
项目、目标文件、选项与输出位置；用当前宿主实际提供的文件、搜索、CLI 和浏览器能力。
项目依赖版本与外部 API 在执行时核实，不能假设示例是现行配置。随包脚本从 Skill 根解析，
业务文件从目标项目根解析。先读当前状态，保护已有未提交内容与其他任务的暂存区。
分析、预览请求保持只读；修改、提交、推送、部署和发布各依当前请求的明确范围执行。
不绕过保护、自动发送消息、强制结束用户进程或抢前台。失败保留可诊断原始错误。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
