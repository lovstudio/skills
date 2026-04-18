---
name: lovstudio:document-illustrator
category: Content Processing
tagline: "为文档原地插入 AI 配图。全局规划插入点，并行生成，异步插回原文。"
description: >
  为文档原地插入 AI 配图。读取文档后全局规划插入点，并行生成所有图片，
  异步插回原文。支持封面图、自定义比例和三种风格。
  Use when: 用户要求为文档/文章/笔记生成配图、插图。
  Also trigger when user mentions: 配图、插图、illustration、
  generate images、document images、为文章加图。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash(python:*)
  - Glob
  - Agent
  - AskUserQuestion
model: claude-opus-4-5-20251101
metadata:
  version: 0.2.0
  author: lovstudio
license: MIT
compatibility: ">=1.0"
---

# Document Illustrator Skill

基于 AI 智能分析的文档配图生成工具。全局规划、并行生成、异步插入，高效为文档添加配图。

## 核心流程（5 步）

```
备份 → 全局规划插入点 → 并行生成图片 → 异步插入原文 → 清理备份
```

### Step 0: 备份原文件

在修改前先创建备份，确保安全回滚：

```python
import shutil
backup_path = f"{doc_path}.illustrator-backup"
shutil.copy2(doc_path, backup_path)
```

所有后续操作直接在原文件上进行。

### Step 1: 全局确定所有插入位置

读取完整文档，一次性规划所有图片的插入位置：

1. 使用 Read 工具读取完整文档
2. AI 分析内容结构，识别核心主题
3. 为每个主题确定**精确的插入锚点**（行号 + 上下文文本）
4. 输出一份插入计划表：

```
插入计划：
  [1] 行 15 后 | 锚点: "## Rules 的诞生" | 主题: Rules 演化历程
  [2] 行 42 后 | 锚点: "## Commands 打包" | 主题: 工作流打包
  [3] 行 78 后 | 锚点: "## MCP 动态能力" | 主题: 第三方集成
  ...
  [cover] 行 1 前 | 封面图 | 主题: 全文概要
```

**关键**：插入锚点使用上下文文本（而非纯行号），这样即使前面的插入导致行号偏移，后续插入仍可通过锚点定位。

### Step 2: 并行生成所有图片

用 Agent 工具并行启动所有图片生成子任务：

```
对每个插入计划项，同时启动一个 Agent：
  Agent 1: generate_single_image.py --title "..." --content "..." --output images/illustration-01.png
  Agent 2: generate_single_image.py --title "..." --content "..." --output images/illustration-02.png
  Agent 3: generate_single_image.py --title "..." --content "..." --output images/illustration-03.png
  ...
```

- 所有 Agent 并发执行，不互相等待
- 每个 Agent 完成后返回图片路径或错误信息
- 预期总耗时 = 单张耗时（10-20s），而非 N * 单张耗时

### Step 3: 异步插入原文

每个 Agent 完成后立即插入，不等待其他 Agent：

1. Agent 完成 → 获得图片路径
2. 在原文档中**通过锚点文本**定位插入位置（不依赖行号）
3. 使用 Edit 工具在锚点后插入 Markdown 图片引用：
   ```markdown
   ![主题描述](images/illustration-01.png)
   ```
4. 插入使用锚点文本匹配，所以前面的插入不影响后面的定位

**位置偏移处理**：
- 每次插入会增加文档行数
- 使用锚点文本（如 `## Rules 的诞生`）而非行号来定位
- 从文档末尾向开头方向插入也可避免偏移问题

### Step 4: 验证与清理

所有图片插入完成后：

1. **验证**：检查原文档中所有计划的 `![...]()` 引用都已插入
2. **验证**：检查所有图片文件都存在于 `images/` 目录
3. **成功** → 删除备份文件 `{doc_path}.illustrator-backup`
4. **失败** → 保留备份文件，报告哪些图片未能生成/插入，用户可用备份恢复

```
完成: 6/6 张配图已插入原文档
已清理备份文件
```

## 配置选项

执行前 Claude 会询问（或从用户消息中推断）：

| 选项 | 值 | 默认 |
|------|-----|------|
| 图片比例 | 16:9 / 3:4 | 16:9 |
| 是否封面图 | 是/否 | 否 |
| 内容配图数量 | 3-10 | 根据文档长度推荐 |
| 风格 | gradient-glass / ticket / vector-illustration | gradient-glass |

如果用户在请求中已指定（如"竖屏、票据风格、8张"），直接使用，不再询问。

## 风格速查

| 风格 | 关键词 | 适合 |
|------|--------|------|
| gradient-glass | 玻璃拟态、极光渐变、科技感 | 技术文档、产品介绍 |
| ticket | 黑白对比、票券结构、极简 | 数据报告、信息图表 |
| vector-illustration | 扁平插画、复古配色、几何化 | 教程、故事、品牌 |

风格文件位于 `styles/` 目录。

## 技术细节

| 项目 | 值 |
|------|-----|
| API 模型 | Gemini 2.0 Flash Image Preview |
| 16:9 分辨率 | 2560x1440 (2K) / 3840x2160 (4K) |
| 3:4 分辨率 | 1920x2560 (2K) / 2880x3840 (4K) |
| 单张耗时 | ~10-20s |
| 并行耗时 | ~10-20s（总，不乘 N） |
| 依赖 | `pip install google-genai pillow python-dotenv` |
| API Key | `.env` 中 `GEMINI_API_KEY` 或环境变量 |

## 脚本

- `scripts/generate_single_image.py` — 单张图片生成（供 Agent 并行调用）
- `scripts/generate_illustrations.py` — 旧版批量顺序生成（保留兼容）
