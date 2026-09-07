---
name: lov-init-auth
license: MIT
compatibility: 'React 18+, Vite, Supabase JS 2.x, and optional Tauri 2 or Electron
  desktop shells. Desktop OAuth requires a system-browser opener, an application-specific
  deep-link scheme, PKCE code exchange, and a matching Supabase redirect allowlist.

  '
description: 为 React 应用接入 Supabase 登录、账户恢复及桌面浏览器 OAuth。支持明确输入与结果回读。Use to add Supabase
  authentication to a React application.
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.2.1
  tags:
  - supabase
  - auth
  - oauth
  - pkce
  - tauri
  - electron
  - desktop
  - system-browser
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
---

# Supabase 登录接入 · Supabase Auth Setup

为 React 应用接入 Supabase 登录、账户恢复及桌面浏览器 OAuth。

## Triggers

### Activate when

- “为 React 应用接入 Supabase 登录、账户恢复及桌面浏览器 OAuth。”
- “Add Supabase authentication to a React application.”

### Do not activate when

- 只是查询本 Skill 的说明，或请求与上述结果无关的任务；不执行实际业务操作。
- 用户仅要预览或审查时，不进入修改、提交或发布分支。

## Execution boundary

自然语言请求即可触发；无需旧 slash 路径、参数插值或指定助手。明确解析当前请求中的
项目、目标文件、选项与输出位置；用当前宿主实际提供的文件、搜索、CLI 和浏览器能力。
项目依赖版本与外部 API 在执行时核实，不能假设示例是现行配置。随包脚本从 Skill 根解析，
业务文件从目标项目根解析。先读当前状态，保护已有未提交内容与其他任务的暂存区。
分析、预览请求保持只读；修改、提交、推送、部署和发布各依当前请求的明确范围执行。
不绕过保护、自动发送消息、强制结束用户进程或抢前台。失败保留可诊断原始错误。

## Workflow

1. 读取现有框架、认证实现、Supabase client 与目标项目配置。使用该应用的 Supabase URL 和 publishable key，不绑定作者生产账号或跨项目读取凭据。

2. 复用项目状态库与路由，接入注册、登录、登出、邮件确认、密码找回、更新密码和重发邮件；需要的表类型从目标 schema 生成，不假设存在固定 profiles、user_roles 或管理员结构。

3. 建立单一会话订阅并清理监听，处理初始化、token 刷新、访客与错误态；所有服务端权限必须由 RLS 或后端验证，前端 isAdmin 不构成授权。

4. 浏览器 OAuth 配置当前站点允许的回跳地址，校验 redirect 路径避免开放重定向。遵循当前 Supabase JS 文档及项目版本，使用现有密码表单校验。

5. Tauri/Electron 默认通过系统浏览器完成账号登录，使用 PKCE、产品专属深链和 redirect allowlist；先注册回调监听再打开浏览器，同时处理冷启动和已运行实例。

6. 回调严格校验 scheme、host、path、code 和 flow 标识，去重处理并完成 exchangeCodeForSession，不能把 token 放自定义 URL、日志或不可信 WebView。保留密码管理器与原生浏览器能力。

7. 分别验证成功、取消、错误、刷新、登出、过期与密码恢复，桌面需验证浏览器到应用完整回跳；部署和修改共享认证配置需在请求范围内。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
