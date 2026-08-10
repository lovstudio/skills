---
name: lov-project-port
category: Dev Tools
tagline: "Generate stable unique dev port (3000–8999) from project name."
description: >
  Generate a stable unique dev port (3000-8999) from a project name and help
  update project config. Use when the user needs to set a project port, start a
  dev server, resolve port conflicts, initialize a new project, or mentions
  "端口", "port", "dev server", "端口冲突", "project port".
license: MIT
compatibility: >
  Requires bash for scripts/hashport.sh. Works on macOS/Linux; port occupancy
  reporting uses lsof when available.
metadata:
  author: contributors
  version: "0.1.1"
  tags: dev-server ports project-setup
---

# Project Port Generator

为项目生成稳定唯一的端口号（范围 3000-8999），同一项目名永远返回相同端口。

## 端口生成算法

```python
def generate_port(project_name: str) -> int:
    hash_value = sum(ord(c) * (i + 1) for i, c in enumerate(project_name))
    return 3000 + (hash_value % 6000)
```

## 使用场景

### 1. 查询项目端口

用户询问端口时，直接计算并告知：

```
项目 "skill-publisher" 的端口号是：7965
```

### 2. 更新项目配置

检测并更新项目中的端口配置文件：

| 文件 | 配置方式 |
|------|----------|
| `.env` / `.env.local` | `PORT=<port>` |
| `package.json` | scripts 中的 `--port <port>` |
| `vite.config.ts` | `server.port: <port>` |
| `next.config.js` | 通常使用 .env |

更新时优先使用 `.env` 方式，最小侵入性。

### 3. 启动开发服务器

```bash
PORT=$(scripts/hashport.sh) pnpm dev
```

## 脚本

运行 `scripts/hashport.sh [project-name]` 生成端口：

```bash
# 使用当前目录名
./scripts/hashport.sh
# 输出: 7965

# 指定项目名
./scripts/hashport.sh my-project
# 输出: 5123
```

## 端口冲突处理

若端口被占用：
1. 提示用户哪个进程占用了端口
2. 建议使用 `lsof -i :<port>` 查看
3. 可追加后缀生成备用端口：`generate_port("project-dev")`

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
