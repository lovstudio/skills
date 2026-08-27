# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

| Skill | 路由契约 | 与本 Skill 的关系 |
| --- | --- | --- |
| `lov-search-chat` | 从 Ataru 索引召回过去的 AI 会话，返回 session/message 标识与原文片段 | 可选上游：提供更准的 session ID 或查询原话 |
| `lov-search-project` | 分层定位项目或源码目录 | 相邻但不组合：它的结果是目录，不是对话交付文件 |
| `lov-codex-thread-usage` | 读取 Codex 本地状态并统计 token/usage | 不组合：它不输出消息正文或交付文件路径 |
| `lov-finder-action` | 生成 Finder 右键菜单 | 不组合：它创建系统扩展，不负责定位文件 |
| `lov-share-session` | 把指定会话转换为可分享链接 | 不组合：它发布会话，不追踪本地制品 |

## Atomic Handoffs

- 可选上游 `lov-search-chat`
  - 输入制品：用户记得的主题或对话片段
  - 上游输出：`sessionId`、`messageId`、原文片段
  - 本 Skill 输入：`--session-id` 或更准确的查询短语
  - 验收边界：上游只证明是哪次对话；本 Skill 负责提取路径并验证文件仍存在
- 核心 `lov-search-file`
  - 输入：查询词、可选 session ID、transcript/file roots
  - 输出：按证据与耐久度排序的现存文件候选
- 下游：无。打开、复制、移动、上传或发布文件都需要用户另行请求。

## Overlap Decisions

- 不复用 `lov-search-project` 的目录结果冒充具体文件；只把 transcript 中的路径、
  session 生成缓存与 session 工作目录的 `output(s)` 作为会话关联证据。
- 不硬依赖 `lov-search-chat`：Ataru 未安装、索引未就绪或宿主没有对话工具时，仍可
  直接解析用户自己的本地 transcript。
- 文件内容搜索不是本 Skill 的主目标；显式 `--root` 只做文件名/父目录兜底。

## Composition Decision

**Single Skill**。用户可见结果只有一个：从过去的 AI 对话定位仍存在的本地文件。
transcript 预筛、消息解析、路径提取、session 派生与排序共用同一查询和证据模型，拆成
Kit 不会产生独立可验收制品。所有 sibling Skill 均为可选、制品级交接。
