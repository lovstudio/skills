---
name: lov-wechat-ui-parity
description: >
  在既有设计系统内实现微信官方的消息层级、组件语义、交互状态与视觉密度；适用于“按微信官方改这个组件”“还原微信聊天体验”、"build the WeChat UI behavior" 或 fix official UI parity。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  tags:
    - wechat
    - uiux
    - frontend
    - interaction-design
  compatibility: "Portable Agent Skills format with target frontend repository tools."
  dependencies: []
---

# 微信界面还原 · WeChat UI Parity

Express canonical WeChat meaning through the product's existing visual system
without introducing a parallel component language.

## Triggers

### Activate when

- 用户说“按微信官方改这个组件”“还原微信聊天体验”“头像/气泡/菜单语义不对”。
- 用户给出已经明确分类的微信对象及官方参考，要求实现交互和视觉表现。
- The user asks to build the WeChat UI behavior, fix official UI parity, or refine a WeChat-compatible component.

### Do not activate when

- 原始消息仍未正确分类，或者参与者、状态和正文来源尚未确定；先运行语义模块。
- 用户要品牌官网、海报或不以微信体验为基准的独立视觉创作。

## Workflow (MANDATORY)

### Step 1: Map meaning to component grammar

Classify the object before styling:

- user-authored message;
- system event or timeline separator;
- rich card or embedded content;
- media object;
- status, action, toggle, navigation, selection, or destructive control;
- transient feedback or diagnostic state.

Use the adjacent shared primitive whenever the same meaning already exists.

### Step 2: Match official hierarchy

Compare and implement:

- alignment and conversation-flow ownership;
- avatar, sender label, bubble, surface, tail, icon, timestamp, and metadata;
- typography, line height, wrapping, emoji baseline, spacing, radius, and color;
- grouping across neighboring messages and time gaps;
- long content, missing assets, unknown type, loading, failure, and deletion states.

Absence is part of the contract. Do not show an avatar, bubble, title, chip, or
button merely because the generic message component has one.

### Step 3: Preserve product consistency

- Reuse tokens and primitives; add the smallest semantic modifier needed.
- Keep peer actions in one control grammar. Move crowded secondary actions into
  an extensible menu.
- Keep explanatory copy in secondary text, tooltip, popover, or diagnostic detail.
- Do not expose reverse-engineering intent or raw protocol language in user copy.
- Make error detail copyable and include stable debug context.

### Step 4: Implement interaction states

Verify normal, hover, focus, pressed, selected, loading, disabled, error, and
missing-content states. Preserve keyboard order, accessible names, selection,
context menu behavior, link safety, and IME composition for any input.

### Step 5: Update all semantic consumers

When the same presentation appears in search, copy, export, notification,
analysis, or archive views, reuse the shared payload and keep intentional surface
differences explicit. Avoid independent XML parsing inside components.

### Step 6: Prepare visual acceptance

Capture or describe exact comparison states at the narrowest supported container
and normal desktop width. Include adjacent messages when grouping, time, avatar,
or background context affects meaning.

## Dependencies

No fixed UI library. Use the target repository's design system, accessibility
primitives, localization, and responsive conventions.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
