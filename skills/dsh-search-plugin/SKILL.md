---
name: dsh-search-plugin
description: >
  Search the public dshfind plugin gateway and return ranked, evidence-tagged
  DSH plugins matching a goal. 触发：查找 DSH 插件 / 搜索插件 / find a plugin / search plugins.
license: MIT
metadata:
  author: Lovstudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - dsh-plugin
    - search
    - gateway
    - dshfind
    - deepseek-harness
  compatibility: "Portable Agent Skills format. Requires Python 3.8+ (stdlib only) and network access to api.dshfind.com; the gateway is public and needs no auth."
  dependencies: []
---

# 插件雷达 · Plugin Radar

针对用户目标从 dshfind 插件网关检索 DSH 插件，返回带证据的候选清单：官方评分与等级、星标、分类、标签、安装方式、风险标记和仓库链接，并附上数据版本与时间戳溯源。

## Triggers

### Activate when

- 用户说“查找插件”“搜索 DSH 插件”“有没有现成的 XX 插件”“帮我找找实现 XX 的插件”。
- The user asks to find or search plugins, e.g. "find a plugin for memory", "search plugins for web automation".
- 用户只想要候选清单与证据，暂不决定选用还是新建。

### Do not activate when

- 用户要直接安装或使用某个插件；那是 dsh 运行时或下游流程的事。
- 用户要新建插件；交给 dsh-plugin-creator。
- 用户要发布插件；交给 dsh-plugin-publisher。
- 用户要找的是通用 Agent Skill 而不是 DSH 插件；交给 find-skills。

## User Profile (cross-session)

This Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and the
`skills.dsh-search-plugin` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference, persist it through
`scripts/profile_store.py` and report the saved profile path. Skill-specific
values live under `records.<field>`; use `brand.<field>` or `user.<field>` for
shared values. Do not persist inferred secrets or credentials. See
`references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. This Skill does not silently
depend on any sibling Skill.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it; otherwise infer the installed
  skill directory from the current skill context.
- Verify `scripts/search_plugin.py` and `references/gateway-api.md` exist before
  work; if a resource is missing, name its expected relative path and stop.
- Resolve `context.profile` on every invocation. Precedence: current request,
  project context, Skill records, shared preferences, shared user/brand
  profile, safe defaults. A direct user statement about a durable preference
  should be saved with `scripts/profile_store.py record` using `--confirm`,
  followed by a concise saved-path report.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/dsh-search-plugin"
```

### Step 1: Understand the requested outcome

- Extract from the request: the goal or keyword, optional filters (category,
  language, grade, tag, owner, min score), result count, and the output
  language (default: profile `user.language`).
- Confirm the deliverable: an evidence-tagged candidate list in the final
  answer (default), plus an optional raw JSON artifact saved to
  `workspace.output_dir` when the user wants a durable file.
- Keep internal background out of the user-facing result.

### Step 1.5: Analyze nearby Skills before implementation

- Inspect `references/skill-composition.md`. `dsh-search-or-create-plugin` may
  consume this Skill's JSON artifact as an optional upstream handoff;
  `dsh-plugin-creator` may consume the candidate list as base-implementation
  evidence. Neither is a hidden dependency of this Skill.

### Step 2: Search the gateway

1. Derive 2-4 short keywords from the goal. The gateway needs at least two
   trimmed characters per keyword and caps at 64.
2. Run the deterministic client. Examples:

```bash
python3 "$SKILL_DIR/scripts/search_plugin.py" search "memory" --limit 10 --pretty
python3 "$SKILL_DIR/scripts/search_plugin.py" suggest "memory"
```

3. Apply filters from the request or profile defaults:

```bash
python3 "$SKILL_DIR/scripts/search_plugin.py" search "web" --grade S --min-score 80 --limit 10
python3 "$SKILL_DIR/scripts/search_plugin.py" search "feishu" --category automation --language TypeScript
```

4. When a candidate looks central to the goal, fetch its detail for the
   localized intro, highlights, and growth evidence:

```bash
python3 "$SKILL_DIR/scripts/search_plugin.py" detail owner repo
```

5. On empty or weak results, retry with synonyms, a broader keyword, or the
   category facet; only then consult `/v1/catalog` or `/graphql` per
   `references/gateway-api.md`. A single miss is not evidence of absence.

### Step 3: Rank and present evidence

- Rank primarily by gateway `score` then `grade`, then `stars`; demote
  `archived` or `is_risky` plugins and surface `risk_note`.
- Present each candidate with: `full_name`, one-line description, score,
  grade, stars, category, tags, install kind and package name, official or
  featured placement, repository URL, and risk flags.
- Include provenance in the result: `data_version` and `as_of` from the
  response, plus the `pushed_at` and `last_synced_at` freshness.
- When the user wants a durable artifact, save the raw JSON under
  `workspace.output_dir` (or the current directory) and report the exact path.

### Step 4: Validate the deliverable

- Verify every claim in the final answer comes from a live gateway response
  fetched in this run or from the saved artifact; cite `data_version`.
- Verify completeness, factual support, and output paths; report remaining
  evidence gaps (for example unrated plugins with null score or grade).
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as
  the standard trust bundle for this Skill.

## References

- `references/gateway-api.md` — verified endpoint contract for the dshfind gateway.
- `references/skill-composition.md` — nearby Skill group and handoff analysis.
- `references/user-profile.md` — the shared `user-profile/v1` contract.

## Dependencies

- Python 3.8+ (stdlib only, no pip packages) and network access to
  `https://api.dshfind.com` (public, no auth).
- The OpenAPI document is published at
  `https://dshfind.lovstudio.ai/openapi.json`; it describes the same endpoints.
- No external Skills are required; sibling Skills are optional artifact-level
  handoffs only.
