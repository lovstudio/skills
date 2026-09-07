---
name: lov-image-creator
license: MIT
compatibility: 'Requires Python 3.8+. End-to-end image generation requires ZENMUX_API_KEY
  plus google-genai and Pillow, which gen_image.py can install into the user Python
  environment. Code rendering requires Playwright Python.

  '
description: 按用途生成图像、制作可编辑图文布局或整理图像提示词。支持明确输入与结果回读。Use to create an image, designed
  graphic, or image prompt.
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.3.1
  tags:
  - image-generation
  - design
  - rendering
  - prompt-engineering
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
---

# 图像创作

按用途生成图像、制作可编辑图文布局或整理图像提示词。

## Triggers

### Activate when

- “按用途生成图像、制作可编辑图文布局或整理图像提示词。”
- “Create an image, designed graphic, or image prompt.”

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

1. 先区分生成图、编辑已有图、含排版的设计稿与仅提示词。根据用户意图选机制，保持参考图、文字、品牌资产与用途边界。

2. 优先使用当前宿主提供的图像生成/编辑工具，按其输入协议传递参考图。用户只要提示词时只输出提示词，不能声称已有图像。

3. 外部 API 仅在该渠道被授权且凭据已配置时使用，先核实当前生产模型与官方端点，不固定过时模型、不自行安装全局 Python 包或扫描其他项目密钥。

4. 海报、卡片等需可编辑文字时可用 HTML/SVG 与已安装的排版工具；根据实际字体检查中文覆盖，使用可靠静态布局，不引用不存在的 React UMD 版本。

5. 生成或编辑完成后查看最终文件，核对构图、文字、参考一致性、尺寸和透明度；不要用纯图像生成伪造真实 Logo、来源照片或事件证据。

6. 保存到用户指定位置或项目 output，回读实际文件并展示结果。不自动打开前台应用、上传或发布；原旧 API 脚本不再作为默认执行入口。

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
