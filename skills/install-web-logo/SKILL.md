---
name: lov-install-web-logo
description: 将正式 Logo 接入 favicon、PWA manifest、网页头部和相关组件。支持明确输入与结果回读。Use to install
  a web logo and favicon set.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.2.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - install-web-logo
  - portable-skill
---

# 网站 Logo 助手 · Website Logo Setup

将正式 Logo 接入 favicon、PWA manifest、网页头部和相关组件。

## Triggers

### Activate when

- “将正式 Logo 接入 favicon、PWA manifest、网页头部和相关组件。”
- “Install a web logo and favicon set.”

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

1. 读取正式 Logo、已有 public/assets、框架 metadata、manifest 与 Logo 组件，确定真实引用路径，保留已有自定义资产。

2. 按使用场景生成 favicon ICO 的 16/32/48 尺寸、PNG、180px Apple touch 和 192/512 PWA 图标；只有需要的版本才生成，保留矢量源。

3. 按 Next.js、Vite 或当前框架的正确入口更新图标 metadata、HTML head 与 manifest，检查 MIME、路径与部署 base URL。

4. 组件能直接使用现有 SVG 时保留，不强迫所有 inline SVG 改为图片。替代文本服务实际内容，装饰图避免重复朗读。

5. 分享 OG 图只有用户需要且品牌素材允许时制作；与 favicon 独立，不能把默认色背景当正式分享视觉。

6. 回读文件与页面链接，验证缓存更新、浅深背景和真实服务响应；未启动页面时如实标记。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
