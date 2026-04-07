---
name: lovstudio:project-port
description: 基于项目名生成稳定唯一的端口号，并自动更新项目配置。当用户需要为项目设置端口、启动开发服务器、解决端口冲突或初始化新项目配置时使用此 skill。
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
项目 "lovstudio" 的端口号是：7965
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
