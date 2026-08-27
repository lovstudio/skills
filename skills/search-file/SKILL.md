---
name: lov-search-file
description: >
  从本机 Codex、Claude 等 AI 对话记录中追溯图片、文档与其他交付文件，返回仍然
  存在的候选路径、会话证据与存储层级。适用于“上次 AI 给我的文件在哪”或
  “find the file from an earlier AI chat”。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - search
    - file
    - conversation
    - local-first
  compatibility: "Portable Agent Skills format. Requires Python 3.9+; ripgrep is recommended for fast transcript prefiltering."
  dependencies: []
---

# lov-search-file — 从 AI 对话追到本地文件

把用户记得的对话主题、片段或 session ID 还原为可验证的本地文件候选。结果会区分
项目归档、下载目录、AI 生成缓存与临时目录，优先返回仍然存在且更耐久的副本。

## Triggers

### Activate when

- “找一下之前 Codex 给我 P 头像的图片存储位置。”
- “上次 AI 生成的 PDF / PPT / 压缩包在哪？”
- “从那次对话里把最终交付文件找出来。”
- “Find the image/file from an earlier Codex, ChatGPT, or Claude conversation.”

### Do not activate when

- 只想回忆之前讨论或决定了什么，不需要文件路径 → `lov-search-chat`
- 只想定位一个源码仓库或项目目录 → `lov-search-project`
- 已知当前目录和文件名，只需普通源码搜索 → `rg` / `find`
- 文件只存在于网盘或远端聊天附件，本机无副本 → 使用对应连接器或云端搜索

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work.
- 必须确认 `scripts/find_ai_file.py`、`scripts/profile_store.py`、
  `references/skill-composition.md` 均存在。
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-search-file"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 提取用户仍记得的线索：对话主题或原话、AI 产品、文件类型、大致日期、项目名、
  文件名片段与 session ID。现有线索足够时直接搜索，不先追问。
- 区分用户要找的是 AI 的最终输出、原始输入附件，还是所有相关副本；默认最终输出
  优先，但保留原始输入作为低分候选。
- 自动从查询推断 `image`、`document`、`audio`、`video`、`archive` 等类型；用户已
  明确类型时以当前请求为准。

### Step 1.5: Analyze nearby Skills before implementation

- 先读 `references/skill-composition.md`。`lov-search-chat` 可以提供 session ID、
  message ID 或原文片段作为可选上游，但不是运行时依赖。
- `lov-search-project` 返回项目目录，不返回项目里的具体对话交付文件；不要把两个
  Skill 合并，也不要用项目名命中冒充文件证据。

### Step 2: Execute the workflow

1. 若宿主提供任务/对话搜索能力，先只读查询匹配的历史任务，取得更准确的标题、
   session ID 或原话；ChatGPT 桌面端的加密数据不可由本地脚本直接解密。没有该能力
   时直接进入本地 transcript 搜索，不把连接器当硬依赖。

2. 运行确定性 CLI。默认自动推断文件类型，并输出 JSON 供 Agent 排序解读：

```bash
python3 "$SKILL_DIR/scripts/find_ai_file.py" "<记得的对话或文件线索>" --json
```

3. 已知 session ID 时强约束搜索；用户还给了自定义对话目录或文件根时重复传参：

```bash
python3 "$SKILL_DIR/scripts/find_ai_file.py" "<线索>" \
  --session-id '<session-uuid>' \
  --transcript-root '<transcript-root>' \
  --root '<file-root>' --json
```

4. CLI 先用 ripgrep 预筛 transcript，再只解析用户/助手消息及工具调用里的本地路径；
   它不会把 developer/system 文本当成会话证据。命中的 session 会继续关联
   `$CODEX_HOME/generated_images/<session-id>` 与该 session 工作目录的 `output/`、
   `outputs/`。增量索引存于用户缓存目录，权限为 `0600`；传 `--no-cache` 可禁用。

5. 按 `exists`、`score` 与 `durability` 解释结果：
   - `project-output` / `documents`：优先作为长期副本；
   - `downloads`：用户可直接访问的交付副本；
   - `ai-cache`：可追溯生成来源，但不视作唯一长期归档；
   - `temporary`：可能随时消失，不能作为唯一结论。

6. 结果为空时，用同义词或更准确的原话重试；需要查看已在对话中提及但已删除的
   路径时加 `--include-missing`。仍为空就明确说未找到，不编造路径。

### Step 3: Validate the deliverable

- 对最终候选再次 `stat`，确认文件在本轮仍存在，并报告大小、修改时间与证据 session。
- 至少给出一个推荐路径；同一制品有多个副本时按耐久度说明主副本与缓存副本。
- 不移动、复制、删除或上传任何命中文件，除非用户另行明确要求。
- 运行 `python3 scripts/validate_skill.py .` 与聚焦回归测试，验证可信度卡、真实案例
  和本地安装链。

## Dependencies

- Python 3.9+（仅标准库）
- ripgrep（推荐，用于快速预筛；缺失时回退到受上限保护的 transcript 扫描）
- 不需要网络、凭据或第三方 Python 包
