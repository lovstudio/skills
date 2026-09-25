# 项目寻踪 · Project Finder · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

分层定位本机项目 / 源码目录。给定项目名、关键词或特征描述，按
「项目根目录 → 当前文件夹 → AI 聊天记录 → 全盘」四层递进搜索，返回候选绝对
路径与每层命中证据。不修改任何文件。

## Owner

Lovstudio 工作室（手工川）。contact: lovstudio

## License / Terms

MIT。免费使用并注明来源。本 Skill 不包含任何 Anthropic 私有源码。

## Use Case

**受众**：需要在本机多个工作区之间快速定位某个项目/源码副本的开发者。

**输入**：项目名、别名、关键词，或特征描述（如「claude code 泄露源码」）。

**任务**：定位候选目录；从 AI 聊天记录回溯项目路径；全盘确认是否存在。

## Deployment Geography

macOS 本机（依赖 Spotlight mdfind、Finder 目录结构）。代码层面可移植到其他
POSIX 系统，仅 full 层需替换索引工具。

## Requirements / Dependencies

- 凭据：无
- 运行时：Python 3.8+
- 可选：ripgrep（聊天记录层加速）、macOS Spotlight `mdfind`（全盘层）
- 第三方包：无

## Known Risks and Mitigations

1. **全盘搜索命中同名无关目录** → 候选按匹配分数排序并标注命中层，full 层
   明确提示「可能存在同名无关目录」，由用户确认。
2. **聊天记录搜索耗时** → 默认只扫 `.claude/projects` 与 `.gemini` 的 jsonl，
   有 ripgrep 时快扫，限制每文件行数与文件总数。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Composition record](references/skill-composition.md)

## Skill Output

- 类型：候选项目绝对路径列表（JSON / 结构化文本结论）
- 格式：CLI `--json` 输出 + 人类可读结论
- 参数：`query`、`scope`（auto|roots|cwd|chat|full）、`--limit`
- 校验：候选路径必须真实存在；结论标注命中层与证据来源

## Skill Version

0.2.0

## Ethical Considerations

仅在本机文件系统与用户自己的 AI 聊天记录内搜索，不访问远程仓库、不扫描他人
文件。对聊天记录只做关键词与路径提取，不输出敏感对话正文。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json)：真实案例「从聊天记录定位 claude-code
泄露源码目录」，Input → Prompt → Output 完整记录。

### Dimension Map

`skill-card.yaml` 中 correctness / effectiveness / efficiency 三维度均有证据
与自评分（5 / 5 / 4）。

### Pricing Basis

[`pricing-card.yaml`](pricing-card.yaml)：纯本地搜索能力、无外部成本，免费
分发；边界为不含远程仓库搜索与代码内容理解。

### Distribution

免费渠道：github、lovstudio。付费渠道（workbuddy、skillpay）当前均不可用，
不宣称上线。
