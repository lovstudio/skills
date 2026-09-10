# 额度体检 · Check Balance · Skill Card

## Description

看到你多个平台（例如 Claude Code、Codex、DeepSeek 等）账号的用量与重置时间，
并汇总本地消费速率，输出统一的文本表或 JSON。

## Owner

skill-publisher（contributors）。

## License

MIT。脚本在本机运行，凭据不离开本机。

## Use Case

同时使用多个 agent 或 API 平台的开发者，在被限流、余额见底或准备切换 provider
之前，需要一份可信的剩余额度视图。

## Deployment Geography

global；在 macOS 与 Linux 本地运行，macOS 上可使用 Keychain 作为凭据来源。

## Requirements

Python 3.8+ 标准库。可选输入：macOS Keychain、Codex auth.json、cc-switch SQLite、
LiteLLM 请求日志。无第三方依赖。

## Known Risks

- 凭据处理不当可能泄漏：脚本只做一次只读请求，从不打印或回传密钥。
- 过期登录态可能被误读为额度耗尽：过期单独标记为 expired 并提示重新登录。
- 预付余额批量结算会让短窗口速率失真：窗口短于 120 秒时标注不可靠并回退估算。

## References

- SKILL.md
- references/providers.md
- references/skill-composition.md

## Skill Output

额度体检表或 JSON，包含每个账号的状态、计划、窗口用量、重置时间、余额与提醒。
支持 --only、--watch、--min-balance-cny 等参数。

## Skill Version

0.1.1

## Ethical Considerations

只读访问本机凭据，不刷新、不上传、不落盘；不代用户执行充值或购买。结果可能包含
账号邮箱，对外分享前应自行脱敏。

## User Cases

1. 一次问清 Claude、Codex 与 DeepSeek 的剩余额度与重置时间；结论是 ChatGPT Pro
   周窗口已用满并于 2026-09-15 10:10 重置，Claude 官方凭据过期，DeepSeek 余额
   213.41 元由两条链路共用。
2. 被限流前发现周额度已用满，据此改用备用池或切换到预付余额路径继续工作。

## Dimension Map

- coverage（覆盖度）：六个独立探测覆盖订阅窗口、预付余额与本地消费。
- correctness（正确性）：重置时间与余额均来自官方接口字段。
- safety（安全性）：只读、不刷新、不打印密钥。
- actionability（可执行性）：直接给出剩余、重置时间与需要动作的条目。

## Pricing Basis

免费。纯本地标准库实现，无托管成本；不包含充值、订阅购买、密钥轮换与通知投递。

## Distribution

已准备：本地源码、lovstudio。付费渠道暂无计划。
