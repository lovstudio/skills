---
name: lov-install-design
description: 将项目品牌设计规范映射到已有前端样式与组件系统。支持明确输入与结果回读。Use to install a project design system.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.2.2
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - install-design
  - portable-skill
---

# 设计系统接入

将项目品牌设计规范映射到已有前端样式与组件系统。

## Triggers

### Activate when

- “将项目品牌设计规范映射到已有前端样式与组件系统。”
- “Install a project design system.”

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

1. 从项目或 Profile 读取品牌设计规范、字体与资产，识别框架、Tailwind 版本和已有 token；不存在规范时用现有 UI 归纳安全默认值。

2. 将颜色、文字、圆角和间距映射到 semantic token，保留主题和暗色模式；不把作者品牌或错误的陶土色值硬编码给所有项目。

3. 按项目当前技术栈增加必要样式依赖和组件，复用 shadcn 等现有库；只安装需要的组件，不覆盖整个配置。

4. 设计说明放项目规范或设计文档。全局配置仅在用户明确指定全局范围时修改，不能用 cwd 判断授权。

5. Logo 按平台资产事实源增量接入，桌面图标与网页图标分别验证；不删除既有图标目录或启动服务抢前台。

6. 运行构建并检查代表性页面、断点、暗色、焦点和对比度，记录未验证的 UI 状态。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
