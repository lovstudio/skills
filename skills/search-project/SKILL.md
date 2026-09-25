---
name: lov-search-project
description: >
  分层定位本机项目/源码目录：项目根优先，其次当前文件夹、AI 聊天记录，最后全盘
  兜底，返回候选路径与证据。Use when locating a project on this machine:
  "找到 xxx 项目"、"这个项目在哪"、"where is the X project"、"find the source for X".
license: MIT
metadata:
  author: lovstudio
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - search
    - project
    - locator
    - filesystem
  compatibility: "Portable Agent Skills format. Requires Python 3.8+, ripgrep recommended, Spotlight (mdfind) on macOS."
  dependencies: []
---

# 项目寻踪 · Project Finder

用户给出项目名、关键词或特征描述，Skill 在四层递进范围中定位候选目录，
每一层都标注命中来源与证据，供用户确认或继续深入。全程不修改任何文件。

## Triggers

### Activate when

- 帮我找一下 xxx 项目 / 项目在哪个目录
- 这个项目（源码）在哪 / 本机有没有 xxx 的源码
- 找 xxx 的仓库、文件夹、workspace
- "where is the X project", "find the source/folder for X", "locate X on disk"

### Do not activate when

- 搜索知识库/记忆/会话内容 → `lov-memory-search` / `lov-search-chat`
- 生成 Finder 右键菜单 → `lov-finder-action`
- 查找品牌 Logo 资产 → `lov-find-logo`
- 搜索网页或远程仓库 → 交给对应网络搜索能力

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

`workspace.projects`（项目根目录列表）会追加到 CLI 的默认搜索根中，无需
硬编码路径。当用户直接说出「我常把项目放在 /xxx」这类长期事实，通过
`scripts/profile_store.py` 写入 `workspace.projects` 并报告保存路径。

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
- Verify every required local module, reference, script, and asset before work:
  - `scripts/find_project.py`（分层搜索 CLI，必需）
  - `scripts/profile_store.py`（Profile 读写，必需）
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-search-project"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 提取查询词：项目名、别名、关键词，或用户给的特征描述（如「claude code
  泄露源码」→ 关键词 `claude code`）。
- 明确目标：是要定位目录路径，还是顺带查看目录内容、打开 Finder。
- 若用户没有给可搜索的实质信息（例如只问「能找到我的项目吗」），先用一
  个问题澄清想找什么，再继续。

### Step 1.5: Analyze nearby Skills before implementation

- 已在本 Skill 的 `references/skill-composition.md` 记录：与本 Skill 相邻的
  `lov-find-logo`、`lov-memory-search`、`lov-search-chat`、`lov-finder-action`
  均为不同能力，无重叠；`lov-repo-takeover` 是其下游可选交接（拿到路径后可
  让用户决定是否接手仓库）。本 Skill 是 Single Skill，无需 Kit。
- 只在用户明确要求时提及下游 Skill，不要自动调用。

### Step 2: Execute the workflow

1. **运行分层搜索 CLI**（默认 `--scope auto`，roots 命中即停）：

```bash
python3 "$SKILL_DIR/scripts/find_project.py" "<查询词>" --json
```

2. **按命中层解读结果**（结果 JSON 中每条 `hits[]` 有 `layer` / `path` /
   `score` / `evidence`）：
   - `roots`：项目根目录集合内的直接子目录（最可靠）
   - `cwd`：当前目录向下 4 层内的名字匹配
   - `chat`：AI 聊天记录中提及过的路径（`evidence` 标注提及来源文件）
   - `full`：Spotlight/全盘慢扫（噪声大，需要人工甄别）

3. **缩小范围或扩大范围**：
   - roots 层有结果但用户想找的不在其中 → 提示可运行
     `--scope chat`（从聊天记录找）或 `--scope full`（全盘兜底）。
   - 结果过多 → 建议更精确的关键词，或让用户确认是哪个项目。
   - 结果为空 → 先试 `--scope full`，仍未命中则如实说「本机未找到」，不要
     编造路径。

4. **给出结论**：列出 top 候选（默认 10 条内），每条标注命中层与证据。若
   唯一性高（score 显著领先且语义吻合），明确指出推荐路径；否则请用户挑选。

5. **可选后续**：用户需要时，用打开的路径继续（查看结构、打开 Finder、
   或询问是否需要 `lov-repo-takeover` 处理仓库）。

### Step 3: Validate the deliverable

- 确认给出的路径真实存在、命名吻合（可 `ls` 验证）。
- 诚实标注不确定性：`full` 层命中即使路径存在也可能是同名无关目录。
- 不编造路径、不猜测不存在的目录。
- 若用户直接表达了长期偏好（如「项目都在 /xxx」），已通过
  `profile_store.py` 写入并报告保存路径。
- 本次真实案例（Input → Prompt → Output）记录在 `cases/cases.json`。

## Dependencies

- Python 3.8+（运行时）
- ripgrep（可选，聊天记录层加速；缺失时自动回退 grep）
- macOS Spotlight `mdfind`（可选，full 层使用；缺失时回退 find）
- 无第三方 Python 包
