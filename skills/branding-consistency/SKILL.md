---
name: lov-branding-consistency
description: >
  面向公众号、网站、App、策划案、海报等真实发布场景，为读者可见文本建立受众、品牌角色、组件惯例与信息可见性门禁。Use when generating, editing, rendering, publishing, or reviewing audience-facing copy for brand and context fit.
license: MIT
compatibility: "Portable Agent Skills format. Core workflow is instruction-first; Python 3.8+ supports optional copy audits, Profile storage, and dependency validation."
metadata:
  author: LovStudio
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - branding-consistency
    - brand-voice
    - audience
    - editorial-review
    - microcopy
  dependencies: []
---

# lov-branding-consistency

把文案当作真实产品或出版物的一部分，而不是模型回答的残留物。先确定谁在什么场景
看到这句话、此刻要完成什么，再决定写什么、写多少，以及是否根本不该显示文字。

## Triggers

### Activate when

- “这句 Caption 很下头，按公众号读者的习惯改好。”
- “从品牌和目标受众角度审校这组网站文案。”
- “给 App 的空状态、按钮和错误提示写一套专业文案。”
- “把策划案 / 海报 / 发布说明改成目标客户真正会读的语言。”
- “Write audience-aware copy for this product surface.”
- “Review this UI copy against our brand voice and user context.”

### Do not activate when

- 用户只要求复现某位作者的个人文风；使用对应 writing-style 或 style-clone 能力。
- 用户只要求检测 AI 套话、句式均匀或平台 AI 风险；使用 humanizer 或 anti-AI 审计。
- 用户只要求营销落地页的转化结构、SEO 关键词或广告投放策略；使用 copywriting、
  landing 或 SEO 能力。本 Skill 可在其输出后做语境验收。
- 用户只要求事实研究、翻译、排版、视觉设计或正式发布，不需要改动可见文案。

## User Profile

每次运行读取 `skill.yaml` 声明的 `user-profile/v1` 上下文，按当前请求、项目上下文、
本 Skill records、共享 preferences、brand/user Profile 和安全默认值解析。品牌名称、
定位、语气、禁用表达与目标受众来自 Profile 或当前 brief，不在 Skill 源中硬编码。

用户直接声明且希望跨任务沿用的文案偏好，通过：

    python3 scripts/profile_store.py record \
      --skill-id lov-branding-consistency \
      --path records.<field> \
      --value '<json>' \
      --confirm

写回共享 Profile，并报告 canonical 路径。推断值、私有素材和凭据不得持久化。

## Skill Group Composition

执行前读取 [Skill composition](references/skill-composition.md)。本 Skill 独占“让最终
可见文案符合具体媒介、受众与品牌角色”的验收结果；相邻能力只通过 brief、草稿、
品牌 Profile 或审计报告可选交接，不是隐藏依赖。

## Cross-Skill dependency contract

当本 Skill 由另一个 Skill 的 `depends_on` 触发时：

1. 只审校该 Skill 即将交付或发布的受众可见文本，不接管其事实、数据、代码或渠道职责。
2. 引文、转录、源数据、法律文本、标识符、代码与用户原始输入默认保持逐字不变。
3. 对标题、Caption、摘要、按钮、说明、CTA、章节名、发布描述等创作型字段执行在位验收。
4. 修正文案直接回填目标制品；诊断和内部说明留在交付报告，不混入正文。
5. 发布型 Skill 发现 hard failure 时先修复或停止，不能把“已调用品牌门禁”当作通过证据。

## Core rule: write from the audience side

模型、设计师和运营者知道的制作事实，不自动属于读者。用户可见文案只能保留三类
信息：帮助理解、帮助行动、完成必要归属。其余制作说明留在 alt、备注、manifest、
设计稿标注或交付报告中。

例如：

- 内部事实：这是正文首图；Logo 是官方版本；画面由原作与 Logo 合成。
- 读者需要：作品是谁的、叫什么、何时创作；必要时补馆藏或版权信息。
- 专业 Caption：`Piet Mondrian，《Composition (No. 1) Gray-Red》，1935。`
- 更合适的选择：若正文已有“封面里的作品”完整说明，首图可以不显示 Caption。

## Workflow (MANDATORY)

### Step 0: Resolve context and references

1. 读取当前请求、相关界面或文档、共享 Profile 与本 Skill records。
2. 完整读取 [Context contract](references/context-contract.md)。
3. 按目标媒介读取 [Scene conventions](references/scene-conventions.md)。
4. 输出前读取 [Quality gate](references/quality-gate.md)。
5. 输入足够时直接推进；只有缺失项会改变品牌身份、受众或行动结果时才问一个问题。

