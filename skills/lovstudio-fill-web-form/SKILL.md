---
name: lovstudio:fill-web-form
category: Content Processing
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
  author: lovstudio
  version: "1.1.0"
  tags: form web fill knowledge-base conference speaker application
---

# fill-web-form — Fill Web Forms from Local Knowledge Base

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
`手工川-<form-topic>-<YYYY-MM-DD>-v0.1.md`

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
