---
name: lov-business-card
description: >
  Generate a professional, editorial-style business card (2:1) as a
  high-resolution PNG and a self-contained interactive HTML. Collects the user's
  identity (name, roles, tagline, interests, locations, optional avatar), fills a
  parameterized design template with a chosen theme, and renders it via headless
  Chrome. Trigger when the user wants to make a business card, personal card, name
  card, profile card, or "电子名片", or says "生成名片", "做一张名片", "个人名片",
  "make a business card", "design a name card".
license: MIT
compatibility: >
  Portable Agent Skills format. Requires Python 3.8+ and a Chromium-based browser
  (Google Chrome or Chromium) for PNG rendering; without one, the HTML still works
  in any browser via its built-in download button. macOS uses sips for cropping,
  other platforms need Pillow. All identity/brand/output values come from CLI
  flags — no personal paths are hard-coded.
metadata:
  author: contributors
  version: "0.2.0"
  tags: business-card, design, branding, png, html
---

# business-card — 专业精美电子名片生成器

把任意用户的身份信息，渲染成一张 2:1 的编辑式（editorial / luxury-minimal）名片：
瑞士排版网格、发丝线分隔、单一强调色、宋体 × Didot 字体配对。输出高分辨率 PNG
（默认 4800×2400）+ 一个自包含、可在浏览器点击下载的 HTML。

## 工作流

### 1. 先用 AskUserQuestion 收集信息（必做）

**不要直接跑脚本。** 先确认主题与必填项。能从对话/记忆里推断的先预填，只问不知道的。

建议问题（一次最多 3 个）：

- **主题**：dark-terracotta（暖深·陶土，默认）/ midnight（冷深·钢蓝）/ ivory（浅·象牙编辑风）
- **是否有头像**：有 → 要文件路径；无 → 用名字首字渲染 monogram
- **强调词**：tagline 里哪个词要高亮（强调色）

身份字段尽量从上下文取；缺的逐项问或让用户一次性给。

### 2. 映射到 CLI 参数

| 用户提供 | flag | 说明 |
|---|---|---|
| 姓名 | --name | 必填，支持中文 |
| 英文名/罗马音 | --latin | 名字旁的斜体小字 |
| 品牌（左上） | --brand | 如 SKILL.AI（含 . 会高亮圆点） |
| 编号（右上） | --index | 如 STUDIO — Nº 2026 |
| 角色标签 | --tags | 逗号分隔，菱形分隔渲染 |
| 金句 | --tagline | **词** 高亮，竖线 \| 换行 |
| 爱好/兴趣 | --pursuits | 逗号分隔（底栏左） |
| 据点/城市 | --bases | 逗号分隔，每项带定位针（底栏右） |
| 头像 | --avatar | 图片路径；省略则用 monogram |
| 头像图注 | --caption | 可选，肖像底部小字 |
| 主题 | --theme | dark-terracotta｜midnight｜ivory |
| 输出目录 | --out | 默认 ./output |
| 格式 | --format | png｜html｜both（默认 both） |

### 3. 运行

```bash
python3 scripts/render_card.py \
  --name "品牌方" --latin "Mark Shawn" \
  --brand "SKILL.AI" --index "STUDIO — Nº 2026" \
  --tags "背包客,超级开发者,AI / OPC 布道师" \
  --tagline "在 **Agent 时代**，|寻找**人**的意义" \
  --pursuits "旅行,羽毛球,计算机科学,心理学,哲学" \
  --bases "上海 陆家嘴数智港,北京 搜狐大厦清智孵化器" \
  --avatar ./me.png --theme dark-terracotta \
  --out ./output --format both
```

### 4. 交付

把 PNG 展示给用户；告诉他们 HTML 可在浏览器打开、右下角「下载为图片 PNG」自出 3× 高清图
（HTML 与同目录的 modern-screenshot.umd.js 需一起保留）。

## 设计说明

- 比例：固定 2:1（1600×800 画布），PNG 按 --scale 倍率导出（默认 3 → 4800×2400）。
- 自适应：HTML 在浏览器里等比缩放铺满视口，绝不放大、不溢出；导出尺寸不受影响。
- 无头像：自动用姓名首字渲染衬线 monogram，仍然专业。
- 主题扩展：在 scripts/render_card.py 的 THEMES 字典加一组 CSS 变量即可。

## User Configuration

本 skill 不假设任何私有工作区。所有身份、品牌、输出路径都由 CLI flag 传入；
--out 默认当前目录下 ./output。如需复用默认身份，调用方可自行从用户 profile
预填这些 flag，但脚本本身不读取任何固定个人路径。

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
