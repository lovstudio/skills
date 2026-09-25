---
name: lov-gen-card
description: >
  把结构化内容与独立示意图排成可复制、可下载的高清知识卡片，输出自包含 HTML 和 2× PNG；适用于“生成一张卡片”“做系列图鉴卡”“render an editorial card”等任务。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - card
    - editorial-design
    - html
    - png
    - modern-screenshot
  compatibility: "Portable Agent Skills format. Python 3.9+; PNG export requires Chrome or Chromium."
  dependencies: []
---

# 知识卡片工坊 · Knowledge Card Studio

把一份结构化 JSON 和一张独立示意图渲染为固定比例的编辑式卡片。文字、评分、
Logo 和版式全部由 DOM 生成；AI 图像只进入视觉槽。交付自包含 HTML 与高清 PNG，
网页中可复制 Prompt、下载图片，并在导出时执行尺寸与溢出检查。

首个内置预设是 900×1350 的 `art-system-card`，适合艺术风格图鉴、术语图鉴、
方法卡和系列知识卡。它不是把整张卡交给生图模型。

## Triggers

### Activate when

- 用户说“生成一张知识卡片”“把这条内容做成卡”“做一组艺术风格图鉴卡”。
- 用户需要名称、示意图、背景、可复制 Prompt、场景、评分和品牌组成一张系列卡。
- The user asks to “create an editorial card”, “render a collectible knowledge card”, or “export a card as HTML and PNG”.

### Do not activate when

- 只需要生成或修改示意图：交给 `lov-image-creator`，再把图像路径交回本 Skill。
- 需要证据关系、数据图表与决策结论的一页信息图：使用 `lov-professional-infographic`。
- 需要姓名、角色、联系方式等身份名片：使用 `lov-business-card`。
- 只是在既有网页中增加截图按钮：使用 `lov-integrate-modern-screenshot`。

## User Profile (cross-session)

每次运行先读取 `skill.yaml` 和共享 `user-profile/v1`。解析顺序是：当前请求、
项目上下文、`skills.lov-gen-card.records`、共享 preferences、共享 brand/user、
安全默认值。

只有用户直接声明并希望长期复用的品牌或偏好，才使用
`scripts/profile_store.py record --confirm` 保存；不得保存推断值、凭据、秘密或
一次性内容。品牌名称、网站与 Logo 可以从 Profile 回退，但私有绝对路径不得写进
可复用源码。完整约定见 `references/user-profile.md`。

## Skill Group Composition

先读 `references/skill-composition.md`。相邻 Skills 只通过文件工件交接，不构成隐含
运行依赖。卡片 HTML 中所需的导出运行时已随本 Skill 一起提供。

## Required resources

运行前确认：

- `$SKILL_DIR/scripts/render_card.py`
- `$SKILL_DIR/assets/art-system-card.template.html`
- `$SKILL_DIR/assets/modern-screenshot.js`
- `$SKILL_DIR/references/input-schema.md`

## Workflow (MANDATORY)

### Step 0: Resolve root and context

- 优先使用宿主提供的 `SKILL_DIR`，否则从当前 Skill 上下文解析安装目录。
- 读取 `skill.yaml` 与共享 Profile；不存在 Profile 时使用无品牌的安全默认值。
- 检查 Python 版本。请求 PNG 时检查 Chrome/Chromium；只有 HTML 时不强制浏览器。

### Step 1: Build the structured brief

从用户请求和已有材料提取 JSON。必填内容是：主副标题、示意图本地路径、背景、
Prompt、1-6 个适用场景、1-5 个 1-5 星编辑评分。字段规则见
`references/input-schema.md`。

能从上下文确定的内容不要重复询问。若只有示意图缺失，可让用户提供本地图片，或
明确将一份“无文字、无徽章、无 Logo、4:3”的视觉 brief 交给可选上游生图能力。
不可在没有图时伪装完成。

评级属于编辑判断，必须保留“editor rating / 5”语义；不得把流行度、品味度写成
未经证据支持的客观统计。模仿在世艺术家时，改写成可描述的媒介、时代、构图和视觉
特征，不把艺术家姓名当作捷径。

### Step 2: Validate and render

先校验输入：

```bash
python3 "$SKILL_DIR/scripts/render_card.py" card.json --validate-only
```

再输出自包含 HTML 与 2× PNG：

```bash
python3 "$SKILL_DIR/scripts/render_card.py" card.json \
  --out ./card-output --name card-01 --format both --scale 2
```

可选参数：

- `--profile` 指定共享 Profile；默认读取 `SKILL_PROFILE_PATH` 或标准位置。
- `--chrome` 指定 Chrome/Chromium 可执行文件；也可设置 `CHROME_PATH`。
- `--format html` 只生成可复制、可手动下载的网页。
- `--scale 1-4` 控制 PNG 像素倍率；默认 2，即 1800×2700。

### Step 3: Inspect the actual card

- 确认输出 PNG 像素严格等于 900×1350 乘倍率。
- 检查脚本输出的 `layout`：`overflowX` 与 `overflowY` 必须为 0，`visualReady` 为 true。
- 打开 PNG 做视觉检查：标题层级、视觉槽完整性、Prompt 可读性、底部 Logo 大小与留白。
- 打开 HTML 测试“复制 Prompt”和“下载 PNG”。HTML 是可编辑母版，PNG 是传播稿。

任何溢出、图像未加载或尺寸不符都会让 PNG 导出失败；不要把失败说成完成。

### Step 4: Deliver and record evidence

报告 JSON、HTML、PNG 的绝对路径，倍率、像素尺寸与布局审计结果。真实使用案例可以
追加到 `cases/cases.json`，但必须记录 Input → Prompt → Output，不得制造案例或评分。

## Output contract

- 一个 UTF-8、自包含、可复制 Prompt 并可离线下载 PNG 的 HTML。
- 一个透明度与颜色保持一致的高分辨率 PNG；默认 1800×2700。
- 终端中的像素、字节数和 DOM 溢出审计。
- 如输入缺图、浏览器缺失或内容超出安全字号，返回可复制的具体错误，不输出假成品。

## Dependencies

- Python 3.9+，脚本仅使用标准库。
- PNG 自动导出需要 Chrome 或 Chromium。
- `modern-screenshot` 运行时随 Skill 内置；生成网页不依赖网络、npm 或兄弟 Skill。