### Step 1: Build a private context contract

在内部解析九项，不默认展示：

1. `surface`：公众号、网站、App、策划案、海报、邮件、社交媒体或其他；
2. `component`：标题、Caption、按钮、提示、Hero、正文、CTA、表单、脚注等；
3. `audience`：谁会看到，他们已知道什么，最在意什么；
4. `moment`：浏览、比较、决策、输入、等待、失败、完成或分享；
5. `job`：这句话唯一要完成的读者任务；
6. `brand_role`：个人、产品、公司、媒体、专家或平台，此刻以何种身份说话；
7. `tone`：由品牌 Profile 与情境共同决定，不从通用“专业感”猜口号；
8. `constraints`：字符、层级、屏幕、平台语法、法务、无障碍与可验证事实；
9. `visibility`：哪些事实给读者，哪些只留在制作链。

普通任务不要把这份 contract 当作前言输出。它用于决策，不是用户制品。

### Step 2: Decide whether copy should exist

先问三件事：

1. 没有这句话，读者是否仍能正确理解或行动？
2. 邻近标题、图片、控件或平台字段是否已经表达同一信息？
3. 这句话是否只是在解释制作者做了什么？

三问都不支持保留时，删除优于改写。零文案是合格结果，尤其适用于装饰图片、已经
自明的正文首图、重复按钮说明和平台已展示的作者字段。

### Step 3: Separate visible copy from metadata

建立可见性防火墙：

- **Visible copy**：读者必须理解、决定或行动的信息。
- **Accessibility text**：描述图片或控件本身，不承担营销和制作说明。
- **Attribution**：作者、作品、日期、来源、版权等必要归属。
- **Production metadata**：正文首图、官方 Logo、生成方式、导出规格、审批状态、
  文件名、组件名与实现说明；默认不出现在读者文案。

Alt、Caption、设计标注和正文不是同一个字段，不得把一段内部描述复制到所有位置。

### Step 4: Draft by component convention

1. 先写一句只完成 `job` 的核心版本。
2. 用目标组件的专业惯例决定长度、句法、标点、称谓和信息顺序。
3. 品牌通过选词、判断、节奏与克制体现，不自报“官方”“品牌化”“专业”。
4. 删除读者已经看得见的事实、内部术语、解释性尾巴和防御性补充。
5. 事实、名字、日期、版本、引用、权利状态和行动后果保持准确。
6. 用户只要局部文案时，只交付局部，不附“我做了哪些优化”。

### Step 5: Review in place

把文案放回真实邻接环境再检查：上一行、下一行、图片、按钮、页面标题、平台 author
字段和移动端宽度。脱离组件单看“挺好”的句子，放回界面后可能重复、抢层级或像
设计交付说明。

可对短文案运行辅助审计：

    python3 scripts/copy_audit.py --text '待检查文案' \
      --surface wechat --component caption --format json

脚本只定位可观察的元话语、制作术语与组件错配，不代替受众和品牌语义验收。

### Step 6: Apply the quality gate

逐项判断：

1. 说话者是否是目标品牌，而不是 AI、设计师或执行 Agent？
2. 文案是否帮助目标受众完成此刻唯一任务？
3. 是否暴露正文首图、官方 Logo、组件、生成、导出等制作链信息？
4. 是否重复平台、界面或图片已经表达的内容？
5. 是否把 alt、Caption、归属和正文混为一谈？
6. 语气是否来自品牌与场景，而不是“专业、温暖、高级”等空洞形容词？
7. 是否符合此组件的真实长度、句法、标点和行动后果？
8. 删除后是否更好？如果是，删除。

任何一项失败都先修复，再交付。

## Output Contract

- 默认只输出可直接粘贴或写入目标位置的最终文案。
- 审校请求先给一句结论，再给最高优先级问题；用户要求修改时直接附最终版本。
- 存在多个合理方向时最多给三版，并明确差异来自受众或品牌策略，不堆同义句。
- 不把内部 brief、推理步骤、制作说明、Prompt 或验收清单混入读者制品。
- 不虚构品牌事实、用户研究、数据、评价、权利状态或产品承诺。

## Dependencies

核心能力为 instruction-first，无网络、凭据或 sibling Skill 强依赖。Python 3.8+
用于可选本地审计和 Profile 存储；完整源校验需要 PyYAML。
