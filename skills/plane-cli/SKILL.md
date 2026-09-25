---
name: lov-plane-cli
description: >
  用命令行读写 Plane 项目管理实例：查项目、工作项、周期、模块、状态、标签，创建和更新工作项与评论。
  适用于“看看 Plane 上有哪些任务”“在 Plane 建个工作项”“同步 Plane 进度”。
  Use when reading or writing a self-hosted or cloud Plane instance through its REST API v1.
license: MIT
compatibility: >
  Portable Agent Skills format. Requires Node.js 20+.
  Needs a reachable Plane instance and an API token; defaults to a local self-hosted instance at http://localhost.
metadata:
  author: LovStudio
  version: "0.1.0"
  tags:
    - project-management
    - plane
    - api-client
---

# Plane 助手 · Plane Assistant

通过 Plane REST API v1 读写 Plane 实例。命令表由随包的 `cli/openapi.json` 在启动时构建，覆盖 **130 个操作 / 17 个资源分组**，与实例导出的 schema 严格一致。

## Triggers

### Activate when

- “Plane 上有哪些项目 / 任务？”
- “在 Plane 里建一个工作项。”
- “把这个任务同步到 Plane。”
- “看下 Plane 某个项目的进度 / 周期 / 模块。”
- “List my Plane work items.”

### Do not activate when

- 部署、启动或排障 Plane 实例本身（容器、compose、迁移）——那是运维任务，不走本 Skill。
- 目标是 Jira、Linear、Notion 等其他项目管理工具。
- 用户没有该实例的访问权，或要求绕过认证。

## Step 0: 解析运行时

1. `node --version` 确认 Node.js 20+。
2. CLI 入口：`$SKILL_DIR/cli/bin/lov-plane-cli.mjs`。若已 `npm link`，可直接用 `lov-plane-cli`。
3. 缺 Node 或缺 `cli/openapi.json` 时报出相对路径并停止，不要凭记忆拼 URL 调用 API。

## Step 1: 确认实例与凭据

实例地址按此顺序解析：`--base-url` → `$PLANE_BASE_URL` → `~/.config/lov-plane-cli/config.json` 的 `baseUrl` → `http://localhost`。

凭据同理：`--api-key` → `$PLANE_API_KEY` → 配置文件 `apiKey`。

```bash
export PLANE_BASE_URL=http://localhost
export PLANE_API_KEY=<api token>
```

获取 token：登录 Plane → 右上角头像 → Settings → API tokens → Add API token。

**凭据只经环境变量或用户自有配置文件传入。** 不要把 token 写进生成文件、示例、日志或 Profile 记录，也不要在回复里回显完整 token。

缺凭据时 CLI 以退出码 2 停止并打印获取指引——把该指引转达用户，不要伪造响应。

## Step 2: 调用

先看命令表，再执行；不要凭记忆拼 operationId：

```bash
lov-plane-cli help                          # 130 个命令，按资源分组
lov-plane-cli <command> --help              # 单命令的路径参数与查询参数
lov-plane-cli <command> ... --dry-run       # 只打印请求，不发出
```

常用工作流：

```bash
lov-plane-cli list-projects -w <workspace-slug>
lov-plane-cli list-work-items -w <slug> -p <project-id> --per-page 50
lov-plane-cli list-states -w <slug> -p <project-id>          # 建工作项前取状态字典
lov-plane-cli list-labels -w <slug> -p <project-id>          # 取标签字典
lov-plane-cli create-work-item -w <slug> -p <project-id> --data '{"name":"新任务"}'
lov-plane-cli list-work-item-comments -w <slug> -p <pid> --issue-id <issue-id>
```

参数写法：路径参数可按顺序作为位置参数，也可用同名选项；`-w`/`-p`/`--id` 分别是 `slug`/`project_id`/`pk` 的别名。请求体用 `--data '<json>'` 或 `--data @file.json`。未知参数会直接报错，不会被静默丢弃。

## Step 3: 写操作前确认

`create-*`、`update-*`、`delete-*`、`archive-*` 会改变用户的真实项目数据。

- 删除、归档、批量修改：**先确认再执行**，除非用户已明确授权本次操作。
- 不确定字段取值时，先用 `--dry-run` 给用户看将要发出的请求。
- 创建工作项前先取 `list-states` / `list-labels` 的 id，不要猜 UUID。

`api-graph.json` 记录资源层级：workspace slug → project id → 工作项 / 周期 / 模块 / 状态 / 标签 id。

## Step 4: 回读

写操作后回读对应资源确认结果，不把 2xx 当作最终验收。报告时区分成功、失败与部分完成。

常见状态码：`401` 未提供凭据；`403` token 无效或无权访问该工作区/项目；`404` slug 或 id 不存在。CLI 会原样保留 Plane 的错误体，把它转达给用户而不是改写。

## 覆盖范围

| 分组 | 操作数 | 分组 | 操作数 |
| --- | --- | --- | --- |
| Work Items | 14 | Cycles | 14 |
| Members | 13 | Modules | 12 |
| Work Item Comments | 10 | Work Item Attachments | 10 |
| Work Item Links | 10 | Projects | 8 |
| Assets | 6 | workspaces | 6 |
| Intake | 5 | Labels | 5 |
| States | 5 | Stickies | 5 |
| Work Item Activity | 4 | Work Item Relations | 2 |
| Users | 1 | | |

## 来源与限制

OpenAPI 由 Plane 自托管实例内置的 drf-spectacular 导出，未人工改写路径或字段；仅修正 `servers`（容器内地址 → 对外地址）并补充证据标注。

每个操作带 `x-observation`：`live-probe-401-403` 表示端点经真实探测确认存在（17 个），`vendor-generated-schema` 表示仅有 schema 定义（113 个）。**所有写操作从未在线执行过**，字段语义以 Plane 官方文档为准。

Plane 升级后接口可能变化：重新导出 schema 覆盖 `cli/openapi.json` 即可同步，无需改代码。

## SDK

`cli/sdk/index.mjs` 导出 `PlaneClient`，含常用入口与通用 `request(method, path, {query, body})`。凭据经构造参数或 `PLANE_API_KEY` 在内存中传入。
