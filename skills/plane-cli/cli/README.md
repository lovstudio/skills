# Plane REST API v1

由 Plane v1.4.2 自托管实例导出，共 130 个操作、17 个资源分组。

实例地址 http://localhost，API 前缀 /api/v1。

## 证据来源

- **vendor-generated-schema** — docker exec -e ENABLE_DRF_SPECTACULAR=1 plane-api-1 python manage.py spectacular --format openapi-json
  drf-spectacular 由 Plane 自身内置，导出为一次性进程，未改变运行中的实例配置。
- **live-probe** — curl 对每个 tag 的代表 GET 端点各发两次请求（无认证 / 无效 X-API-Key）；结果：17/17 无认证=401、无效 key=403
  证明端点真实存在且 API key 认证链路生效；未使用任何真实凭据。
- **live-endpoint** — curl http://localhost/api/instances/；结果：200 is_self_managed=true

OpenAPI 文档本身由实例内置的 drf-spectacular 生成，未人工改写路径或字段，只修正了 servers 并补充 `x-observation` 证据标注。17 个操作经过 live 探测（无认证 401、无效 key 403），其余 113 个仅有 schema 定义，未在线执行。

## 认证

请求头 `X-API-Key`。获取方式：登录 Plane → 右上角头像 → Settings → API tokens → Add API token。

凭据不写入本目录任何文件。运行时通过环境变量提供：

```bash
export PLANE_BASE_URL=http://localhost
export PLANE_API_KEY=<你的 api key>
```

## 安装

```bash
cd <生成目录>
npm link          # 或 npm install -g .
```

未安装时也可直接运行 `node bin/lov-plane-cli.mjs`。

## 资源分组

| 分组 | 操作数 |
| --- | --- |
| Work Items | 14 |
| Cycles | 14 |
| Members | 13 |
| Modules | 12 |
| Work Item Comments | 10 |
| Work Item Attachments | 10 |
| Work Item Links | 10 |
| Projects | 8 |
| Assets | 6 |
| workspaces | 6 |
| Intake | 5 |
| Labels | 5 |
| States | 5 |
| Stickies | 5 |
| Work Item Activity | 4 |
| Work Item Relations | 2 |
| Users | 1 |

## 用法

```bash
lov-plane-cli help                                    # 按分组列出全部命令
lov-plane-cli list-projects -w <workspace-slug>
lov-plane-cli list-work-items -w <slug> -p <project-id>
lov-plane-cli create-work-item -w <slug> -p <project-id> --data '{"name":"新任务"}'
lov-plane-cli list-projects --help                    # 查看单个命令的参数
lov-plane-cli list-projects -w <slug> --dry-run       # 只打印请求，不发出
```

命令表在启动时由随包的 `openapi.json` 构建，operationId 转为 kebab-case 即命令名，因此 130 个操作全部可直接调用，无需为每个端点写代码。路径参数可按顺序作为位置参数传入，也可用同名选项；`-w`/`-p`/`--id` 是 `slug`/`project_id`/`pk` 的别名。请求体用 `--data '<json>'` 或 `--data @file.json`。

## 调用顺序

`api-graph.json` 记录资源层级：workspace slug → project id → 工作项/周期/模块/状态/标签 id。创建工作项前先用 `list-states` 和 `list-labels` 取字典 id。

## 限制

- 未执行任何写操作（POST/PATCH/DELETE 仅来自 schema 定义，未在线验证）。
- 实例尚未创建管理员与工作区，因此未用真实 API key 验证 200 响应体。
- schema 中 servers 的 http://localhost:8000 是容器内地址；对外经 proxy 为 http://localhost。
- drf-spectacular 导出时报告 35 warnings / 4 errors（operationId 冲突，已由数字后缀消解）。

## SDK

`sdk/index.mjs` 导出 `PlaneClient`，包含常用入口和通用 `request(method, path, {query, body})`。凭据经构造参数或 `PLANE_API_KEY` 在内存中传入，不落盘。
