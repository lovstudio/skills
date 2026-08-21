# Skill Card — lov-app-adapters

## Description

定义 OpenLess、Typeless 等语音输入法词汇表的读写映射；本地 JSON 直接读写，API 走用户凭据只读探测。

## Owner

LovStudio / 手工川工作室 — https://lovstudio.ai

## License / Terms

MIT；用户只读写自己的词库，不绕过授权。

## Use Case

需要把词库同步进具体语音输入法/剪辑工具的用户，读取或写入某款 App 的词汇表。

## Deployment Geography

Global；本地 agent runtime + 用户本机词库文件与账号凭据。

## Requirements / Dependencies

- Python 3.9+（仅标准库）
- 用户授权访问本机词库或账号凭据

## Known Risks and Mitigations

- App 格式未知 → 先探测再补映射，未确认前标注并拒绝写入。
- API 凭据泄露 → 凭据仅内存用于只读请求，不持久化、不打印。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

各 App 格式词库文件（JSON）。

## Skill Version

0.1.0

## Ethical Considerations

仅读写用户自己的词库；不批量逆向，凭据不落盘。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：OpenLess 与 Typeless 两套字段结构已确认并映射。

### Dimension Map

- correctness（映射准确）：4 — OpenLess 与 Typeless 字段已实测。
- effectiveness（覆盖主流 App）：3 — OpenLess/Typeless 已适配，剪映待探测。
- efficiency（声明式映射）：4 — render 秒级生成。

### Pricing Basis

免费，通用适配层。

### Distribution

free：github、lovstudio；paid：无。
