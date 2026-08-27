---
name: lov-skill-publisher
description: >
  Publish or submit a validated Skill. Default to the LovStudio official
  website, run lov-skill-pricing automatically, and use other channels only
  when explicitly named.
license: MIT
compatibility: >-
  Requires Python 3.8+, PyYAML, git and GitHub CLI for the Skill Publisher
  adapter. Channel credentials stay in environment variables or credential
  stores; generated metadata and archives stay outside canonical source.
metadata:
  author: contributors
  version: "0.7.2"
  tags:
    - skill-publisher
    - release
    - marketplace
    - workbuddy
    - skillpay
  dependencies:
    - lov-skill-pricing
---

# lov-skill-publisher

Publish one validated local Skill source to the LovStudio official website or
explicitly selected additional channels. When the user does not specify a
channel, run only the Skill Publisher website adapter. Always auto-price first,
keep channel metadata and generated packages outside canonical source, and
report evidence per selected channel.

## Triggers

### Activate when

- 用户说“发布这个 Skill”“上架 Skill Publisher”“生成 WorkBuddy 包”或“分发到多个平台”。
- The user asks to publish, release, distribute, upload, or package an existing Skill.

### Do not activate when

- 用户要创建、实现、修改或仅在本地安装 Skill；交给 `lov-skill-creator`。
- 用户只是在调用某个业务 Skill，而不是发布它。

## Product boundary

- Input is a local Skill source that already passes source validation.
- When no channel is specified, select only **Skill Publisher**, the LovStudio
  official website adapter.
- Explicitly named channels narrow the run; do not ask a channel-selection question
  when the request omits channel parameters.
- Run every supported adapter only when the user explicitly says “全部渠道”,
  “多平台”, “all channels”, or names every intended channel.
- A request may select multiple channels in one run.
- Pricing, visibility, protection, licensing, and target accounts are publishing
  inputs. Reuse context when known and ask only for values required by a target.
- A license scope named `global` or `all` is a dynamic entitlement to every
  currently listed Skill for the license lifetime. Never publish or migrate it
  as a frozen list of current Skill IDs; explicit per-Skill grants remain fixed.
- Every publish run invokes `lov-skill-pricing` by default to create or refresh one
  evidence-backed Pricing Card per Skill before channel preparation. An explicit
  user price is a constraint for that pricing pass, not a reason to skip it.
- Keep the canonical Pricing Card in publisher profile/output storage. Transform
  only its public fields into catalogs, packages, or submission forms; do not add
  channel state or generated cards to canonical Skill source.
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

### Step 2: Auto-price the Skill

Use `lov-skill-pricing` for every source, even when the user only says “发布” or
selects a channel without mentioning price.

1. Pass the validated source, version, delivery unit, real result evidence,
   maintenance/support conditions, selected channels, and any existing price or
   `pricing-card.yaml` into the pricing workflow.
2. Let the pricing workflow use explicit assumptions when cost/value inputs are
   missing. Ask at most one focused question only when the missing field changes
   the commercial model; ordinary missing estimates must not block publication.
3. If the user supplied a public price, currency, free/paid status, or billing
   model, preserve it as a hard publishing constraint and have the Pricing Card
   explain any difference from its model recommendation.
4. Record recommended price, launch price, stable range, billing model, channel,
   cost floor, value anchor, weighted score, confidence, evidence gaps, and review
   trigger outside canonical source.
5. Reuse this one price contract across selected adapters. Skill Publisher maps
   it into catalog pricing metadata and its public Pricing Card; SkillPay uses the
   public CNY price; installation-only channels use the free/paid funnel and
   upgrade path without inventing a separate price.

Do not hand-author an unexplained price inside a channel adapter. If automatic
pricing cannot run, mark pricing `blocked` with the missing Skill/resource and do
not submit a paid listing with an inferred number.

### Step 3: Resolve channels and release model

If channels are explicit, proceed without another distribution question. If no
channel is named, select only Skill Publisher and proceed without asking the
user to choose a channel. Expand to all supported adapters only after an explicit
all-channel or multi-platform request.

For each selected channel, resolve only required fields:

- public/private visibility and free/paid catalog status where supported;
- paid delivery mode: protected encrypted bundle or explicitly public source;
- organization, account, catalog, or output location;
- platform metadata, icon, examples, and source locator;
- requested version versus current source version.

Do not ask users to choose implementation details such as staging layout,
validation commands, archive format, or adapter order.

### Step 4: Build a per-channel plan

Read `references/channels.md`, then load only the selected channel references.
Keep independent state for each target so one failure does not masquerade as a
successful multi-channel release.

### Step 5: Publish Skill Publisher

Read `references/publishing.md` completely. Execute the source repository,
release, catalog, cache refresh, and live verification workflow. Publication is
complete only when the expected version and release-specific content are visible
on the live detail page and the catalog's exact install command succeeds through
the declared delivery mode. A paid catalog entry without either a verified
encrypted bundle or explicit `public_source: true` is blocked, not published.
When a catalog refresh adds or delists a Skill, verify that dynamic `global`/`all`
licenses immediately gain or lose catalog access without granting or spending
Credits. This entitlement check is part of publication, not a later migration.

### Step 6: Publish WorkBuddy through CodeBuddy

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

### Step 7: Submit Alipay SkillPay

Read `references/skillpay.md` completely. Build a clean product ZIP outside the
canonical source, keep the current Pricing Card price as the single public CNY
price, then upload and wait for parsing to finish before submitting. Record the
product title, package checksum, public price, submission result, and current
review state. A parsed archive is only `uploaded`; a success notice after form
submission is `review` until the marketplace marks the product live.

### Step 8: Additional platform adapter

Use the adapter contract in `references/channels.md`. Research current official
documentation, implement deterministic preparation/validation scripts when
useful, and define an observable completion gate. Never reuse another channel's
metadata or call an upload dialog a completed publication.

### Step 9: Multi-channel report

Report each target separately:

| Channel | State | Version/artifact | Evidence | Follow-up |
|---------|-------|------------------|----------|-----------|
| TARGET | prepared/published/verified | VALUE | URL or local path | ACTION |

Use precise states. `prepared`, `uploaded`, `installed`, `listed`, and `live`
represent different outcomes.

## Dependencies

- Python 3.8+
- PyYAML
- `lov-skill-pricing` for the default pre-publish Pricing Card
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

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
