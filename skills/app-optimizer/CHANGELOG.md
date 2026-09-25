# Changelog

## [0.2.1] - 2026-09-07

### Added

- 统一展示名为「应用性能医生」，保持调用 ID 与能力契约。

## 0.2.0

- 将核心能力从 Electron 专项提升为跨平台 `lov-app-optimizer`，覆盖 Electron、Tauri、原生桌面、iOS、Android、React Native、Flutter 与 Web/PWA。
- 将平台差异收敛到 host、runtime/framework 与 resource adapters；Yoda/Electron 保留为第一个完整案例，不把案例数字外推为通用结论。
- 证据契约升级为 `app-runtime-evidence/v1` / `app-runtime-report/v1`，兼容读取旧 Electron evidence，并加强 provenance、比较质量与 evidence gap 表达。
- 修正案例中推导、现场测量、正确性门与性能验收的边界，以及免费分发状态的表述。

## 0.1.0

- 创建三模块 Skill Kit：现场审计、回收工程、运行时验收。
- 加入只读证据报告脚本、fail-closed 回收判定和触发路由评测。
- 以 Yoda 的 PR 扇出、PTY/tmux、Agent session 与 worktree 治理作为首个真实案例。
