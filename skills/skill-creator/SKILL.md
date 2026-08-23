---
name: lov-skill-creator
description: >
  创建、验证并安装本地 Skill Publisher Skill 或 Skill Kit，并为每个新 Skill 固化真实案例、维度地图、定价依据和分发状态；当用户说“创建 skill”、"create a skill" 或 "scaffold skill kit" 时使用。
license: MIT
metadata:
  author: contributors
  version: "4.4.0"
  tags:
    - skill-creator
    - scaffold
    - local-install
    - skill-kit
    - skill-card
    - user-cases
  compatibility: "Python 3.8+ and PyYAML. Git is optional for local source history."
  dependencies: []
---

# lov-skill-creator

Create every Skill as a portable local source directory named `{name}-skill`,
bind it to the shared `user-profile/v1` contract, validate it, and install it
into the user's local agent skills directory as `lov-{name}`. Remote repositories, catalogs, marketplace packages,
uploads, and live-channel verification belong to `lov-skill-publisher`.

## Triggers

### Activate when

- 用户要“创建 skill”“封装成 skill”“生成 Skill Kit”或优化 Skill 生成机制。
- The user asks to create, scaffold, validate, or locally install an Agent Skill.

### Do not activate when

- 用户只是在调用现有 Skill 完成业务任务。
- 用户要发布远程仓库、上架目录、生成平台发行包或上传 Skill；交给 `lov-skill-publisher`。

## Architecture

```text
<configured local source root>/
└── {name}-skill/
    ├── SKILL.md
    ├── README.md
    ├── CHANGELOG.md
    ├── LICENSE
    ├── kit.yaml                 # Skill Kit only
    ├── skills/                  # embedded modules, Skill Kit only
    ├── scripts/                 # deterministic local CLIs
    ├── references/              # progressive disclosure
    └── assets/                  # reusable output assets
    ├── skill-card.yaml          # machine-readable trust/release record
    ├── skill-card.md            # human-readable Skill Card
    ├── cases/cases.json         # real Input → Prompt → Output evidence
    └── pricing-card.yaml        # value, boundary, and review basis

<agent skills directory>/
└── lov-{name} -> <local source root>/{name}-skill
```

Key rules:

- Creation ends with a validated, locally discoverable Skill.
- Source frontmatter name is `lov-{name}` and uses kebab-case.
- Source top-level fields are limited to `name`, `description`, `license`,
  `allowed-tools`, and `metadata`.
- Required modules live inside a Skill Kit; no external sibling dependencies.
- User-specific values come from flags, environment, or a portable profile.
- Every generated Skill declares and reads a shared user Profile across sessions;
  Skill-specific durable records live under `skills.<skill_id>.records`.
- A direct user statement about a durable preference or brand fact is persisted
  through the generated `scripts/profile_store.py` entrypoint and reported back.
- Every new Skill carries a real user case, a dimension map, a pricing basis,
  and explicit paid/free distribution states. A scaffold is incomplete until
  those records are filled and validated.
- Skill Publisher is a possible profile value, never a separate implementation mode.
- Do not create remotes, releases, catalogs, platform packages, or uploads here.

## Creation Workflow

### Step 1: Infer the product shape

Use the request, memory, repository, and supplied examples before asking
anything. Ask one question at a time only when a missing answer changes the
user-visible outcome. Never ask users to choose technical machinery.

Record these decisions internally:

1. Problem, supported input, and concrete output.
2. Two or three realistic examples and Chinese plus English trigger phrases.
3. Internal context versus content that belongs in the final user-facing result.
4. Public layer versus protected logic, prompts, keys, rules, or data.
5. The first real user case: input, minimum prompt/brief, output, and evidence
   assets. Do not manufacture a case or score to make the card look complete.

Background details, personal names, and competitor observations are context by
default. Include them in generated products only when they serve the end user.

### Step 2: Infer implementation and composition

Choose automatically and briefly state the result:

- **Cloud handler** — sensitive proprietary logic must stay off the user's disk.
- **Instruction-only** — judgment, research, conversation, or generation has no
  useful deterministic local transform.
- **Python CLI** — repeatable parsing, conversion, validation, packaging, or
  file generation benefits from deterministic execution.
- **Single Skill** — one outcome, or several modes sharing the same context.
- **Skill Kit** — two or more independently useful stages with their own
  input/output contracts are composed through named pipelines.

Scripts alone do not justify a Kit. Prefer Single when modularity is marginal.
For a Kit, list module IDs and named pipeline order before scaffolding.

### Step 2.5: Analyze the nearby Skill group before creating a new one

Before scaffolding, inspect the local Skill source root and installed Skill
catalog for related capabilities, using their routing descriptions and actual
input/output contracts rather than names alone. Record the outcome in
`references/skill-composition.md` for every generated Skill.

Classify each relevant Skill as one of:

- **upstream atom** — independently produces an approved input for this Skill;
- **core atom** — this new Skill owns the requested user-visible outcome;
- **downstream atom** — independently consumes the verified output;
- **overlap** — owns the same outcome and should be extended or selected instead
  of duplicated; or
- **not composed** — adjacent in topic but adds no meaningful handoff.

For each proposed handoff, state the concrete artifact or contract, the
invocation boundary, and who owns the final acceptance criterion. Do not create
an external sibling dependency merely because another Skill is related. If
multiple stages are required for one user-visible outcome, embed them as a
self-contained Skill Kit; otherwise keep the new Skill standalone and describe
optional handoffs explicitly. A no-composition conclusion is valid only after
the nearby group was inspected.

### Step 3: Declare the user Profile contract — always

Every new Skill receives a `skill.yaml` declaration for `user-profile/v1`, even
when its first invocation has no missing configuration. This is the cross-session
connection point for:

