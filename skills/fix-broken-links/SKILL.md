---
name: lov-fix-broken-links
description: 核对项目路由及页面链接，修复失效目标并保留有效导航。支持明确输入与结果回读。Use to find and fix broken links
  in a project.
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
  - fix-broken-links
  - portable-skill
---

# 链接修补匠 · Link Fixer

核对项目路由及页面链接，修复失效目标并保留有效导航。

## Triggers

### Activate when

- “核对项目路由及页面链接，修复失效目标并保留有效导航。”
- “Find and fix broken links in a project.”

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

1. 检索页面 href、菜单、Footer、README 与路由定义；分离内部路由、动态模板、hash、外站和刻意禁用入口。

2. 优先静态核对真实路由与文件，外链按正常重定向检查；403、鉴权页或网络失败不能直接当 404。

3. 报告文件位置、目标、失败证据与替代项。用户要求修复时更新确切错误链接；不确定目标保留并标注，不凭猜测改 URL。

4. 有意用作交互触发的锚点和代码示例占位符不能一律删除；必要的入口改为合理禁用态并保留可访问性。

5. 回读修改页面与目标，运行相关路由或构建检查；报告仍不可验证的外链。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
