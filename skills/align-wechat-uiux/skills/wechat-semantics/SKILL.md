---
name: lov-wechat-semantics
description: >
  将微信数据库类型、嵌套 XML/JSON、身份与状态归一为稳定产品语义，定位最早失真层；适用于“这是什么微信消息”“修复消息分类”、"model the WeChat message" 或 review parser semantics。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  tags:
    - wechat
    - semantics
    - parser
    - data-model
  compatibility: "Portable Agent Skills format with repository and fixture inspection tools."
  dependencies: []
---

# 微信语义解析 · WeChat Semantics

Turn unstable storage details into one canonical product meaning before any
surface decides how to render it.

## Triggers

### Activate when

- 用户问“这到底是什么微信消息”“为什么被识别成文件/视频/应用卡片”。
- 用户要求修复消息分类、发送者、目标人、时间、状态或正文来源。
- The user asks to model the WeChat message, review parser semantics, or fix message classification.

### Do not activate when

- 用户只调整已经正确分类的组件视觉，且共享语义契约已有回归证明。
- 用户只做数据库连接、密钥提取或文件恢复，不涉及产品含义。

## Canonical model

Every relevant object should resolve, as applicable, to:

- stable source identity;
- storage type, direct subtype, and nested types;
- canonical product type and semantic subtype;
- conversation, sender, target, direction, and ownership;
- display text source and structured payload;
- timestamp behavior and grouping role;
- actionability and interaction permissions;
- media/attachment identity;
- raw diagnostic payload;
- downstream presentation consumers.

## Workflow (MANDATORY)

### Step 1: Parse structure by hierarchy

- Prefer a real XML/JSON parser or hierarchy-aware extraction.
- Distinguish direct children from nested quoted, forwarded, or embedded types.
- Decode escaped inner payloads only at the layer that owns them.
- Preserve unknown fields instead of flattening them into misleading text.

### Step 2: Resolve identity and direction

- Separate database sender columns, group-content prefixes, current-user aliases,
  conversation identity, embedded participant IDs, and display names.
- Never substitute approximate contact/time/text matching for stable record identity.
- Distinguish “who stored/sent the event” from “who appears in the event text”.

### Step 3: Define canonical semantics

Write an explicit rule using positive structural evidence. For example:

- direct app type plus a required structured block;
- database type plus subtype and XML root;
- system template type plus resolved links;
- media type plus required attributes.

Avoid broad keyword-only classification. Keep a negative fixture for the nearest
ordinary message that must not match.

### Step 4: Define one presentation payload

The payload should expose only what all consumers need, such as text, subtype,
action label, participant roles, media metadata, and diagnostic source. Chat,
search, copy, export, analysis, and notifications must not re-parse raw XML with
independent rules.

### Step 5: Find the earliest broken layer

Report the first divergence among acquisition, decoding, identity, parsing,
canonical type, presentation, routing, visual grammar, interaction, and downstream
consumers. Fix that layer first, then remove or narrow compensating workarounds.

### Step 6: Specify regression fixtures

Include:

- exact positive raw fixture;
- nearest negative fixture;
- expected canonical type and payload;
- stable source identity and raw-data preservation;
- downstream expectations;
- version/platform notes.

## Dependencies

None. Use the target project's parsing libraries and test framework.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
