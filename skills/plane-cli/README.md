# Plane 助手 · Plane Assistant

用命令行读写 Plane 项目管理实例，覆盖 REST API v1 的 130 个操作。

## 安装

```bash
npx skills add lov-plane-cli -g -y
```

本地开发时也可直接 `npm link` 包内的 `cli/`。

## 使用

```bash
export PLANE_BASE_URL=http://localhost
export PLANE_API_KEY=<api token>      # Plane → 头像 → Settings → API tokens

lov-plane-cli help
lov-plane-cli list-projects -w <workspace-slug>
lov-plane-cli create-work-item -w <slug> -p <project-id> --data '{"name":"新任务"}'
```

命令表由随包的 `cli/openapi.json` 在启动时构建，因此 130 个操作全部可直接调用。完整触发条件、参数写法、写操作确认要求与来源限制见 `SKILL.md`。

## 来源

OpenAPI 由 Plane 自托管实例内置的 drf-spectacular 导出，未人工改写路径或字段。每个操作带 `x-observation` 证据等级；写操作从未在线执行过。
