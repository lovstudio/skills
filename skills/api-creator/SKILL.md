---
name: lov-api-creator
description: >
  当开发某个 app 需要 API 网关能力时，在 uni-api（FastAPI 聚合网关）后端新增该 app 的网关
  端点与分组，并在 uni-app 前端封装统一调用层。触发：集成网关到 uni-app / integrate an API
  gateway into my uni-app project。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - api-gateway
    - uni-api
    - fastapi
    - uni-app
  compatibility: "Portable Agent Skills format. 需要可访问的 uni-api（FastAPI）后端仓库与 uni-app（DCloud）前端仓库。"
  dependencies: []
---

# 网关工坊 · Gateway Studio

开发某个 app 需要 API 网关能力时，本 Skill 在 uni-api（FastAPI 聚合网关）后端为该 app 创建网关
端点与 `/docs` 分组，并在对应 uni-app 前端项目封装统一调用层，让 app 通过网关访问聚合后的 API。

## Triggers

### Activate when

- 开发某个 app 时需要 API 网关能力，要求集成进 uni-api（FastAPI 聚合网关）后端。
- “帮我把网关能力集成到 uni-app 项目里”。
- “给 <app> 加后端聚合接口 / 网关端点”。
- "integrate an API gateway into my uni-app project".
- "create backend gateway endpoints for my app".

### Do not activate when

- 只需为项目加单个第三方 AI 代理（如 Gemini 生图代理）：交给 `lov-install-zenmux-api`。
- 重构已有后端里冗余的 API：交给 `lov-refactor-api`。
- 只是把现成网关或服务部署上线：交给 `lov-deploy-to-vercel`。
- 生成独立 App 工程或落地页：交给 `lov-app-generator` / `lov-oh-my-landingpage`。

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

## Skill Kit Modules

This repository is a self-contained Skill Kit. At Step 0, load and verify:

- `$SKILL_DIR/skills/backend/SKILL.md` — `lov-backend`
- `$SKILL_DIR/skills/frontend/SKILL.md` — `lov-frontend`

`kit.yaml` is the machine-readable module and pipeline manifest. Every module
listed there must ship inside this repository.

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
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-api-creator"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- Separate internal context from user-visible output.
- Confirm the input, intended audience, expected deliverable, and evidence gaps.
- 确认三项输入：**app 名称**、**需要网关化的上游能力**（LLM 聚合 / 代理 / 业务 API）、
  **前端项目路径**（DCloud uni-app，含 `pages.json` 与 `manifest.json`）。
- Record one real user case before calling the Skill complete. The case must show
  the input, the prompt or minimum brief, and the output; do not invent results.

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.

### Step 2: Execute the workflow

按 `kit.yaml` 的流水线执行。默认跑 `full`（backend → frontend）；用户只要求一端时只跑对应模块。

- **backend**（`$SKILL_DIR/skills/backend/SKILL.md`）：在 uni-api 后端为该 app 创建网关能力
  —— 业务 `packages/<domain>/` + `router/<capability>.py` + 注册进 `router/__init__.py`
  + 把 tag 分组加入 `config/app_groups.py` + 必要 env。产物是**网关端点清单**。
- **frontend**（`$SKILL_DIR/skills/frontend/SKILL.md`）：在 uni-app 前端封装网关调用层
  —— 统一 `request` 封装（baseURL / token / 错误处理）+ 按端点清单生成的模块化 API 文件。
  产物是可用的 `api/` 模块与用法示例。

两模块通过「网关 baseURL + 端点清单」契约交接：backend 的端点表是 frontend 的输入。

### Step 3: Validate the deliverable

- 后端：`python -c "import main"` 通过（先按 uni-api 的 AGENTS.md 备好 `.env` 与 `socksio`），
  `/openapi` 出现新 tag，`/docs` 新 Tab 生效。
- 前端：request 封装可被页面 `import` 后正常调用，错误提示可复制并携带上下文。
- Report concrete files or results, plus any remaining evidence gaps.
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as the
  standard trust bundle for this Skill.

## Dependencies

- 后端：可访问的 uni-api（FastAPI）仓库；`python3` 与项目 poetry 环境；`.env` 与 `socksio` 等
  运行前提见 uni-api 仓库根目录 `AGENTS.md`。
- 前端：DCloud uni-app 项目（HBuilderX 或 CLI 工程均可）。
- 无第三方外部服务依赖。
