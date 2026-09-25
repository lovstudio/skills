# Changelog

## 0.1.0 — 2026-09-12

- 初始版本：只读诊断器 `scripts/codex_provider_doctor.py`，对比 `config.toml` 已定义
  provider、`state_5.sqlite` 持久化 provider、桌面 App 与核心日志中的
  `Model provider ... not found` 证据，并抽样核对 rollout session_meta。
- 两个写入模式：`--fix-retag` 重打历史 provider 标签，`--restore` 回滚；都先备份
  （索引库完整副本 + 被改写 rollout 的首行原文），都必须显式 `--yes`。
- 三份 reference：机制与真实证据、修复手册（补定义 / 重打标签 / 回滚 / 验证）、
  相邻 Skill 边界。
- 可信度包：Skill Card（三维度地图与分发状态）、真实用户案例、免费定价卡。
- 本机验证：7 个端到端单元测试通过；对真实 `state_5.sqlite` 冷副本执行重打标签与
  回滚成功；真实目录未被写入。
- 2026-09-12 实机修复：为 `yoda` 补定义后，官方 app-server `thread/resume` 从
  `-32600 Model provider not found` 变为成功返回目标 thread。
