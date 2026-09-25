# Changelog

## [0.1.1] - 2026-09-07

### Added

- 统一展示名为「网页截图导出」，保持调用 ID 与能力契约。

## 0.1.0

- 新增 `scripts/integrate_screenshot.py`：`integrate` / `verify` / `self-test` 三个子命令，无第三方依赖。
- 内联 `assets/modern-screenshot.js` v4.5.1（MIT），自包含离线可用。
- 注入契约：`#capture` 容器 + 浮动导出按钮 + `domToPng` 显式 width/height/scale + 可复制错误提示。
- 补齐 `references/integration-contract.md` 与 `references/acceptance-checklist.md`。
- 首个真实案例：给《手工川 DSH 剪辑成本审计》HTML 加一键导出 PNG，端到端验证通过。
