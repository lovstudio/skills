---
name: lov-fill-web-form
category: Office Automation
tagline: "Fill web forms from local knowledge base. Fetch URL → deep-search KB → generate markdown doc."
description: >
  Fill web forms by fetching form fields from a URL, deep-searching the user's
  local knowledge base for relevant info, and generating a markdown document
  with all answers pre-filled. Use when the user provides a URL to a web form
  (conference application, speaker submission, event registration, profile form)
  and wants help filling it out from their existing materials.
  Also trigger when the user mentions "填网页表", "fill web form", "网页填表",
  "表单填写", "申请表填写", "conference application", "speaker submission",
  "讲师申请", "报名表", or provides a URL with "form", "feedback", "apply",
  "register", "submit" in the path.
license: MIT
compatibility: >
  No external dependencies. Uses built-in tools: WebFetch, Agent (Explore),
  Grep, Glob, Read, Write. Requires internet access for URL fetching.
metadata:
  author: contributors
  version: "1.2.2"
  tags: form web fill knowledge-base conference speaker application
---

# 网页填表助手 · Web Form Assistant

Fetch a web form, extract all fields, deep-search the user's local knowledge
base for matching information, and output a ready-to-use markdown document.

## When to Use

- User provides a URL to a web form and wants help filling it
- Conference speaker applications, event registrations, profile forms
- Any scenario where form fields can be answered from existing local materials

## Workflow (MANDATORY)

### Step 1: Fetch and extract form fields

Use `WebFetch` to retrieve the form page and extract ALL fields:

```
WebFetch(url, prompt="Extract ALL form fields. For each field list: label,
type (text/textarea/select/radio/checkbox/file), required status, options
if applicable, min length constraints. Return structured list.")
```

If the form has radio/select fields, make a second `WebFetch` call to get
the exact option text for each.

### Step 2: Deep-search local knowledge base

Launch an `Agent` (subagent_type: Explore, thoroughness: very thorough) to
search the user's knowledge base. The agent prompt MUST include:

1. The complete list of form fields from Step 1
2. Instructions to search for:
   - Personal/professional bio and profile files
   - Speaking/conference history
   - Project descriptions and achievements
   - Company/organization info
   - Published articles and their topics
   - Awards, credentials, media mentions
