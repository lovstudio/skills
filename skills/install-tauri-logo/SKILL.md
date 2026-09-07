---
name: lov-install-tauri-logo
description: 把已确认 Logo 接入 Tauri 包图标和托盘并核验生成资源。支持明确输入与结果回读。Use to install a logo in
  a Tauri application.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 4.1.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - install-tauri-logo
  - portable-skill
---

# Tauri 图标接入

把已确认 Logo 接入 Tauri 包图标和托盘并核验生成资源。

## Triggers

### Activate when

- “把已确认 Logo 接入 Tauri 包图标和托盘并核验生成资源。”
- “Install a logo in a Tauri application.”

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

1. 从用户指定资产、项目正式 Logo 和 tauri 配置确定真源；找不到时请求真实素材，不用无关品牌替代。

2. 读取 Tauri 主版本、bundle.icon、托盘初始化与 Rust 资源引用，使用现有图标生成流程生成平台尺寸。保留旧文件以便回退。

3. macOS 模板托盘图使用正确 alpha 形状并设置 template；彩色托盘和包图标分开，按系统实际行为验证浅深背景。

4. 更新所需 Rust 路径与配置；include_bytes 编译期资源变动需要重新构建，不能仅热刷新前端。

5. 验证生成的 PNG、ICO、ICNS 和包内文件；不强制关闭开发进程、清整个 target、重启 Dock 或图标缓存服务。

6. 已授权安装运行时观察 Dock 与菜单栏，否则明确仅完成文件/构建验证。网页 Logo 为独立可选交接。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
