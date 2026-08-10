---
name: lov-skill-publisher
description: >
  Use when the user asks to publish a validated local Skill to one or more
  channels, including “发布这个 Skill”、“上架 Skill Publisher”、"publish this skill"、
  "package for WorkBuddy" 或“提交 SkillPay”。
license: MIT
metadata:
  author: contributors
  version: "0.3.1"
  tags:
    - skill-publisher
    - release
    - marketplace
    - workbuddy
    - skillpay
  dependencies: []
---

# lov-skill-publisher

Publish one validated local Skill source to one or more publishing channels. When
the user does not specify a channel, run every supported adapter by default. Keep
channel metadata and generated packages outside canonical source, execute each
adapter independently, and report evidence per channel.

## Triggers

### Activate when

- 用户说“发布这个 Skill”“上架 Skill Publisher”“生成 WorkBuddy 包”或“分发到多个平台”。
- The user asks to publish, release, distribute, upload, or package an existing Skill.

### Do not activate when

- 用户要创建、实现、修改或仅在本地安装 Skill；交给 `lov-skill-creator`。
- 用户只是在调用某个业务 Skill，而不是发布它。

## Product boundary

- Input is a local Skill source that already passes source validation.
- When no channel is specified, select every supported adapter by default.
- Explicitly named channels narrow the run; do not ask a channel-selection question
  when the request omits channel parameters.
- A request may select multiple channels in one run.
- Pricing, visibility, protection, licensing, and target accounts are publishing
  inputs. Reuse context when known and ask only for values required by a target.
- Channel metadata, credentials, staging files, and archives stay outside source.

Supported adapters in this version:

- **Skill Publisher** — source repository, release, catalog, cache refresh, and live page.
- **WorkBuddy（CodeBuddy 开放平台）** — 生成独立 Skill ZIP，并在控制台上传、解析、填写上架信息和提交审核。
- **Alipay SkillPay** — validated product ZIP, explicit CNY price, upload, parse,
  submission, and observable review state.

For any additional platform, follow `references/channels.md` and verify its
current official name, submission contract, public URL, and completion signal
before implementing an adapter.

## User Configuration

Publishing inherently needs persistent target settings. Initialize them on first
use through `references/user-config.md`, while keeping tokens in environment or
credential stores rather than committed profiles.

## Workflow (MANDATORY)

### Step 0: Resolve roots and settings

- Resolve this Skill as `SKILL_DIR`.
- Resolve the source from an explicit path, current directory, or conversation.
- Resolve target settings from flags, environment, and shared profile.
- Verify referenced scripts and channel documents before external changes.

### Step 1: Validate canonical source

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" SOURCE --target source
```

Check that source has no platform metadata directory or generated release
artifacts. Record name, version, description, modules, dependencies, git state,
and whether a remote already exists.

### Step 2: Resolve channels and release model

If channels are explicit, proceed without another distribution question. If no
channel is named, select all supported adapters and proceed without asking the
user to choose a channel.

For each selected channel, resolve only required fields:

- public/private visibility and free/paid catalog status where supported;
- organization, account, catalog, or output location;
- platform metadata, icon, examples, and source locator;
- requested version versus current source version.

Do not ask users to choose implementation details such as staging layout,
validation commands, archive format, or adapter order.

### Step 3: Build a per-channel plan

Read `references/channels.md`, then load only the selected channel references.
Keep independent state for each target so one failure does not masquerade as a
successful multi-channel release.

### Step 4: Publish Skill Publisher

Read `references/skill-publisher.md` completely. Execute the source repository,
release, catalog, cache refresh, and live verification workflow. Publication is
complete only when the expected version and release-specific content are visible
on the live detail page.

### Step 5: Publish WorkBuddy through CodeBuddy

Read `references/workbuddy.md` completely. Keep connector metadata and icon in a
publisher profile outside source, then run:

```bash
python3 "$SKILL_DIR/scripts/build_workbuddy.py" SOURCE \
  --meta CONNECTOR_META \
  --icon ICON \
  --output-dir OUTPUT_DIR
```

Record source validation, package validation, archive listing, checksum, module
count, and output paths. Then follow `references/workbuddy.md`: upload each
individual ZIP to `https://www.codebuddy.cn/open/console/dashboard`, wait for
“解析成功”, fill user-facing Chinese/English listing fields, and submit it.
Record the review state separately from public listing evidence.

### Step 6: Submit Alipay SkillPay

Read `references/skillpay.md` completely. Build a clean product ZIP outside the
canonical source, keep the requested price as the single public CNY price, then
upload and wait for parsing to finish before submitting. Record the product
title, package checksum, requested price, submission result, and current review
state. A parsed archive is only `uploaded`; a success notice after form
submission is `review` until the marketplace marks the product live.

### Step 7: Additional platform adapter

Use the adapter contract in `references/channels.md`. Research current official
documentation, implement deterministic preparation/validation scripts when
useful, and define an observable completion gate. Never reuse another channel's
metadata or call an upload dialog a completed publication.

### Step 8: Multi-channel report

Report each target separately:

| Channel | State | Version/artifact | Evidence | Follow-up |
|---------|-------|------------------|----------|-----------|
| TARGET | prepared/published/verified | VALUE | URL or local path | ACTION |

Use precise states. `prepared`, `uploaded`, `installed`, `listed`, and `live`
represent different outcomes.

## Dependencies

- Python 3.8+
- PyYAML
- `git` and `gh` for GitHub-backed publication
- Target-specific credentials resolved without printing secrets

## Local development

Validate this publisher Skill with:

```bash
python3 scripts/validate_skill.py . --target source
```

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
