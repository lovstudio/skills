---
name: lov-wechat-evidence
description: >
  为微信体验差异建立可追溯证据集，关联官方表现、当前产品、原始记录、代码路径与版本环境；适用于“先确认微信官方怎么表现”、"review the WeChat reference" 或 parity evidence audit。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  tags:
    - wechat
    - evidence
    - product-research
  compatibility: "Portable Agent Skills format with local repository and optional image or web inspection."
  dependencies: []
---

# 微信行为取证 · WeChat Evidence

Build the smallest evidence set that can distinguish appearance, product
semantics, storage shape, and runtime behavior.

## Triggers

### Activate when

- 用户说“先确认微信官方怎么表现”“对比这两张微信截图”“查清这个消息类型”。
- 用户提供截图、XML、数据库行、版本号或运行时入口，要求建立差异证据。
- The user asks to review the WeChat reference, compare official behavior, or build a parity evidence set.

### Do not activate when

- 用户只要最终 CSS 数值且已有完整、已验证的体验契约。
- 用户只要泛化的竞品研究，不涉及微信产品行为或具体实现入口。

## Workflow (MANDATORY)

### Step 1: Anchor to exact inputs

- Open the supplied screenshot or artifact first.
- Preserve exact database/table/row identity when available.
- Record target surface, WeChat platform/version, theme, viewport, conversation
  kind, direction, and state.
- Confirm current worktree, route, process, or build when runtime evidence matters.

### Step 2: Separate evidence classes

Capture these independently:

1. `official_reference` — observed WeChat behavior and source context;
2. `product_observation` — current rendered behavior;
3. `raw_record` — XML/JSON/database/event structure;
4. `implementation` — parser, model, renderer, style, downstream consumers;
5. `runtime` — actual message path, device/app state, and observation;
6. `inference` — a hypothesis awaiting proof.

Do not use a screenshot to infer storage type or use raw XML to infer exact pixel
layout. Label platform/version uncertainty explicitly.

### Step 3: Extract observable grammar

For each reference, record:

- position, grouping, hierarchy, spacing, alignment, typography, color, surface;
- avatar, sender name, bubble, timestamp, icon, badge, menu, and affordance presence;
- normal, hover, pressed, focus, loading, disabled, error, missing-content states;
- keyboard, selection, context menu, copy, open, retry, and accessibility behavior;
- what is absent, because forbidden artifacts often reveal the wrong component.

### Step 4: Trace repository consumers

Locate the acquisition, decoding, parser, canonical type, presentation helper,
component, CSS, search, copy, export, analysis, and diagnostic paths. Prefer exact
symbols and focused searches over broad repository scans.

### Step 5: Produce an evidence ledger

Return a compact ledger with:

- confirmed observations;
- version/platform scope;
- raw structural facts;
- product differences;
- affected code and downstream surfaces;
- open questions or evidence gaps;
- the next semantic decision required.

## Dependencies

None. Use local image inspection and repository tools first. Use current primary
web sources only when official behavior is unclear or may have changed.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