- user identity, language, timezone, and working defaults;
- brand name, website, logo, tone, profile, and design guidance;
- workspace/project roots and output locations;
- Skill-specific defaults and durable records.

The generated contract reads the shared Profile and writes direct user
statements into `skills.<skill_id>.records` (or the shared `user` / `brand`
scope when the value is explicitly global). It uses this precedence:

1. Explicit CLI flags or current request.
2. Environment variables.
3. Shared profile JSON.
4. Safe inferred defaults.
5. Ask once for only the remaining user-facing values.

When the user directly states a value intended for future sessions, run the
generated `scripts/profile_store.py record ... --confirm` command and report the
canonical saved path. Inferred values stay in the current request context.

Every generated Skill remains portable. Never introduce an author-only or
Skill Publisher-only branch; different users supply different profile values.

### Step 4: Plan contents

- Deterministic operations → `scripts/` as standalone `argparse` CLIs.
- Domain knowledge → `references/`.
- Reused output files, templates, fonts, or icons → `assets/`.
- Independently triggerable stages → embedded `skills/` plus `kit.yaml`.
- User Profile contract → `skill.yaml`, `references/user-profile.md`, and the
  standalone `scripts/profile_store.py` reader/writer; this is always generated.
- Skill trust evidence → `skill-card.yaml`, `skill-card.md`,
  `cases/cases.json`, and `pricing-card.yaml`.
- Skill group decision → `references/skill-composition.md`, including nearby
  Skills inspected, atomic handoffs, overlap decisions, and the final
  Single-versus-Kit rationale.

Python scripts must be standalone files without package scaffolding. Treat CJK
text handling as a core requirement for document and content workflows.

### Step 5: Initialize locally

Single Skill:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" <name> \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

Skill Kit:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" <name> \
  --kit \
  --module <module-a> \
  --module <module-b> \
  --install-dir "$SKILL_SKILLS_INSTALL_DIR"
```

Resolve the install directory from an explicit flag, environment variable,
shared profile, or the active agent runtime. If it remains unknown, ask once.
The initializer must reject an occupied install target instead of overwriting it.

For cloud-split implementations, read `references/cloud-split.md` completely
before coding. Keep real logic in the configured cloud handler, return minimal
symbolic payloads, render symbols locally, and complete its mandatory preflight
audit. Cloud deployment itself is an external publication step when applicable.

### Step 6: Implement

Write the source as instructions for an agent, not as notes about this chat:

- `description` is the routing contract: outcome, inputs, and natural Chinese
  plus English triggers in 50–200 characters.
- Add `## Triggers`, activation examples, and adjacent non-trigger conditions.
- Keep `SKILL.md` below 500 lines; move detail to relevant references.
- Put compatibility, version, tags, and dependencies under `metadata`.
- Keep the NVIDIA-compatible required card fields intact, then add LovStudio's
  user case, dimension map, pricing basis, and distribution fields.
- Keep external Skills optional unless they are embedded Kit modules; expose
  artifact-level handoffs instead of hidden cross-Skill coupling.
- Use `AskUserQuestion` only for unresolved user-facing product decisions.
- Never hard-code private paths or personal brand data in reusable source.
- Fill missing visual/content assets with clearly appropriate generated
  material when the workflow permits; ask for originals only when authenticity
  materially affects the result.

Human-facing `README.md` includes a matching version badge, local installation,
the Profile contract, examples, dependencies, and quality gate.

### Step 7: Validate and install

```bash
python3 scripts/validate_skill.py .
```

Completion requires:

1. Validation passes with standard YAML.
2. Every module, local reference, script, and asset resolves.
3. No unresolved placeholders, private absolute paths, cache files, or compiled
   Python artifacts remain.
4. The local install path resolves to this source directory.
5. A documented activation phrase works and a non-trigger stays outside scope.
6. Every Skill Kit module and at least one named pipeline are exercised.
7. Every new Skill has at least one verified Input → Prompt → Output case,
   three or more named dimensions with evidence, a pricing basis, and explicit
   paid/free channel states.
8. `references/skill-composition.md` records the inspected Skill group, atomic
   handoffs or overlap decision, and why the result is a Single Skill or Kit.

Stop at the local result unless the user also requests publication. When they
do, invoke `lov-skill-publisher` with the validated source path and requested
channels; do not duplicate publishing logic in this Skill.

## Design Patterns

### Context-aware prefill

1. Read the request, conversation, memory, and current project.
2. Prefill all supported fields.
3. Infer implementation and configuration modes.
4. Ask only for missing information that changes the user-facing outcome.

### Progressive disclosure

Keep the controller lean. Split large theme systems, APIs, examples, platform
contracts, and asset catalogs into directly referenced files.

## Exclusions

- Remote repository creation, pushes, releases, catalogs, marketplace packages,
  platform uploads, and live publication checks.
- `INSTALLATION_GUIDE.md`; installation belongs in `README.md`.
- Test-framework scaffolding for instruction-only Skills.
- `__pycache__`, compiled Python files, `.DS_Store`, or unresolved placeholders.
- User-specific absolute paths or an internal-only product mode.

For source templates see `references/templates.md`. For the Skill Card contract
see `references/skill-card-standard.md`. For the Profile contract see
`references/user-profile.md`. Historical migrations remain in
`references/migration.md`.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、Skill 专属记录、个人 Preferences、品牌/用户 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存用户与品牌的共享资料，`skills.<skill_id>.records` 保存本 Skill 的持久化记录。
- 用户直接说出的长期偏好或品牌事实，通过 `scripts/profile_store.py` 原子写回 Profile，并在结果中报告保存路径。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
