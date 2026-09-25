# 语音成字幕 · Voice to Subtitles · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把本地音频或视频转成带可靠时间戳的 SRT、JSON 与纯文本，并以 OpenLess 或
canonical personal vocabulary 增强产品名、技术名和英文缩写。

## Owner

LovStudio Skills；联系入口为 LovStudio Skills catalog。

## License / Terms

MIT。用户负责确认有权处理输入媒体；云端调用同时受对应 provider 条款约束。

## Use Case

面向访谈、录屏、播客与自媒体视频创作者。输入本地音视频和可选个人词库，输出
可进入剪辑流程的字幕包。

## Deployment Geography

可在具备 Python 3.9+、FFmpeg/FFprobe 与网络访问的 macOS、Linux、Windows 运行。

## Requirements / Dependencies

需要 DashScope 或 Volcengine ASR credential。凭据只在运行时读取；OpenLess
Keychain 必须由用户显式启用。词库 Skill 通过 JSON 文件交接，不是安装依赖。

## Known Risks and Mitigations

主要风险是云端音频隐私、错误热词诱导、分段边界重叠和 API 价格/契约变化。
工作流通过 provider 披露、成本门禁、词库上限、时间轴验证和可覆盖配置降低风险。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

输出 `transcript.srt`、`transcript.json`、`transcript.txt`、`report.json` 和本地 raw
响应。验证 cue 有效性、重叠、媒体边界、SRT 解析与凭据脱敏。

## Skill Version

0.1.0

## Ethical Considerations

只处理用户有权转写的媒体；调用前说明 provider；不保存 key；不把“已传热词”
等同于“识别正确”，必须回看真实结果。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free Skills still explain their value,
boundary, and review trigger.

### Distribution

Keep paid channels (`workbuddy`, `skillpay`) and free channels (`github`, `lovstudio`)
explicit. A planned or unavailable channel must not be described as live.
