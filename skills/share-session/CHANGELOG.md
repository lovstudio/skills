# Changelog

## [0.5.0] - 2026-09-12

### Added

- 导出 role=`tool` 块：Claude Code 的 `tool_use`/`tool_result` 与 Codex 的 `function_call`/`custom_tool_call` 及其输出都进入分享页，`verbose`（完整）档可回放命令行交互；shell 类工具渲染为 `$ cmd`，其余为 JSON，单块截断至 16 KB。
- Claude Code 的过程说明（签名带 `narration` 标记的 `thinking` 块）导出为助手 `commentary` 正文，`detailed` 档可见；签名为 `thinking` 的真实推理仍不导出。
- 助手正文按 `stop_reason` 标注 `agentPhase`（`final`/`commentary`），未收尾的轮次提升最后一条为 `final`，与站点 `concise`/`detailed`/`verbose` 分档语义对齐。

### Fixed

- 此前 Claude 模式分享在「完整」档与「详细」档内容相同、看不到任何工具调用；工具输出中的宿主注入残留改为丢弃该块而非中止上传。

## [0.4.2] - 2026-09-07

### Added

- 统一展示名为「会话分享」，保持调用 ID 与能力契约。

## [0.4.1] - 2026-09-01

### Added

- strip Codex host-injected context from user-role transcript blocks
- fail closed when known host-context markers remain before upload

## [0.4.0] - 2026-09-01

### Added

- support scoped standing consent for public session uploads
- skip redundant confirmation only when invocation, session, sanitized payload, destination, and exclusions match

## 0.3.0

- Add paid case Session uploads linked to a target Skill and stable case ID.
- Keep pricing server-authoritative at `ceil(target Skill Credits price / 10)`;
  reject client prices and paid attachments that could bypass access control.
- Return structured paid metadata for `lov-skill-add-case` composition.
- Redact private home prefixes, obvious access tokens, Authorization values, and
  private keys before upload.

## 0.2.0

- Support Codex Desktop `response_item.message` JSONL records and exclude
  developer messages, reasoning, tool calls, status events, and injected UI,
  environment, plugin, and Skill context from the public transcript.
- Resolve `CODEX_SESSION_ID` / `CODEX_THREAD_ID` and merge multiple rollout
  segments belonging to the same logical session in chronological order.
- Recover once from an expired cached access token by refreshing local auth and
  retrying the upload; fall back to device flow only when refresh is unavailable.
- Add focused tests for Codex normalization, multi-segment resolution, metadata
  removal, and 401 refresh retry.

## 0.1.0

- Initial local Skill source.
