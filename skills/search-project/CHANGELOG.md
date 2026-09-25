# Changelog

## [0.2.1] - 2026-09-07

### Added

- 统一展示名为「项目寻踪」，保持调用 ID 与能力契约。

## 0.2.0

- 将用户可见 Skill 名从 `lov-find-project` 统一为 `lov-search-project`。
- 迁移本地真源目录、Profile namespace、相邻 Skill 引用与安装入口。

## 0.1.0

- Initial local Skill source.
- 分层搜索 CLI `scripts/find_project.py`：roots → cwd → chat → full 四层递进，
  auto 模式命中即停；按匹配分数排序、排除隐藏/构建目录、聊天记录提取路径证据。
- `user-profile/v1` 契约：`workspace.projects` 追加为搜索根，`profile_store.py`
  写入长期偏好。
- 证据包：skill-card / cases（真实 claude-code 泄露源码定位案例）/ pricing。
