---
name: lov-share-session
description: >
  把 Agent 会话转成免费公开或按 Credits 解锁的 LovStudio 在线页。Use when the user
  asks to share a session, publish a transcript, or attach paid evidence to a Skill case.
license: MIT
compatibility: "Python 3.10+. Reads JSONL/JSON/Markdown transcripts and needs LovStudio authentication for upload."
depends_on:
  - lov-branding-consistency
metadata:
  author: skill-publisher
  version: "0.5.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - session-share
    - transcript
    - publish
---

# 会话分享 · Session Sharing

把一个 Agent 会话的完整对话记录，转成一个可直接打开、可在微信/Twitter/邮件里分发的
LovStudio 分享页 URL。默认是免费公开页；被 `lov-skill-add-case` 组合调用时，可生成
按 Credits 解锁的案例 Session。Skill 只处理「读取转录 → 脱敏归一化 → 上传 → 返回链接」，
不修改原会话。

## Triggers

### Activate when

- 用户说「把这个 session 分享出去」、「生成分享链接」、「给我一个可公开访问的会话页面」。
- 用户给了一个 transcript / session 文件，希望转成一条可分享的 Lovstudio 在线链接。
- "Share this session", "make a public link for this conversation", "publish this transcript to Lovstudio", "generate a shareable page".
- 用户在 Yoda 里对一个当前运行的会话点了「生成公开分享链接」。
- `lov-skill-add-case` 需要把已验收案例的完整对话作为付费证据上传。

### Do not activate when

- 用户只是要导出会话文本到本地 Markdown/PDF —— 用 `lov-rich-export` 或 `lov-any2pdf`。
- 用户要把会话上传/发布到 GitHub、博客或别的公开平台 —— 不在本 Skill 范围。
- 用户没有指定会话，也不想读取当前会话（此时应询问来源，而不是凭猜测抓一个会话）。

## 输入（会话来源，按优先级）

脚本按以下顺序解析会话来源，前一个命中即用：

1. `--file <path>`：显式的 transcript / JSONL / JSON / markdown 文件。
2. `--session-id <uuid>`：显式指定会话 id，脚本去 `$HOME/.claude/projects/<cwd-slug>/{id}.jsonl` 读取。
3. 自动探测：`CLAUDE_CODE_SESSION_ID` 环境变量。
4. 自动探测：`CODEX_SESSION_ID` / `CODEX_THREAD_ID`，并按同一 session id 合并
   `$CODEX_HOME/sessions/` 下因压缩或恢复产生的多个 rollout 分段。
5. 自动探测：`YODA_PTY_ID`（去掉 `claude-conv-` 前缀后当会话 id）。
6. 兜底：当前工作目录所属的 `$HOME/.claude/projects/<cwd-slug>/` 下最新的 `*.jsonl`。

## User Profile (cross-session)

本 Skill 连接 `user-profile/v1`：每次运行开头读取共享 user / brand / workspace /
preferences 与 `skills.lov-share-session` 命名空间。用户直接说出的、值得跨会话复用的
偏好（如默认显示档、默认 base url）通过 `scripts/profile_store.py record --confirm`
写回 profile 并报告保存路径；**凭据（access/refresh token）绝不写入 durable records**
，只存到本机 gitignore 文件。详见 `references/user-profile.md`。

## Skill Group Composition

读 `references/skill-composition.md` 判断是否要交接给相邻 Skill。`lov-skill-add-case`
是已声明的下游调用方：它提供目标 Skill ID 与 case ID，本 Skill 返回服务端权威价格和 URL。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- 用 `SKILL_DIR`（或从当前 skill 上下文推断安装目录）。
- 确认 `scripts/share_session.py` 存在；运行前检查 `python3` 可用。
- 若用户显式给了会话来源就走注入路径，否则走自动探测。

### Step 1: Understand the requested outcome

- 明确用户要的是「一条可公开访问的 Lovstudio 链接」，不是本地文件。
- 记录会话来自哪里（自动探测命中还是显式文件），以及用户是否需要指定显示档（hit hidden / concise / detailed / verbose，默认 `concise`）。
- 若调用方给出 `--paid-skill`，必须同时给出 `--case-id`。付费价格不能由客户端传入；
  服务端读取目标 Skill 当前售价并计算 `ceil(price / 10)`，最低 1 Credit。
- 上传前自动把用户主目录替换为 `$HOME`，移除明显 token、Authorization 与私钥，并剥离
  即使被宿主折叠进 `role=user` 消息的 AGENTS、环境、Skill、权限、Plugin 等注入上下文。
- 解析当前授权：当前请求的明确同意优先；否则读取
  `skills.lov-share-session.records.standing_public_upload_consent`。它只有在用户主动调用本 Skill、
  目标是当次当前会话或显式指定会话、目的地是 `https://lovstudio.ai`、正文已脱敏且无附件时生效。
  匹配时不重复确认；不匹配时仍按高影响操作询问一次。
- 工具块（命令、脚本、文件内容、命令输出）不在 `payload=sanitized-visible-user-assistant-messages`
  的站立授权范围内。含工具块的上传需当次确认，并先用 `--dry-run` 列出敏感候选（付费 Skill
  解密正文、个人档案、内部规范、Profile 转储），用 `--exclude-tool-pattern` 排除后再上传。

