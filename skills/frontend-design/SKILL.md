---
name: lov-frontend-design
description: >
  把需求、现有界面与真实素材落实为有辨识度、交互一致的前端，覆盖页面、组件、导航、GSAP 展示及图片音视频。触发：设计前端、界面不够专业、制作交互案例集；design or refine a frontend UI.
license: MIT
compatibility: "Repository-aware agent; HTML/CSS/JS, React, Vue or existing stack. Browser inspection for runtime acceptance; Python 3.8+ and PyYAML for local Skill utilities."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.3.0"
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags: [frontend-design, product-interaction, art-direction, gsap, multimedia, accessibility]
---

# lov-frontend-design

把内容、视觉和交互落实为可用的界面。目标受众应能看懂、能操作、能完成任务，同时
获得与内容相称的审美体验。直接实现修改请求；用户明确要求审查时保持只读。

这是手工川工作室维护的通用前端设计方法。维护者身份不决定作品品牌：优先遵守当前
请求与项目设计系统；独立专题可以采用适合内容的视觉方向，不把工作室配色、Logo、
字体或个人路径写成所有用户的默认值。

## Triggers

### Activate when

- “用手工川工作室版本设计这个前端，直接实现。”
- “这个工具栏能用，但按钮、图标和状态不像一个专业产品。”
- “把真实案例做成支持图片、音频和视频的交互展示，使用 GSAP。”
- “为现有官网增加资源入口，并验证桌面和手机的访问路径。”
- “Design or refine this frontend UI with the existing product conventions.”
- “Audit this interactive case collection without changing the site.”

### Do not activate when

- 只创建或安装 Skill，或只发布已完成页面：使用相应创建、发布能力。
- 核心任务是品牌定位、商业叙事和营销转化：优先已有 Landing Page 能力。
- 只调后端并发、启动架构、请求封装、CSS 清理或独立媒体剪辑：交给对应能力。

## Runtime context

每次读取 `skill.yaml` 和 [Profile contract](references/user-profile.md)。从当前请求、
项目现状、Skill records、共享 preferences、brand/user Profile、安全默认值解析上下文。
环境变量可指定 Profile 来源；显式请求始终优先。仅消费 Manifest 声明的字段。

    python3 scripts/profile_store.py read --skill-id lov-frontend-design --pretty

只有用户明确表达跨任务偏好时才用 `profile_store.py record --confirm` 保存，随后报告
保存路径。单次“无需遵循品牌限制”留在当次上下文，不推断成永久品牌偏好。
秘密、素材原件和个人绝对路径不得写入可分发 Skill。

## References by need

- 所有任务：[Interaction contract](references/interaction.md)。
- 新视觉方向或整体重设计：[Art direction](references/art-direction.md)。
- 动态图表、GSAP、图片、音频、视频或演示模式：[Motion and media](references/motion-and-media.md)。
- 交付前：[Acceptance](references/acceptance.md)。
- 选择相邻能力时：[Skill composition](references/skill-composition.md)。
- 来源与历史案例：[Provenance](references/provenance.md)。

## Workflow

### 1. 找到真实界面与验收路径

读取项目规则、Git 状态、目标路由、相邻页面、共享组件和已有数据来源，保留其他工作。
区分产品小改、完整界面设计和独立展示。新增导航不必重做品牌策略；全新展示需要先
理解受众和内容结构。工作量随范围变化。

内部明确受众、打开时已知信息、主要任务、核心内容、输入输出、技术限制、风格约束、
资产真伪与最终访问路径。从上下文能确认的直接决定，只问会改变结果的缺口。
使用宿主真实工具，不假定拥有浏览器、媒体生成或部署能力。

### 2. 设计理解顺序与操作语义

确定第一屏让人理解什么，主体如何展开证据，最后如何继续行动。长内容采用逐层
展开、检索、筛选、索引或具体案例，不把章节机械排成同尺寸卡片。

按 [Interaction contract](references/interaction.md) 区分导航、动作、状态和切换。
主要控件有明确输入、状态、结果和失败后的下一步，复用现有组件与状态模型。
调用 `lov-branding-consistency` 审校标题、按钮、说明和 Caption，保留来源文本与数据。
需要长篇正文时接受经确认的稿件，不把前端设计自动扩展成研究或文章创作。

### 3. 按情境确定视觉方向

已有产品沿用 token、组件、字体和布局习惯，把新意放在内容组织与细节上。
新作品用一句话说明这个方向为什么适合内容与受众，再确定排版、密度、色彩、素材
处理和一项可记忆的视觉特征。装饰不能争夺图表、证据与主要动作的注意力。

标题、正文、数据、注释承担不同排版角色；检查中文断行、数字、长英文和真实宽度。
字体选择服从可读性、授权、加载与项目现状，不因反模板化而全局替换字体。

### 4. 实现完整用户路径

使用现有技术栈和依赖。独立静态展示可采用 HTML/CSS/JS，不为样式增加应用框架。
相同动作组重复出现时复用公共实现。数据来源真实，快照标注范围与日期，不把历史
样本数量冒充当前全部能力。

涉及媒体时完整读取 [Motion and media](references/motion-and-media.md)。GSAP 服务于
关系变化、叙事推进与演示，不作为基本内容可见性的唯一开关。主要操作都有真实结果。

集成站点同时检查桌面导航、移动端、身份分支、语言与目标路由。独立 HTML、下载和
浏览器目的地采用合适的原生链接，避免客户端路由误接管。仅在当前授权范围内部署，
设计完成和线上发布分别验收。

### 5. 在真实界面检查并修复

按 [Acceptance](references/acceptance.md) 覆盖本次涉及的状态与操作，以真实输入走完
主要路径。先解决内容、交互和可访问性，再调整动效与细节；检查最窄支持宽度和常用
桌面。浏览器不可用时报告静态结果与运行待验项，不声称点击、播放或辅助技术已通过。

保存必要截图、测量、检查命令或可回读产物。只读审查列出核实的问题及影响；修改
请求落实修复并复验。证据不完整时标记具体缺口，不写虚构评分。

### 6. 简洁交付

给出实际页面或文件、主要变化、已验证路径与剩余限制。页面不展示内部 brief、设计
自评、Agent 操作记录或“专业制作”等自我说明。可复用经验更新最窄参考与真实案例，
不把单个作品的风格升级成普遍规则。

## Output contract

- 页面或组件的项目原生代码，以及必要的真实素材引用。
- 明确的内容层级、控件文案和一致的操作状态。
- 媒体文件或经核实的地址、用途与来源记录。
- 相称的构建检查、浏览器验证与未验证项。
- 准确区分本地与线上状态；Skill 公开分发交给发布能力。
