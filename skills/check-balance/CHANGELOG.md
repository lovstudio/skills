# Changelog

## 0.1.1

- 明确两层文案：frontmatter description 只服务 AI 路由，人看的 PR 文案改由 catalog tagline_zh / tagline_en 承载。
- 探测逻辑、输出 schema 与触发语均无改动。

## 0.1.0

- 初始本地 Skill 源码：六个只读 provider 探测（codex、claude、deepseek、openrouter、gateway、cc-switch）。
- 统一文本表与 JSON 输出，含状态、窗口用量、重置时间、余额与 alerts。
- `--watch` 二次采样估算消耗速率与可用天数，余额批量结算时回退到网关计价。
- 携带 user-profile 契约、Skill Card、用户案例与定价卡。
