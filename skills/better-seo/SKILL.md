---
name: lov-better-seo
depends_on:
- lov-branding-consistency
description: 检查 Next.js 页面元数据、索引规则、站点地图与分享展示。支持明确输入与结果回读。Use to review and improve
  Next.js SEO.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 1.0.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - better-seo
  - portable-skill
---

# Next.js SEO

检查 Next.js 页面元数据、索引规则、站点地图与分享展示。

## Triggers

### Activate when

- “检查 Next.js 页面元数据、索引规则、站点地图与分享展示。”
- “Review and improve Next.js SEO.”

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

1. 读取 Next.js 版本、路由模式、部署域名和现有 metadata；检查动态页面、canonical、OG/Twitter、sitemap、robots、JSON-LD 与鉴权页面。

2. 输出有路径和影响的优先级清单。依据当前官方文档与项目版本修复；已有 SEO helper 直接扩展，不为每个项目强造新工具库。

3. 从已核实配置取网站地址。动态 metadata 放服务端支持位置；需要时拆分客户端组件，不强迫所有动态路由静态生成。

4. 站点地图只列可索引的真实公开路由，lastModified 使用实际内容变更时间；私有页面检查访问控制，robots 不能替代权限。JSON-LD 只陈述页面上真实内容。

5. 核实 canonical、robots 和 sitemap 一致，检查分享图可访问性与替代文本，运行构建并回读现有服务输出；不把构建通过当成搜索引擎已收录。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
