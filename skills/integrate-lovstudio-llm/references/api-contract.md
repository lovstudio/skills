# LovStudio API contract

## Connection

- Base URL: `LOVSTUDIO_BASE_URL`, default `https://llm.lovstudio.ai/v1`.
- Credential: `LOVSTUDIO_API_KEY`, read only from the process environment.
- HTTP authentication: `Authorization: Bearer $LOVSTUDIO_API_KEY`.
- Realtime authentication: the same Bearer header plus `OpenAI-Beta: realtime=v1`.
- The Python runtime needs a TLS stack that can negotiate the endpoint. On
  macOS, use a current Python build with OpenSSL when the system Python reports
  an `SSLEOFError` during the handshake.

The API follows the OpenAI-compatible resource names below. Model availability
belongs to the active account group and can change independently from this
Skill source.

## HTTP operations

| Operation | Route | Typical model | Input | Output |
| --- | --- | --- | --- | --- |
| Chat | `/v1/chat/completions` | `gpt-4o-mini` | JSON messages | JSON text choice |
| Transcription | `/v1/audio/transcriptions` | `whisper-1` | multipart audio | JSON transcript |
| Translation | `/v1/audio/translations` | `whisper-1` | multipart audio | JSON English text |
| Speech | `/v1/audio/speech` | `gpt-4o-mini-tts` | JSON text and voice | audio bytes |

The bundled HTTP client preserves the model as an explicit option. A
`model_not_found` or `OperationNotSupported` response means the current group
needs a compatible upstream audio channel; it is not a client parsing error.

## Realtime operation

- WebSocket route: `/v1/realtime?model=gpt-realtime`.
- Input format: mono PCM16, 24 kHz, sent as Base64 in
  `input_audio_buffer.append` events.
- The client commits the buffer and requests a text response.
- Useful server events include `session.created`, `session.updated`,
  `conversation.item.input_audio_transcription.completed`,
  `response.text.done`, and `response.done`.

The Realtime client uses a small standard-library WebSocket implementation so
the Skill stays installable without a third-party Python package.

## Runtime selection

Use these environment variables for deployment-specific defaults:

| Variable | Purpose |
| --- | --- |
| `LOVSTUDIO_CHAT_MODEL` | Chat Completions default |
| `LOVSTUDIO_TRANSCRIBE_MODEL` | HTTP transcription default |
| `LOVSTUDIO_TRANSLATE_MODEL` | HTTP translation default |
| `LOVSTUDIO_SPEECH_MODEL` | Speech default |
| `LOVSTUDIO_REALTIME_MODEL` | Realtime default |
| `LOVSTUDIO_REALTIME_URL` | Realtime WebSocket endpoint |
| `LOVSTUDIO_REALTIME_TRANSCRIPTION_MODEL` | Optional Realtime transcription model |
