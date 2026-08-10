---
name: sgc-skill-creator
description: >
  创建、验证并安装本地 LovStudio Skill 或 Skill Kit；当用户说“创建 skill”、
  “封装成 skill”、"create a skill" 或 "scaffold skill kit" 时使用。
license: MIT
metadata:
  author: lovstudio
  version: "4.0.0"
  tags:
    - skill-creator
    - scaffold
    - local-install
    - skill-kit
  compatibility: "Python 3.8+ and PyYAML. Git is optional for local source history."
  dependencies: []
---

# sgc-skill-creator

Create every Skill as a portable local source directory named `{name}-skill`,
validate it, and install it into the user's local agent skills directory as
`sgc-{name}`. Remote repositories, catalogs, marketplace packages,
uploads, and live-channel verification belong to `sgc-skill-publisher`.

## Triggers

### Activate when

- 用户要“创建 skill”“封装成 skill”“生成 Skill Kit”或优化 Skill 生成机制。
- The user asks to create, scaffold, validate, or locally install an Agent Skill.

### Do not activate when

- 用户只是在调用现有 Skill 完成业务任务。
- 用户要发布远程仓库、上架目录、生成平台发行包或上传 Skill；交给 `sgc-skill-publisher`。

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

<agent skills directory>/
└── sgc-{name} -> <local source root>/{name}-skill
```

Key rules:

- Creation ends with a validated, locally discoverable Skill.
- Source frontmatter name is `sgc-{name}` and uses kebab-case.
- Source top-level fields are limited to `name`, `description`, `license`,
  `allowed-tools`, and `metadata`.
- Required modules live inside a Skill Kit; no external sibling dependencies.
- User-specific values come from flags, environment, or a portable profile.
- LovStudio is a possible profile value, never a separate implementation mode.
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

### Step 3: Infer user initialization — NEVER ASK FOR THE MODE

Enable a user profile when the Skill needs persistent values across runs:

- workspace or project roots;
- identity, brand, audience, locale, or design guide;
- default output directories;
- model, provider, or integration preferences.

Use no profile when every required input/output is explicit per invocation and
the current directory is a sound default. If a profile is needed, scaffold the
first-run initialization flow automatically with this precedence:

1. Explicit CLI flags or current request.
2. Environment variables.
3. Shared profile JSON.
4. Safe inferred defaults.
5. Ask once for only the remaining user-facing values, then persist with the
   user's knowledge.

Every generated Skill remains portable. Never introduce an author-only or
LovStudio-only branch; different users supply different profile values.

### Step 4: Plan contents

- Deterministic operations → `scripts/` as standalone `argparse` CLIs.
- Domain knowledge → `references/`.
- Reused output files, templates, fonts, or icons → `assets/`.
- Independently triggerable stages → embedded `skills/` plus `kit.yaml`.
- Persistent user settings → `references/user-config.md` and initialization
  instructions; add them only when Step 3 says they are needed.

Python scripts must be standalone files without package scaffolding. Treat CJK
text handling as a core requirement for document and content workflows.

### Step 5: Initialize locally

Single Skill without persistent configuration:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" <name> \
  --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
```

Skill Kit with inferred user configuration:

```bash
python3 "$SKILL_DIR/scripts/init_skill.py" <name> \
  --kit \
  --module <module-a> \
  --module <module-b> \
  --user-config \
  --install-dir "$LOVSTUDIO_SKILLS_INSTALL_DIR"
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
- Use `AskUserQuestion` only for unresolved user-facing product decisions.
- Never hard-code private paths or personal brand data in reusable source.
- Fill missing visual/content assets with clearly appropriate generated
  material when the workflow permits; ask for originals only when authenticity
  materially affects the result.

Human-facing `README.md` includes a matching version badge, local installation,
configuration only when applicable, examples, dependencies, and quality gate.

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

Stop at the local result unless the user also requests publication. When they
do, invoke `sgc-skill-publisher` with the validated source path and requested
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

For source templates see `references/templates.md`. For configuration rules see
`references/user-config.md`. Historical migrations remain in
`references/migration.md`.
