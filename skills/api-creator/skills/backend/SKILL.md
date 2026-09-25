---
name: lov-backend
description: >
  在 uni-api（FastAPI 聚合网关）项目内为某个 app 新增网关能力：新建业务 package 与 router，
  注册进 router/__init__.py 并接入 config/app_groups.py 分组，让该 app 通过网关调用聚合 API。
  触发：给 uni-api 加网关能力 / add gateway endpoints in uni-api。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - uni-api
    - fastapi
    - gateway
  compatibility: "Portable Agent Skills format. 需要在 uni-api（FastAPI）仓库根目录内执行；启动前提见仓库 AGENTS.md。"
  dependencies: []
---

# 网关后端 · Gateway Backend

在 uni-api（FastAPI 聚合网关）仓库里为该 app 新增一组网关端点并挂进 `/docs` 分组，让该 app
通过网关调用聚合后的上游 API。改动只落在 uni-api 既有约定内，不引入新框架。

## Triggers

### Activate when

- “给 uni-api 加一个 app 的网关能力 / 聚合接口”。
- “后端需要为 <app> 暴露一组 API”。
- "add gateway endpoints in uni-api for my app".
- "expose aggregated APIs for my app through the uni-api gateway".

### Do not activate when

- 只需加单个第三方 AI 代理（如 Gemini 生图）：交给 `lov-install-zenmux-api`。
- 重构已有后端冗余 API：交给 `lov-refactor-api`。
- 前端调用层封装：由本 Kit 的 `lov-frontend` 模块处理。

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

- Use `SKILL_DIR` if the environment provides it；否则从当前上下文推断已安装的模块目录。
- 确认工作目录在 uni-api 仓库根目录（有 `main.py`、`router/`、`packages/`、`settings.py`）。
- 确认仓库根目录 `AGENTS.md` 的运行前提（`.env` 必填字段、`socksio` 等）已满足，避免破坏 app 启动。
- 读取 `references/uni-api-patterns.md` 掌握 uni-api 既有约定后再动手。

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 确认 **app 名称** 与 **需要网关化的上游能力**（例如：新增某类 LLM 供应商聚合、某业务数据接口、
  OSS/媒体代理等）。
- 复用 uni-api 已有的 `packages/llm`、`packages/spider` 等能力，避免重复造轮子。
- 分离内部上下文与用户可见输出：最终交付的是**网关端点清单**（method + path + 说明），
  不是内部实现笔记。

### Step 1.5: Analyze nearby Skills before implementation

- 确认本次不依赖 `lov-install-zenmux-api`（不同网关槽位）与 `lov-refactor-api`（下游可选重构），
  记录见 `references/skill-composition.md`。

### Step 2: Execute the workflow

1. **业务逻辑**：按能力归属放入 `packages/<domain>/`（新能力则新建目录）。复用已有
   `packages/llm`、`packages/spider` 等模块，保持依赖最小化。
2. **网关端点**：新建 `router/<capability>.py`（复杂能力用 `router/<capability>/` 包）：
   - `APIRouter(prefix='/<capability>', tags=['<Tag>'])`，tag 名用英文驼峰/短横线，与 app 分组对应。
   - 请求/响应体使用 `packages/common.pydantic` 的 `BaseModel`，字段尽量少。
   - 用 `@standard_error_handler()` 装饰路由，保证错误结构统一（见 `packages/fastapi/standard_error.py`）。
   - 参考既有 `router/llm.py`、`router/account.py` 的写法保持一致。
3. **注册**：在 `router/__init__.py` 里 import 并 `root_router.include_router(...)`。
4. **/docs 分组**：把该 app 的 tag 加入 `config/app_groups.py` 的 `APP_GROUPS`（新增分组或并入现有组）。
   分组名即 `/docs` Tab 名，用简洁中文。
5. **env（按需）**：新增上游密钥或配置时，在 `settings.py` 的 `Settings` 加字段，并在 `.env.sample`
   补充占位，不硬编码密钥到源码。
6. **本地验证**：
   - `python -c "import main"` 通过（先满足 AGENTS.md 前提）；
   - `openapi.json` 出现新 tag；
   - 启动后 `/docs` 出现对应 Tab。

### Step 3: Validate the deliverable

- 检查 `router/__init__.py` 注册完整、`config/app_groups.py` 分组正确、无硬编码密钥。
- 汇报**网关端点清单**（表格：method / path / 说明），这是交给 frontend 模块的契约。
- Report concrete files or results, plus any remaining evidence gaps.

## Dependencies

- uni-api（FastAPI）仓库；python3 + 项目 poetry 环境。
- `.env`（含 AGENTS.md 列出的必填变量）与 `socksio` 等运行前提。
- 无第三方外部服务依赖。
