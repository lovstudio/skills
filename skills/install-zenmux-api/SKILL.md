---
name: lov-install-zenmux-api
description: 为应用接入 ZenMux 服务端代理，隔离密钥并验证请求链路。支持明确输入与结果回读。Use to integrate the ZenMux
  API through a secure backend.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.0.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - install-zenmux-api
  - portable-skill
---

# ZenMux 接入 · ZenMux Setup

为应用接入 ZenMux 服务端代理，隔离密钥并验证请求链路。

## Triggers

### Activate when

- “为应用接入 ZenMux 服务端代理，隔离密钥并验证请求链路。”
- “Integrate the ZenMux API through a secure backend.”

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

1. 读取框架、现有后端、Supabase 环境与目标模型用途；先核实 ZenMux 当前官方 API 路径和可用模型。

2. 复用服务端代理或当前项目 Edge Function，认证调用方、限制允许的路径与模型，并配置适当 CORS、输入大小、超时、错误和用量边界。

3. 密钥从指定环境变量或已授权凭据库读取，不扫描其他项目 .env，不把密钥写到前端、源码、命令记录或日志。

4. 只代理必要请求，避免把任意 endpoint 变成开放转发器；根据当前 API 协议处理 JSON、流式响应和失败状态。

5. 前端调用自有后端，使用明确授权的模型或已核实默认值，不写死过时低价模型。部署仅在用户请求覆盖目标项目时执行。

6. 用最小有效请求验证鉴权、成功和失败路径，报告本地、部署、线上各自状态及实际模型。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
