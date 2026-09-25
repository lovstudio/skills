# 多模态 API 接入 · Multimodal API Setup · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

通过一个可移植的本地 Skill 调用 LovStudio.AI 的文本、音频与 Realtime API，输出结构化文本、转写结果、翻译结果或音频文件。

## Owner

手工川工作室 / LovStudio.AI；联系地址：https://lovstudio.ai

## License / Terms

Skill 客户端代码按 MIT 使用；模型调用、网络流量与上游渠道费用由调用方账户承担。

## Use Case

面向需要在 Agent、脚本或应用中统一调用 LovStudio.AI 的开发者与创作者，支持文本、音频文件和 Realtime PCM16 输入。

## Deployment Geography

用于本地 Agent Skills 目录，也可运行在支持 Python 3.8+ 并能访问 LovStudio API 的开发机或服务端。

## Requirements / Dependencies

凭据通过 `LOVSTUDIO_API_KEY` 进程环境变量提供；核心客户端使用 Python 3.8+ 标准库；Realtime 音频准备可选使用 ffmpeg。

## Known Risks and Mitigations

主要风险是密钥泄露、账户组未启用指定音频模型以及音频隐私边界。客户端只读环境变量并脱敏诊断；模型错误保留 context_id；发送语音前由调用方确认数据范围。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [LovStudio API contract](references/api-contract.md)

## Skill Output

输出包括 UTF-8 JSON 文本、转写或翻译结果、语音音频文件以及 Realtime 文本响应。结果带有 status 和 operation；错误带有 context_id；音频结果检查文件大小。

## Skill Version

0.1.0

## Ethical Considerations

仅发送调用方有权处理的文本与音频；对个人语音、会议录音和生成内容遵守适用的隐私、版权、告知与使用政策。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). The verified case records a Chinese PCM16 Realtime request and the returned text response.

### Dimension Map

The machine-readable card contains four dimensions: interface correctness, task coverage, diagnostic efficiency, and portability, each with evidence and a score status.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). This local Skill is free; model usage, credentials, cloud channel configuration, and remote deployment remain outside the bundle.

### Distribution

Paid channels (`workbuddy`, `skillpay`) are planned. Free channels are `github`
planned and `lovstudio` local-only; no remote publication is claimed.
