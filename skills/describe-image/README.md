# lov-describe-image

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

给纯文本模型"看图"：把图片发送给视觉模型（智谱 GLM-4V-Flash，免费），返回文字描述，让本身不具备视觉能力的模型（如 `deepseek-v4-flash`）能间接"看到"图片内容。

## 解决的问题

在 Claude Code + 纯文本 DeepSeek（`api.deepseek.com/anthropic`）这类环境下，模型没有原生视觉能力，粘贴的图片无法被直接理解。本 skill 用一个免费视觉模型作为"眼睛"：读入图片文件 → base64 编码 → 调 GLM-4V-Flash → 把文字描述转述回给调用模型。

## 安装

```bash
# 真源（Lovstudio 三层 symlink 约定）
mkdir -p ~/lovstudio/coding/skills
git clone <this-repo> ~/lovstudio/coding/skills/lov-describe-image-skill  # 或直接拷贝目录
ln -sfn ~/lovstudio/coding/skills/lov-describe-image-skill ~/.agents/skills/lov-describe-image
ln -sfn ../../.agents/skills/lov-describe-image ~/.claude/skills/lov-describe-image
```

## 配置

设置智谱 API Key（注册地址 https://bigmodel.cn/apikey/platform，key 格式 `id.secret`）：

```bash
export ZHIPU_API_KEY="你的key"   # 建议写入 ~/.zshenv 长期生效
```

## 用法

```bash
python3 ~/.claude/skills/lov-describe-image/scripts/describe_image.py "<图片路径>" "[具体问题]"
```

- `<图片路径>` 必填：绝对路径，或相对当前工作区的路径。
- `[具体问题]` 可选：想从图中知道的具体信息；省略则完整描述（物体/场景/布局/颜色/风格/所有文字）。

在 Claude Code 中，直接说"看看这张图 <路径>" 即可自动触发。

## 行为细节

- 超 5MB 图片自动用 macOS 自带 `sips` 降采样到 2048px。
- `glm-4v-flash` 的 `max_tokens` 上限是 1024，脚本已固定，设大会被 API 400 拒绝。
- 请求超时 60s；失败时输出明确错误（未设 key / 网络 / 格式 / 尺寸超限）。

## 已知限制

- 视觉后端是 GLM-4V-Flash（免费档），对**细节核对**（逐字转写、精确比对）置信度有限，多次调用可能给出前后不一致的答案；重要结论建议用更强的视觉模型（如 Gemini）交叉验证。
- 需要图片的**磁盘路径**；仅有 `[Image #N]` 占位符而无可读路径时无法工作，需向用户索要路径。
- 只做图片→文字，不做图片生成、编辑或转换。

## 换视觉后端

改 `scripts/describe_image.py` 顶部的 `BASE_URL` / `MODEL` / `apiKeyEnv` 即可切换到任意 OpenAI 兼容视觉端点（如 SiliconFlow 的 Qwen-VL）。

## License

MIT
