---
name: lov-describe-image
description: 给纯文本模型"看图"：调用智谱 GLM-4V-Flash（免费）把图片转成文字描述。当用户要求描述/识别/读取图片，或任务里出现图片文件（截图/图表/照片）而当前模型无法直接看图时，优先调用本 skill。需要图片磁盘路径，可附带具体问题。
license: MIT
metadata:
  author: mark
  version: "0.1.0"
  tags:
    - vision
    - image
    - describe
    - multimodal
    - glm-4v
    - ocr
---

# lov-describe-image

给纯文本模型"看图"：把图片发送给视觉模型（智谱 GLM-4V-Flash，免费），返回文字描述，让本身不具备视觉能力的模型（如 deepseek-v4-flash）能间接"看到"图片内容。

## Triggers

### Activate when

- 用户要求"看看/描述/识别/读懂/读取/识别这张图"，或询问图片里写了什么。
- 任务上下文里出现图片文件（截图、图表、照片、海报、含文字的图），而当前模型无法直接看图。
- 需要从含文字的图片（界面截图、文档扫描、图表）中提取具体信息，例如检查异常、转录文字、核对内容。

### Do not activate when

- 用户只是要求生成、编辑、压缩或转换图片，而不是理解图片内容。
- 当前模型本身具备视觉能力、能直接看到图片，无需转述。
- 用户明确要求走 dsh 的原生多模态管线、项目内置读图工具，或指定了其他视觉后端。

## Usage

```bash
python3 ~/.claude/skills/lov-describe-image/scripts/describe_image.py "<图片路径>" "[具体问题]"
```

- `<图片路径>` 必填：绝对路径，或相对当前工作区的路径（建议绝对路径，避免歧义）。
- `[具体问题]` 可选：想从图中知道的具体信息；省略则让视觉模型完整描述（物体/场景/布局/颜色/风格/所有文字）。

## Behavior

- 读取文件 → 超 5MB 自动用 `sips` 降采样到 2048px → base64 编码 → 调 GLM-4V-Flash（`max_tokens` 上限 1024）。
- 返回的文本就是视觉模型的回答，直接向用户转述，不要添油加醋，也不要声称"看到了原图"。
- 失败时（未设 key / 网络 / 尺寸超限）会打印明确错误，按提示处理即可。
- 小模型对细节核对（逐字转写）置信度有限；重要结论建议用更强的视觉模型（如 Gemini）交叉验证。

## Prerequisites

- 环境变量 `ZHIPU_API_KEY`（智谱 key，格式 `id.secret`，注册地址：https://bigmodel.cn/apikey/platform）。
- macOS 自带 `sips`（大图降采样）与 `python3`。
