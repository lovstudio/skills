# Skill Card — lov-personal-vocabulary

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把散落在各语音输入法里的个人词条收敛成一份规范词汇表，并映射回 OpenLess、Typeless 等 App；按 phrase 去重、产出只读同步计划，确认后再写入。

## Owner

LovStudio / 手工川工作室 — https://lovstudio.ai

## License / Terms

MIT；用户只维护自己的词库与凭据，App 词条不做批量逆向。

## Use Case

同时用多款语音输入法/剪辑工具、希望词库单一来源的个人用户。统一维护个人专有名词与术语，跨 App 同步。

## Deployment Geography

Global；运行于本地 agent runtime，读取用户本机词库文件与账号凭据。

## Requirements / Dependencies

- Python 3.9+（仅标准库）
- 用户授权访问其本机词库文件或账号凭据

## Known Risks and Mitigations

- 目标 App 词库格式未知 → 先探测再补映射，未确认前标注并拒绝写入。
- 覆盖目标 App 已有词条 → 默认只执行 add，conflict 与 app_only 需用户明确裁决。
- API 凭据泄露 → 凭据只在内存中用于只读请求，不持久化、不打印。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

JSON 规范词汇表、各 App 格式词库文件、同步差异计划（add/skip/conflict/app_only）。

## Skill Version

0.1.0

## Ethical Considerations

仅处理用户自己的词库与账号；不绕过授权、不批量抓取他人词条；凭据不落盘。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：真实 OpenLess 21 条词库跑完整 merge/validate/diff 流水线。

### Dimension Map

- correctness（去重与字段映射）：4 — 真实 21 条全部正确归类。
- effectiveness（跨 App 复用）：3 — OpenLess/Typeless 已适配，剪映待探测。
- efficiency（一次维护多处生效）：4 — 一次 merge 可 render 到任意已适配 App。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)：免费，通用个人生产力工具。

### Distribution

free：github、lovstudio；paid：无。
