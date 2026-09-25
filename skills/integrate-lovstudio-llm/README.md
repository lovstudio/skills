# 多模态 API 接入 · Multimodal API Setup

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

LovStudio.AI 的统一 API Skill：文本对话、语音转文字、语音翻译、语音合成和 Realtime 音频输入。

## 本地安装

在 Skill 源目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-integrate-lovstudio-llm-skill"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 配置

只在进程环境中提供密钥：

```bash
export LOVSTUDIO_API_KEY="..."
export LOVSTUDIO_BASE_URL="https://llm.lovstudio.ai/v1"
```

可通过环境变量覆盖默认模型：`LOVSTUDIO_CHAT_MODEL`、
`LOVSTUDIO_TRANSCRIBE_MODEL`、`LOVSTUDIO_TRANSLATE_MODEL`、
`LOVSTUDIO_SPEECH_MODEL`、`LOVSTUDIO_REALTIME_MODEL`。

## 使用

```bash
SKILL_DIR="${SKILL_DIR:-$(pwd)}"

python3 "$SKILL_DIR/scripts/lovstudio_llm.py" \
  chat --prompt "用一句话介绍 LovStudio.AI"

python3 "$SKILL_DIR/scripts/lovstudio_llm.py" \
  transcribe --file ./meeting.wav --model whisper-1

python3 "$SKILL_DIR/scripts/lovstudio_llm.py" \
  speech --text "生命的意义在于创作" --output ./speech.mp3

ffmpeg -i ./meeting.wav -ar 24000 -ac 1 -f s16le ./meeting.pcm
python3 "$SKILL_DIR/scripts/realtime_client.py" \
  --file ./meeting.pcm \
  --response-instructions "请逐字复述刚才听到的中文语音。"
```

`lovstudio_llm.py` 使用 OpenAI-compatible HTTP 路由：
`/v1/chat/completions`、`/v1/audio/transcriptions`、
`/v1/audio/translations` 和 `/v1/audio/speech`。Realtime 客户端连接
`/v1/realtime?model=gpt-realtime`，输入为 24 kHz PCM16。

每个失败结果都带有 `context_id`，方便复制给开发者排查；密钥不会写入
Profile、Skill 源码或诊断输出。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+ 标准库
- LovStudio API 密钥和网络访问
- 仅在准备 Realtime 音频时需要 `ffmpeg` 等媒体转换工具

如果 macOS 系统 Python 报告 `SSLEOFError`，请使用带现代 OpenSSL 的 Python
运行时再访问云端地址；本地 HTTP 地址不受此 TLS 环境差异影响。

## License

MIT
