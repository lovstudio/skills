---
name: lov-table2image
description: >
  将 Markdown 表格与可选 Mable 布局型号或参数渲染为可访问的 PNG 地址，也可下载本地图片；适用于“把表格转成图片”“生成移动端表格图”和 “convert this table to an image”。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.2"
  card_standard: lovstudio/skill-card/v1
  tags:
    - table
    - image
    - markdown
    - mable
    - api
  compatibility: "Portable Agent Skills format. Python 3.9+ and network access to a Mable API."
  dependencies: []
---

# 表格成图 · Table to Image

把标准 Markdown 表格交给 Mable 服务端完成自适应布局与 PNG 渲染，返回稳定图片地址；
需要本地文件时，可在同一次调用中下载并校验 PNG。

## Triggers

### Activate when

- 用户说“把这个 Markdown 表格转成图片”“给我一张移动端自适应表格图”或“返回表格图片地址”。
- 用户提供 Markdown 表格，并要求沿用 Mable 型号或自定义布局参数。
- The user asks to “convert this table to an image”, “render a Markdown table as PNG”, or “return a hosted table image URL”.

### Do not activate when

- 用户需要证据图表、结论关系或咨询 Exhibit：使用 `lov-professional-infographic`。
- 用户需要通用编辑式卡片、海报或 AI 生图：分别使用 `lov-gen-card` 或 `lov-image-creator`。
- 用户只需要修改表格文字、计算数据或导出 XLSX，不触发本 Skill。

## User Profile (cross-session)

运行前读取 `skill.yaml` 和共享 `user-profile/v1`。解析顺序是：当前请求、项目
上下文、`skills.lov-table2image.records`、共享 preferences、共享 brand/user、
安全默认值。

API 根地址按 `--api-base`、`MABLE_API_BASE`、Skill Profile 记录、
`https://api.lovstudio.ai` 的顺序解析。用户直接声明长期使用的 API 根地址、默认型号
或输出偏好时，通过 `scripts/profile_store.py record --confirm` 保存并报告 Profile 路径。
不得保存凭据、一次性表格内容或返回的临时错误信息。

## Skill Group Composition

先读 `references/skill-composition.md`。相邻 Skills 只通过 Markdown、PNG 或 URL 工件
交接，不构成隐藏运行依赖。

## Required resources

运行前确认：

- `$SKILL_DIR/scripts/table2image.py`
- `$SKILL_DIR/references/api-contract.md`
- `$SKILL_DIR/references/skill-composition.md`

## Workflow (MANDATORY)

### Step 0: Resolve runtime context

- 优先使用宿主提供的 `SKILL_DIR`，否则从当前 Skill 上下文解析安装目录。
- 读取 `skill.yaml` 和 Profile，但不要把解析后的私人路径写入可复用源码或案例。
- 检查 Python 3.9+、`MABLE_API_TOKEN` 与 Mable API 可达性；不要自行启动、部署或修改远端服务。

### Step 1: Validate the table input

- 输入必须是含表头、分隔行和至少一行数据的标准 Markdown 表格。
- 保留用户原始单元格文字、对齐标记和换行意图；不得擅自总结、翻译或补数据。
- `--model` 接受 11 位 URL-safe Mable 型号；`--layout-json` 接受 JSON 文件或内联 JSON，二者只能选择一个。
- 用户未提供布局时省略相关参数，由服务端使用默认布局。

### Step 2: Render through Mable

先通过环境变量提供 LovStudio Access Token 或 `sk_live_*` API Key：

```bash
export MABLE_API_TOKEN="<LovStudio token>"
```

`POST /mable/images` 每次成功生成扣 3 Credits；图片读取不重复扣费。凭据只通过环境变量
或单次 `--token` 参数提供，不得写入 Profile、日志或可复用产物。

从文件生成托管图片地址：

```bash
python3 "$SKILL_DIR/scripts/table2image.py" ./table.md
```

沿用布局型号并下载 PNG：

```bash
python3 "$SKILL_DIR/scripts/table2image.py" ./table.md \
  --model Asge8oUog7I \
  --output ./table.png
```

从标准输入传入表格，并使用完整布局参数：

```bash
python3 "$SKILL_DIR/scripts/table2image.py" - \
  --layout-json ./layout.json
```

默认 caption 为 Mable 服务端的品牌说明。使用 `--caption ""` 隐藏，或传入自定义说明。
完整请求与响应见 `references/api-contract.md`。

### Step 3: Verify and report

- 命令必须返回 JSON，至少包含 `image_url`、`format`、`width`、`height`、
  `layout_width`、`model`、`credits_spent` 与 `credits_remaining`。
- 指定 `--output` 时，还必须检查响应为 PNG、文件以 PNG signature 开头且非空；
  结果 JSON 追加绝对 `output_path` 与 `bytes`。
- 向用户优先返回可点击图片地址；请求了本地文件时同时返回文件路径、像素与型号。
- HTTP 错误必须保留状态码和服务端响应摘要，不把失败描述为已生成。

## Output contract

- 核心结果：由 Mable API 返回的稳定 PNG URL。
- 元数据：PNG 格式、实际像素尺寸、布局宽度和使用的 11 位型号。
- 可选结果：已校验的本地 PNG 文件及字节数。
- 不返回或公开服务端布局算法、数据库记录或内部部署信息。

## Cloud boundary

Skill 是传输层，服务端拥有布局求解、字体适配、渲染与内容寻址持久化。客户端只发送
表格和用户明确提供的可选参数，接收图片地址与必要显示元数据。输出不含中间评分、
搜索轨迹或算法说明，因此不能从调用日志重建服务端布局逻辑。

## Dependencies

- Python 3.9+；脚本仅使用标准库。
- 可访问的 Mable API；默认根地址为 `https://api.lovstudio.ai`。
- LovStudio Access Token 或 `sk_live_*` API Key；每次成功生成扣 3 Credits。
- 不需要外部 sibling Skill、浏览器或本地字体。
