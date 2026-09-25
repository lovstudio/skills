---
name: lov-integrate-lovstudio-llm-skill
description: >
  通过 LovStudio.AI 的 OpenAI-compatible API 完成文本对话、语音转文字、语音翻译、语音合成与 Realtime 音频会话；用户说“接入 Lovstudio LLM”“调用语音转文字”或 “use LovStudio API” 时触发。
license: MIT
metadata:
  author: LovStudio.AI
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - lovstudio
    - llm-api
    - speech-to-text
    - realtime
  compatibility: "Python 3.8+ standard library; network access to an OpenAI-compatible LovStudio API."
  dependencies: []
---

# 多模态 API 接入 · Multimodal API Setup

把 LovStudio.AI 作为统一的 OpenAI-compatible 模型入口，按任务调用文本、音频和 Realtime API，并返回可继续处理的结构化结果。

## Triggers

### Activate when

- 用户说“接入 Lovstudio LLM”“帮我调用 Lovstudio 的语音转文字接口”或“用 Lovstudio 生成语音”。
- User asks to “use LovStudio API”, “transcribe this audio with LovStudio”, or “start a LovStudio realtime session”.

### Do not activate when

- 用户要创建云端渠道、修改 New API 管理配置或发布 Skill；这些属于部署与发布工作流。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-integrate-lovstudio-llm-skill"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Resolve connection context

- Read the shared Profile and `skills.lov-integrate-lovstudio-llm-skill` records through `scripts/profile_store.py read --skill-id lov-integrate-lovstudio-llm-skill`.
- Load `references/api-contract.md` when choosing an endpoint, model, audio format, or Realtime event.
- Read `LOVSTUDIO_API_KEY` from the process environment. Never place it in a prompt, Profile record, source file, or command argument.
- Use `LOVSTUDIO_BASE_URL` when supplied; the default is `https://llm.lovstudio.ai/v1`.
- Before a real call, verify the selected model and operation are enabled in the current account group.

### Step 2: Select and call an operation

Use the deterministic local clients. They emit JSON on success and a copyable `context_id` on errors.

| Goal | Command | Default model |
| --- | --- | --- |
| Text response | `python3 "$SKILL_DIR/scripts/lovstudio_llm.py" chat --prompt "..."` | `gpt-4o-mini` |
| Speech to text | `python3 "$SKILL_DIR/scripts/lovstudio_llm.py" transcribe --file INPUT` | `whisper-1` |
| Audio translation | `python3 "$SKILL_DIR/scripts/lovstudio_llm.py" translate --file INPUT` | `whisper-1` |
| Text to speech | `python3 "$SKILL_DIR/scripts/lovstudio_llm.py" speech --text "..." --output OUTPUT.mp3` | `gpt-4o-mini-tts` |
| Realtime audio input | `python3 "$SKILL_DIR/scripts/realtime_client.py" --file INPUT.pcm` | `gpt-realtime` |

For Chat Completions with conversation history, pass a JSON array through
`--messages-json` or a UTF-8 file through `--messages-file`. Use `--model` for
an explicit model choice. Keep `--api-key` out of the interface so credentials
stay outside shell history.

The Realtime client expects mono PCM16 at 24 kHz. It sends audio in timed chunks,
requests text output, and can return the model's recognized speech as a reply.
Convert a WAV or AIFF file with an installed media tool before calling it:

```bash
ffmpeg -i INPUT.wav -ar 24000 -ac 1 -f s16le INPUT.pcm
python3 "$SKILL_DIR/scripts/realtime_client.py" \
  --file INPUT.pcm \
  --response-instructions "请逐字复述刚才听到的中文语音。"
```

If the HTTP transcription command returns `model_not_found`, preserve its
`context_id` and check the active channel's audio-transcription model list.
Realtime remains the voice-input path when the provider exposes Realtime but
has not enabled `/v1/audio/transcriptions`.

### Step 3: Validate the result

- Check the returned `status`, `operation`, model, and output field before presenting the result.
- For audio outputs, confirm the requested output file exists and has non-zero size.
- On errors, show the structured `context_id`, operation, source, HTTP status, and message so the caller can copy them for debugging.
- Run `python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"` when changing the Skill source.

## Dependencies

- Python 3.8+ standard library for the bundled clients.
- A valid `LOVSTUDIO_API_KEY` environment variable and network access to the configured endpoint.
- Optional `ffmpeg` or another media converter when preparing PCM16 Realtime input.
