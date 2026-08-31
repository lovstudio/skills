# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Relation |
| --- | --- | --- |
| `lov-search-chat` | 从 Ataru 记忆索引检索历史 AI 会话，返回稳定 `projectId` / `sessionId` / `messageId` 并回读原文 | optional upstream atom |
| `lov-share-session` | 把转录脱敏、上传并返回公开或付费分享 URL | not composed |
| `lov-codex-thread-usage` | 从 thread UUID 或 deeplink 读取本地状态并统计 token usage | not composed |
| Codex `navigate_to_codex_page` | 接受 `threadId`，让当前主窗口进入该任务 | required host capability, core execution primitive |

## Atomic Handoffs

- **Upstream — `lov-search-chat`**
  - 输入：用户对历史会话的主题描述。
  - 输出制品：经原文回读确认的唯一 Codex `sessionId` 与标题。
  - 交接边界：`lov-search-chat` 对“找对会话”负责；本 Skill 对“打开并得到 `navigated: true`”负责。
- **Core — `lov-open-codex-session`**
  - 输入：thread UUID、Codex deeplink，或上游确认的 `sessionId`。
  - 输出制品：宿主导航结果及简短确认。
  - 验收边界：只有 `navigated: true` 才算完成。
- **Downstream**：无固定下游。继续任务、发消息、改名、取消归档和分享都由各自宿主能力或 Skill 单独处理。

## Overlap Decisions

`lov-search-chat` 不打开任务；`lov-share-session` 打开的是公网分享页；`lov-codex-thread-usage` 明确把导航排除在范围外。三者都不拥有 Codex 主窗口导航结果，因此无需扩展或合并。宿主导航工具是执行原语，不是另一个可分发 Skill。

## Composition Decision

Single Skill。用户可见结果只有“打开一个准确的 Codex 任务”。检索是可选上游，分享与统计是独立结果；把它们嵌入 Kit 会扩大范围并制造不必要耦合。
