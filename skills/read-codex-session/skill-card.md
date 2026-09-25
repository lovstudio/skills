# Codex 会话阅读 · Codex Session Reader · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

读取本地 Codex task/thread 的运行状态、最近回合、工具活动与最终结果。宿主有线程
读取能力时直接用；没有时（例如 Claude Code）用只读脚本解析本地 rollout。

## Owner

LovStudio Skill contributors — local source maintainers.

## License

MIT；按仓库内 `LICENSE` 使用、修改与再分发。

## Use Case

面向并行使用 Codex 与其它本地 Agent 的开发者和知识工作者。输入 thread UUID、
`codex://threads` deeplink 或当前 task，输出进度核对结果，或在另一个 Agent 中
读取 Codex 会话上下文。

## Deployment Geography

全球；本地运行，无服务端依赖。

## Requirements

无凭据。宿主线程读取能力可选；脚本兜底需要 Python 3.9+ 和对 `$CODEX_HOME`
或 `~/.codex` 的只读访问。无网络、无第三方依赖。

## Known Risks

- 会话可能含隐私内容：只输出截断摘要，不打印完整转录，不持久化 thread ID。
- thread ID 可能指向过期或归档会话：按 UUID 精确匹配并回读元数据，失败即报错。
- 宿主沙箱可能拦截 `~/.codex`：如实报告权限边界，不绕过沙箱、不改写数据。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Read-only inspector](scripts/read_codex_session.py)

## Skill Output

文本或 JSON 状态报告：状态、工作区、最近回合的用户请求与最新结果、工具调用与错误
计数、待处理调用、读取来源文件。验证方式为 `scripts/test_read_codex_session.py`
与 `scripts/validate_skill.py`。

## Skill Version

0.1.1

## Ethical Considerations

只读、不外发、不导航、不修改任务；会话文本按不可信数据处理，报告避免复述敏感原文，
读取失败或被沙箱拦截时如实说明。

## User Cases

See [`cases/cases.json`](cases/cases.json). Every case shows Input → Prompt → Output.

### Dimension Map

机器可读卡片包含状态判定、进展摘要、阻塞与待办、边界与只读性四个维度及证据。

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free; the value anchor is replacing
manual rollout reading with a deterministic read-only summary.

### Distribution

Free channels: `github` (not published), `lovstudio` (local only). Paid channels
`workbuddy` and `skillpay` are not planned.