3. Search locations (adapt to user's repo structure):
   - Profile/about files (`**/profile/**`, `**/about/**`, `**/bio/**`)
   - CLAUDE.md files for project context
   - Posts and articles directories
   - Project directories
   - Any `official.md`, `awards.md`, `resume` files
4. Also check user memory (MEMORY.md) for cached info

Run this in parallel with any additional `WebFetch` calls from Step 1.

### Step 3: Map fields to content

For each form field, synthesize the best answer from search results:

| Field Type | Strategy |
|-----------|----------|
| Short text (name, company, city) | Direct extraction from profile |
| Bio/introduction (min chars) | Compose from official bio, expand to meet minimum |
| Long-form (case background, solution) | Synthesize from articles, projects, talks |
| Radio/select | Pick the best-matching option based on profile |
| File upload | Mark as "needs manual upload" with specs |
| Private (phone, email) | Mark as "needs manual input", suggest if found |

If required fields remain unknown after local search, use `AskUserQuestion` to
collect only those missing values. Do not ask for fields already inferred from
context.

### Step 4: Generate output document

Write a markdown document with ALL form fields filled. Format:

```markdown
---
title: "<Form Name> - 填写内容"
status: draft
---

# <Form Name>

> 表单地址：<URL>

---

## 1. <Field Label>

<Filled content or instruction>

---

## 2. <Field Label>

...
```

**Rules:**
- Number every field matching the form order
- For radio/select: prefix chosen option with `**✅ 选择：**`
- For file uploads: use `> ⚠️ 需上传：<specs>`
- For private fields: use `> ⚠️ 需手动填写`（with suggestion if available）
- For textarea fields with min length: ensure content meets or exceeds minimum
- Include a summary table at the end showing field → status (filled/manual)
- **MANDATORY:** Append an "inspected sources" section at the end of the document
  with a tree of all files that were read/searched during knowledge base retrieval:

```markdown
---

## 附录：检索文件路径

```
knowledge-base/
├── profile/
│   └── official.md          ← 个人简介
├── posts/standalone/2025/
│   ├── 07-10-Vol-51...md    ← 演讲经历
│   └── 06-25-comate...md    ← AI工具评测
├── 1-Projects/lovpen/
│   └── ...                  ← 产品信息
└── CLAUDE.md                ← 项目上下文
```
```

  This tree helps the user verify source coverage and spot missing materials.

**Output naming:** Follow user's naming convention. Default:
`品牌方-<form-topic>-<YYYY-MM-DD>-v0.1.md`

### Step 5: Present summary

After writing the file, show:
1. A summary table of all fields with fill status
2. Count of auto-filled vs needs-manual fields
3. Remind user which fields need manual action (uploads, private data)
4. **The inspected files tree** (same as in the document appendix, for quick review)

## Key Principles

1. **Pre-fill aggressively** — search deeply, compose content, don't leave blanks
2. **Meet all constraints** — character minimums, bullet point counts, etc.
3. **Match form tone** — conference apps need professional language, registrations can be brief
4. **Respect privacy** — never guess phone numbers or passwords, mark for manual input
5. **Cite sources** — when composing from knowledge base, the content should be accurate to the user's real experience

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 维护备注

- 飞书分享表单（`feishu.cn/share/base/form/...`）用内部滚动容器 `.base-form-layout__scroll-container`，`Page.getLayoutMetrics` 的 cssContentSize 恒等于视口高；整页 clip 截图只会拍到当前滚动位置，必须逐段设 `scrollTop` 再截（2026-09-03, e38086f）
- 同一页面里元素在视口外时，ego-browser `click(selector)` 会报成功但实际没点中（选中态不变）；必须先 `scrollIntoView({block:'center'})`、在同一轮重新取 `getBoundingClientRect` 再按坐标点击，并逐项回读校验（2026-09-03, e38086f）
- 飞书表单选项的选中判据是 `.base-component-select-list-editor-icon` 的 class 是否含 `no-checked`；按 `checked/selected/active` 正则匹配 outerHTML 一律判不出来（2026-09-03, e38086f）
- 飞书表单有条件题：选中某选项会插入新的必填题并让后续题号整体后移（实测选「已有部分队友」多出「队伍信息」「对队友的期望」两道必填）；填完后必须重新 dump 全量题目再校验，不能沿用第一次快照的题号（2026-09-03, e38086f）
- 飞书表单的文本题是 `[contenteditable="true"].adit-container` 富文本编辑器，不是 input/textarea；`fillInput` 不适用，用真实点击聚焦 + `typeText`，回读 `innerText` 时结尾会带一个零宽字符 `​`（2026-09-03, e38086f）
- 「查看提交记录」需要飞书手机号/邮箱登录并走验证码，不要为了核验而去登录；以提交成功页为验收证据（2026-09-03, e38086f）
- 判断登录：右上角是灰色默认头像（`.ud__avatar-neutral`，页面里没有 `.share-user-avatar-container`）即未登录；表单要求飞书登录时先登录再填：点头像弹出页内登录框，右上角 `.switch-icon` 切到扫码，交给用户扫码，不代填账号（2026-10-31）
- 未登录时文本题的 `[contenteditable]` 编辑器要首次点击题目后才渲染（初始 0 个），按选择器找不到编辑器不能判定题目不可填（2026-10-31）
- 文本题可用 JS `focus()` 编辑器并把选区折叠到末尾，再用 `keyboard.insertText` 或宿主 `type` 输入；多行逐行插入、行间按 Enter（宿主 `type` 里的 `\n` 也会换行），「1. 」开头不会被转成自动列表，回读 `innerText` 去掉零宽字符后与原文逐字一致（2026-10-31）
- 附件题的 `input[type=file]` 可直接 `setInputFiles`，一次可传多个，再次设置是追加，不会替换已上传的附件（2026-10-31）
- 附件上传没有进度条，视频卡片只显示通用图标；判断传完要读 `.bitable-attach-editor` 的 React props：键名是 `__reactInternalInstance$*`（React 16，不是 `__reactFiber$*`），向上 1 层 `memoizedProps.value[i]` 的 `state === "loaded"`、有 `attachmentToken` 且 `size` 与本地文件一致才算完成；键名用错会让等待条件永远不成立，一直等到超时（2026-10-31）
- 表单本地草稿（`localStorage` 里以分享 token 开头的键）只存文本题，不存附件，不能拿来核验附件是否传完（2026-10-31）
- 页面 resource timing 缓冲默认 250 条，停留久了上传请求不会再出现在 `performance.getEntries()`；观察上传要用 CDP `Network.*` 事件：分块请求是 `internal-api-drive-stream.feishu.cn/space/api/box/stream/upload/merge_block/`，单个文件完成是 `/space/api/box/upload/finish/` 返回 `code: 0` 和 `file_token`（2026-10-31）
- Claude 桌面内置浏览器会拦截外部页面访问 localhost（`net::ERR_BLOCKED_BY_CLIENT`），也没有文件上传工具，本地照片和视频传不进飞书表单；需要上传附件时改用 ego-browser 的 `setInputFiles`（2026-10-31）

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
