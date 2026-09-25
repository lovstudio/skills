# Provider contracts

此页记录 `lov-voice2srt` 0.1.0 实现所依据的公开接口。API 与价格会变化；每次正式
使用仍应以 provider 官方页面和控制台为准，CLI 的 `--price-per-second` 可覆盖默认值。

## DashScope

- 默认模型：`qwen-audio-3.0-asr-flash`。
- 可在用户显式启用 `--openless-keychain` 后复用 OpenLess 百炼渠道的 API key；
  以渠道 `providerType` 判断协议，不依赖可能滞后的 map key。
- 同步 HTTP 输入单文件最长 5 分钟；Skill 默认切成 240 秒 MP3。
- 开启 SSE 后收集 `output.sentence`，只接收 `sentence_end=true` 的最终句。
- `parameters.vocabulary` 接收即时热词，权重 1–5 或 50；本 Skill 默认使用 5。
- 北京区公开价快照（2026-08-23）：0.00022 CNY/秒；输出不计费。
- 官方文档：
  - https://help.aliyun.com/zh/model-studio/non-real-time-speech-recognition-for-fun-asr-flash
  - https://help.aliyun.com/zh/model-studio/model-pricing

## Volcengine

- 默认接口：`POST https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash`。
- 最长 2 小时、100 MB，支持 WAV/MP3/OGG OPUS；一次请求返回句/词时间戳。
- 新控制台使用 `X-Api-Key`；旧控制台使用 `X-Api-App-Key` 与
  `X-Api-Access-Key`。资源 ID 固定使用 `volc.bigasr.auc_turbo`。
- 热词沿用 OpenLess 的 `request.context = JSON.stringify({hotwords:[...]})`。
- Skill 不内置火山引擎价格，因为账户服务包和开通项差异较大；用
  `--price-per-second` 在 dry-run 中提供本次实际单价。
- 官方文档：https://www.volcengine.com/docs/6561/1631584

## Local whisper.cpp fallback

- 运行 `whisper-cli`，默认查找 `~/Library/Caches/whisper.cpp/ggml-large-v3-turbo-q5_0.bin`。
- 个人词库通过 `--prompt` 进入 decoder context；这不是 provider 级 hotword 权重。
- 全程本地、无 API 成本。适合云端 key 失效、地区 endpoint 缺失或音频不能上传时。
- 上游项目：https://github.com/ggml-org/whisper.cpp
