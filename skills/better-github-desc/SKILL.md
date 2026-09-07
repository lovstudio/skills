---
name: lov-better-github-desc
depends_on:
- lov-branding-consistency
description: 依据 README 更新 GitHub 仓库描述、主题标签及已核实的官网链接。支持明确输入与结果回读。Use to update a GitHub
  repository description from its README.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 1.1.2
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - better-github-desc
  - portable-skill
---

# GitHub 仓库简介优化

依据 README 更新 GitHub 仓库描述、主题标签及已核实的官网链接。

## Triggers

### Activate when

- “依据 README 更新 GitHub 仓库描述、主题标签及已核实的官网链接。”
- “Update a GitHub repository description from its README.”

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

1. 从用户指定仓库或当前 Git remote 确定完整 owner/repo；多个目标时只问一个必要问题。读取 README.md、package.json 与 gh repo view 返回的 description、homepageUrl、repositoryTopics、url。

2. 提取项目用途、目标用户与已实现能力；可参考 strong 标签，但忽略徽章、安装命令、模板与营销夸张。生成简短、可独立理解的仓库描述，并给出 README 依据。

3. 主题只取有证据的技术和用途，遵循 GitHub 当前格式与数量限制。默认保留已有主题，仅补充相关项；删除主题须在用户要求的范围内。

4. 官网优先使用明确指定且已核实的项目地址，再核对 README 或 package.json homepage 与既有仓库值。品牌根站不能自动当作项目官网；无可靠来源时省略 homepage 修改。绝不拼接占位域名或按目录名臆造产品页面。

5. 形成目标仓库与字段前后对照。仅预览请求到此结束；明确更新请求已授权这些字段时直接执行 gh repo edit OWNER/REPO，以安全参数传入 description、需要新增的 topic 和有依据的 homepage。省略未修改字段，禁止传空值意外清除。

6. 再次 gh repo view 同一 owner/repo，逐字段比较预期与实际值；报告更新成功、无变化或部分失败。禁止顺带修改 README、仓库名、可见性、权限或发布 Release。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
