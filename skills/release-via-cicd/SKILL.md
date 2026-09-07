---
name: lov-release-via-cicd
license: MIT
compatibility: 'Requires Git, GitHub CLI (`gh`), the project''s package manager, and
  platform build tools. Tauri macOS signing additionally requires Apple Developer
  ID certificate and notarization credentials.

  '
description: 配置或运行现有项目发布流水线，并回读产物与真实上线状态。支持明确输入与结果回读。Use to set up or run a verified
  CI/CD release.
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 8.7.1
  tags:
  - release
  - cicd
  - github-actions
  - tauri
  - macos-signing
  - notarization
  - changesets
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
---

# CI/CD 发布

配置或运行现有项目发布流水线，并回读产物与真实上线状态。

## Triggers

### Activate when

- “配置或运行现有项目发布流水线，并回读产物与真实上线状态。”
- “Set up or run a verified CI/CD release.”

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

1. 区分 setup、publish、setup+publish、local、ci、ci-auto 与 status；仅审计或配置不授权发布。读取项目语言、包管理器、版本、CHANGELOG、分支、remote、保护规则及现有 workflows。

2. 保留当前发布方式，配置缺口先按项目事实修复。迁移 semantic-release 到 changesets 是独立行为，只有用户要求时实施；不无条件安装 changesets。

3. 发布前审阅目标差异和已暂存文件，只提交本次发布涉及文件。脏工作区不得自动 git add -A，不能强制切主分支、自动吞掉提交失败或覆盖其他任务。

4. 默认按当前版本补丁递增，0.x 保持 0.x；破坏性升级按用户指定处理。同步所有实际版本源、lockfile 和 CHANGELOG，发布说明从已核验变更生成，不虚构历史。

5. 分支发布遵守保护与 PR 流程，必要时使用独立工作树；不能绕过评审、hooks、签名或非快进保护。已发 tag 不改写，缺漏用补丁版修复。

6. Node/monorepo 依据配置生成 changeset 并运行 version；Shell 或其他项目按既有版本文件与 tag 规则处理。推 tag 和触发 workflow 只在发布授权的目标范围内执行。

7. CI 参数、action 与签名配置按当前官方和项目既有实现核验。桌面或 Tauri 项目完整读取 references/tauri-release-workflow.md；其他项目读取 references/general-release-playbooks.md。

8. 等待已触发 run 的最终状态，记录具体 run ID、commit、tag 和失败日志；较长过程使用宿主等待或监控工具，不以排队视为完成。

9. 回读 Release 与附件，桌面验证签名、公证、安装包内 App 和更新链；需要区域镜像时只在主发布和验证通过后同步，不能让镜像失败掩盖主产物状态。

10. 只在明确授权时向相关 issue 发消息或关闭；发布本身不自动授权对外评论。报告配置、构建、发布、官网/商店与安装验证各层真实结果。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