用户说“以后/默认同意”时，可把上述边界作为站立授权写回 Profile。它授权的是**触发后的当次上传**，
不是后台扫描或自动公开其他会话；不包含其他站点、附件、付费 Session、账号选择或发布后的再分发。
用户说“以后都问我”“取消默认分享”时删除或停用该记录。

### Step 2: Execute the workflow

运行转换脚本（自动含归一化 + 上传）：

```bash
export SKILL_DIR="/path/to/lov-share-session"
python3 "$SKILL_DIR/scripts/share_session.py" \
  [--file "<transcript 路径>"] \
  [--session-id "<uuid>"] \
  [--detail concise] \
  [--base-url "https://lovstudio.ai"] \
  [--token "<access token>"] \
  [--profile-path "<profile.json 路径>"] \
  [--exclude-tool-pattern "<正则，可重复>"]
```

`--exclude-tool-pattern` 丢弃内容匹配的工具块（多行、忽略大小写），用于合法但不能公开的
转录内容：解密后的付费 Skill 正文、私人档案、内部规范。它不作用于用户与助手正文。

案例付费 Session 的确定性调用：

```bash
python3 "$SKILL_DIR/scripts/share_session.py" \
  [--file "<transcript 路径>" | --session-id "<session id>"] \
  --paid-skill "lov-target-skill" \
  --case-id "stable-case-id" \
  --detail concise \
  --json
```

付费模式不接受附件：当前附件桶使用公开 URL，允许附件会绕过购买校验。正文 snapshot
只在页面确认当前用户是上传者或已购买者后读取。

脚本会依次：读取并归一化转录为合法 `yodaSessionShareUpload` 结构 → 取 Lovstudio
access token（本轮请求 > 环境/本地凭据文件 > refresh token > device-flow）→
`POST /api/yoda/session-shares` → 打印分享 URL。

Claude Code 与 Codex JSONL 都会导出三类块：用户与助手可见正文、`role=tool` 的工具调用
（shell 命令渲染为 `$ cmd`，其余为 JSON）与工具输出（单块截断 16 KB）。Claude Code 的过程说明存放在签名带 `narration`
标记的 `thinking` 块里，按签名区分后导出为 `commentary`；开发者消息、
真实推理（签名为 `thinking`）、状态事件和自动注入的 AGENTS/浏览器/环境/Skill/权限/Plugin 上下文不进入
公开主体。助手正文按 `stop_reason` 标注 `agentPhase`：站点 `concise` 只显示 `final`
回复，`detailed` 加上过程说明，`verbose` 加上工具块。若用户或助手正文里发现无法完整
剥离的已知宿主上下文标记，脚本在上传前失败并阻止公开；工具块出现残留则只丢弃该块。
若缓存 access token 返回 401，脚本用 refresh token 更新后只重试一次；显式传入的
无效 token 不会被静默替换。

第一次运行时若没有可用 token，脚本会走 device-flow：打印一个
`verificationUri`，让用户浏览器打开并同意，然后轮询直到登录成功，拿到并本地缓存
refresh token（后续运行自动复用）。

`--detail <hidden|concise|detailed|verbose>` 会把对应显示档烘焙进最终 URL 的
`?detail=` 参数，让打开分享页的人默认看到该深度。

### Step 3: Validate the deliverable

- 脚本返回的 URL 必须能打开且显示会话内容（用 `ego-browser` 或让用户回读确认）。
- 付费模式的 JSON 结果必须含 `access=paid`、`targetSkill`、`caseId`、
  `priceCredits > 0` 与 `pricingRule=ceil(target-skill-price/10)`；这些字段必须来自服务端响应。
- 若上传被拒（`.strict()` schema），确认归一化结构无误后再重试，不要凭猜测改服务器。
- 上传前的 dry-run 必须确认用户正文仍在，且 AGENTS、环境、Skill、权限和 Plugin
  等宿主注入结构均为零；清洗器报告残留时不得绕过。
- 每次成功后把 URL（与可选的显示档说明）给用户；若用户长期偏好该显示档，用
  `profile_store.py record` 落库并报告保存路径。

## 实测约定

- 清洗器原先只认 Codex 的 XML 标签注入，Claude Code 的 skill 正文是无标签纯文本，会整段泄露（2026-09-06）
- dry-run 必须按 `blocks[].role` 逐块查，只用整体正则会漏掉折进 role=user 的注入（2026-09-06）
- 校验清单：`Base directory for this skill` / `task-notification` / `command-message` / `system-reminder` 四项须为 0（2026-09-06）
- 助手正文里引用注入标记会被计为命中，需人工区分是正文还是残留后再放行（2026-09-06）

- Claude Code 桌面端显示的中间进度说明不是 `text` 而是签名 protobuf 含 `narration` 的 `thinking` 块，真实推理块签名含 `thinking` 且正文为空；按签名区分导出，不能按“非空即导出”（2026-09-12）
- Claude 模式此前只导出 user/assistant 正文，「完整」档等于「详细」档、看不到任何工具调用；工具块需与 Yoda 桌面端一致导出 role=tool 并标注 agentPhase，分档才生效（2026-09-12）

## Dependencies

- Python 3.10+（标准库：`json`, `urllib.request`, `argparse`, `pathlib`, `re`, `os`）。
- 运行时可选的 `yaml` 仅在 `validate_skill.py` 校验 SKILL 源时需要，CLI 本身不需要。
- 无外部 npm / pip 包。
