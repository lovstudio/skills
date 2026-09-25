---
name: dsh-search-or-create-plugin
description: >
  Search the plugin gateway, analyze which DSH plugin best fits a goal, then use
  it or design a new plugin from the closest open source. 触发：选插件还是新建 / 插件够用吗 / pick or create a plugin.
license: MIT
metadata:
  author: Lovstudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - dsh-plugin
    - search
    - decision
    - create
    - gateway
    - deepseek-harness
  compatibility: "Portable Agent Skills format. Requires Python 3.8+ (stdlib only) and network access to api.dshfind.com; the create path optionally hands off to the dsh-plugin-creator skill."
  dependencies: []
---

# 插件选型顾问 · Plugin Advisor

针对用户目标从 dshfind 网关检索候选插件，按能力覆盖、成熟度、健康风险、集成可行性与来源可信五个维度分析适配度，给出每个候选的 MATCH / PARTIAL / NO-MATCH 结论与证据；有匹配就给出采用路径，否则产出基于最近开源实现的新插件方案并交给 dsh-plugin-creator。

## Triggers

### Activate when

- 用户说“帮我找个能 XX 的插件，够用就用，不够就新建”“这个需求有现成插件吗”“选哪个插件好”“插件够用吗”。
- The user asks to decide whether an existing plugin covers a need or a new one must be built, e.g. "should I use an existing plugin or create one for X".
- 用户给出目标并希望得到可执行的结论：采用某个插件（含使用路径）或新建插件（含基于的开源实现）。

### Do not activate when

- 用户只要求候选清单与证据；交给 dsh-search-plugin。
- 用户已明确决定新建插件；直接进入 dsh-plugin-creator。
- 用户要发布插件；交给 dsh-plugin-publisher。
- 用户要找的是通用 Agent Skill 而不是 DSH 插件；交给 find-skills。

## User Profile (cross-session)

This Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and the
`skills.dsh-search-or-create-plugin` namespace at the start of every run. Keep
the source portable: resolved personal values belong in the shared profile,
never here.

When the user directly states a durable preference, persist it through
`scripts/profile_store.py` and report the saved profile path. Skill-specific
values live under `records.<field>`; use `brand.<field>` or `user.<field>` for
shared values. Do not persist inferred secrets or credentials. See
`references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The search stage is embedded in this source to
stay self-contained; `dsh-plugin-creator` is an optional downstream handoff for
the create path, never a hidden runtime dependency.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it; otherwise infer the installed
  skill directory from the current skill context.
- Verify `scripts/search_plugin.py`, `references/gateway-api.md`, and
  `references/fit-analysis.md` exist before work; if a resource is missing,
  name its expected relative path and stop.
- Resolve `context.profile` on every invocation. Precedence: current request,
  project context, Skill records, shared preferences, shared user/brand
  profile, safe defaults. A direct user statement about a durable preference
  should be saved with `scripts/profile_store.py record` using `--confirm`,
  followed by a concise saved-path report.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/dsh-search-or-create-plugin"
```

### Step 1: Understand the requested outcome

- Extract the goal's core verbs and objects, the constraints (grade floor,
  install preference such as npm or git, language, output language), and who
  consumes the result.
- Confirm the deliverable: a decision report that either adopts a plugin with a
  usage path, or produces a new-plugin brief based on the closest open source.

### Step 1.5: Analyze nearby Skills before implementation

- Inspect `references/skill-composition.md`. `dsh-search-plugin` is a sibling
  whose search procedure is embedded below; `dsh-plugin-creator` is the
  optional downstream atom that consumes the new-plugin brief. No hidden
  sibling dependency.

### Step 2: Search the gateway for candidates

1. Derive 2-4 short keywords from the goal; the gateway needs at least two
   trimmed characters per keyword. An optional prior `dsh-search-plugin` JSON
   artifact from an earlier session may be reused when the user provides one;
   otherwise run the embedded procedure below.
2. Run the deterministic client:

```bash
python3 "$SKILL_DIR/scripts/search_plugin.py" search "vision" --limit 10 --pretty
python3 "$SKILL_DIR/scripts/search_plugin.py" suggest "vision"
```

3. Apply constraints as filters, then fetch detail for the candidates that
   look central:

```bash
python3 "$SKILL_DIR/scripts/search_plugin.py" search "feishu" --grade B --min-score 60 --limit 10
python3 "$SKILL_DIR/scripts/search_plugin.py" detail owner repo
```

4. On weak results, retry with synonyms or the category facet per
   `references/gateway-api.md` before concluding anything about absence.

### Step 3: Fit analysis

- Score each candidate against the five dimensions in
  `references/fit-analysis.md`: 能力覆盖 capability coverage, 成熟度 maturity,
  健康与风险 health and risk, 集成可行性 integration, 来源可信 provenance.
- Assign each candidate a verdict: MATCH, PARTIAL, or NO-MATCH, and cite the
  gateway fields that support it (description evidence, score, grade, stars,
  pushed_at, install.kind, is_risky, risk_note, is_plugin, is_official).
- A null score or grade is unrated, not a failure; rely on stars, pushed_at,
  description, and install evidence in that case.

### Step 4: Decide use or create

- When at least one candidate is MATCH: recommend the best one, give the
  concrete usage path derived from `install` (npm package name, git repository
  mount, or release artifact per `references/gateway-api.md`), and state the
  acceptance check the user can run to confirm coverage.
- When candidates are only PARTIAL: present the trade-off between composing
  existing candidates and extending the closest one; ask the user one focused
  question before proceeding.
- When no candidate covers the core capability (NO-MATCH): produce a
  new-plugin brief with goal, required capabilities, the closest open-source
  base implementations (full_name, repository_url, why each is the base), and
  the gaps to implement. Save the brief under `workspace.output_dir` as
  `new-plugin-brief-<slug>.md` and report the path.
- Create path handoff: when the user approves, invoke the optional downstream
  atom `dsh-plugin-creator` with the brief; it owns the package authoring
  outcome. Publishing afterwards is `dsh-plugin-publisher`.

### Step 5: Validate the deliverable

- Verify every verdict cites gateway fields fetched in this run or the saved
  artifact; report evidence gaps explicitly.
- Verify the usage path is derivable from `install` fields and the repository
  README, not invented.
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as
  the standard trust bundle for this Skill.

## References

- `references/gateway-api.md` — verified endpoint contract for the dshfind gateway.
- `references/fit-analysis.md` — the five-dimension fit rubric and verdict rules.
- `references/skill-composition.md` — nearby Skill group and handoff analysis.
- `references/user-profile.md` — the shared `user-profile/v1` contract.

## Dependencies

- Python 3.8+ (stdlib only) and network access to `https://api.dshfind.com`
  (public, no auth).
- The OpenAPI document is published at
  `https://dshfind.lovstudio.ai/openapi.json`; it describes the same endpoints.
- Optional downstream handoffs: `dsh-plugin-creator` for the create path,
  `dsh-plugin-publisher` for publishing. Neither is required to run this Skill.
