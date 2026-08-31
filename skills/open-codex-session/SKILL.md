---
name: lov-open-codex-session
description: >
  用 Codex thread UUID、deeplink 或已确认的检索命中，直接在 Codex 主窗口打开目标任务。适用于“打开这个 session”“打开刚找到的 Codex 会话”和 open this Codex session。
license: MIT
compatibility: "Codex desktop host with navigate_to_codex_page; Python 3.8+ for the shared Profile reader."
metadata:
  author: lovstudio-contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - codex
    - session-navigation
    - thread-id
    - desktop
---

# lov-open-codex-session — 打开指定 Codex 任务

把稳定的 Codex `sessionId` / `threadId` 交给宿主导航能力，让当前 Codex 主窗口切换到准确任务。Skill 只负责定位与打开，不修改任务内容、归档状态或 Git 状态。

## Triggers

### Activate when

- “打开这个 session”“打开刚才找到的微信读书投稿会话”“直接进入这个 Codex 任务”。
- 用户给出 Codex thread UUID 或 `codex://threads/<uuid>`，要求打开、跳转或导航。
- “Open this Codex session”, “navigate to that Codex thread”, “show the task we just found”.

### Do not activate when

- 用户要找出过去讨论某主题的会话，但尚未得到唯一候选 —— 先用 `lov-search-chat` 检索并回读原文。
- 用户要生成公开分享链接 —— 使用 `lov-share-session`。
- 用户要统计单个任务的 token —— 使用 `lov-codex-thread-usage`。
- 用户要新建、复制或分叉任务 —— 使用宿主对应的创建或 fork 能力。

## User Profile (cross-session)

`skill.yaml` 声明 `user-profile/v1`。每次运行开始时读取共享的 user、brand、workspace、preferences 与 `skills.lov-open-codex-session` 命名空间。当前请求中的 thread ID 永远优先，且 thread ID、标题和转录内容都不写入持久 Profile。

只有用户直接声明了需要跨会话保持的打开偏好时，才通过 `scripts/profile_store.py record --confirm` 写入 `records.*`，并报告保存路径。完整契约见 [`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

运行前读取 [`references/skill-composition.md`](references/skill-composition.md)。`lov-search-chat` 可以交付稳定 `sessionId`，但检索不是本 Skill 的隐藏依赖；已给出 UUID 或 deeplink 时必须直接导航。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve runtime context

1. 读取 `skill.yaml`、共享 Profile 和 `references/skill-composition.md`。
2. 确认当前宿主提供 `navigate_to_codex_page` 或语义等价的 Codex 任务导航工具。
3. 若宿主没有任务导航能力，明确报告缺失能力；不要用 `open`、浏览器 deeplink、AppleScript 或 Computer Use 冒充等价成功。

读取 Profile 的便携命令：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read \
  --skill-id lov-open-codex-session --pretty
```

### Step 1: Resolve exactly one target

按以下优先级取得目标：

1. 当前请求中的 thread UUID。
2. 当前请求中的 `codex://threads/<uuid>`，只提取 UUID 部分。
3. 当前对话里刚由检索或任务列表返回、且已经确认的唯一 `sessionId` / `threadId`。
4. 只有描述没有 ID 时，调用 `lov-search-chat` 或宿主任务列表定位候选；检索命中必须回读标题与原文，不能凭 snippet 判断。

接受标准 UUID；拒绝空值、截断值、路径、任意 URL 和多个未消歧候选。Ataru 的 Codex `sessionId` 可直接作为 Codex `threadId`。

### Step 2: Open the target

调用宿主任务导航能力：

```text
navigate_to_codex_page(threadId=sessionId)
```

不要先取消归档，不要创建新任务，不要向目标任务发送消息。打开归档任务不等于改变其归档状态。

### Step 3: Verify and report

1. 必须检查工具结果中的 `navigated` 为 `true`。
2. 若已知标题，回答“已打开《标题》”；否则回答“已打开目标 Codex 任务”，并带简短 ID 便于核对。
3. 工具失败时保留准确错误和目标 ID，不得报告“已打开”。
4. 若用户还要求继续、发送消息、取消归档或改名，这些是新的外部动作，交给对应宿主能力处理。

## Validation

- 激活句：“打开刚才找到的 Codex session。”
- Deeplink 激活句：“Open `codex://threads/00000000-0000-0000-0000-000000000000`. ”
- 非触发句：“把这个 session 生成公开分享链接。”
- 真实验收以宿主返回 `navigated: true` 为准；仅解析出 UUID 不算完成。

## Dependencies

- Codex desktop 宿主的任务导航能力。
- Python 3.8+，仅用于共享 Profile 读取与持久化。
- `lov-search-chat` 是没有明确 ID 时的可选上游，不是必需依赖。
