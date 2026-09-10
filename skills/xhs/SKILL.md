---
name: lov-xhs
description: >
  Default a Xiaohongshu topic request to a source-backed research report; use
  search-only mode only when requested. Use when the user mentions
  小红书调研、攻略规划、选题研究、小红书搜索, or "search Xiaohongshu notes".
license: MIT
compatibility: "Portable Agent Skills format. Requires Python 3.9+, xiaohongshu-cli 0.6.4+ with a logged-in session, and network access. jq and API keys are not required."
allowed-tools:
  - Bash
  - Read file
  - Write file
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  category: General
  tags:
    - xiaohongshu
    - xhs
    - research
    - report
    - planning
    - search
    - note-research
---

# 小红书调研助手 · Xiaohongshu Research

A bare Xiaohongshu topic request is a **research request**, not a request to
dump search JSON. The Skill discovers notes, reads selected note bodies,
extracts an auditable evidence corpus, and returns a source-backed report that
answers the operator's actual question. Explicit search-only mode remains
available when the operator asks for it.

## Triggers

### Activate when

- 用户给出一个主题或命题，例如「冈仁波齐线路规划」「小红书露营装备趋势」。
- 用户要求“小红书调研”“做一份攻略/规划/对比/建议”“整理选题/内容方向”。
- 用户明确要求“小红书搜索”“查标题同时包含……”“导出 JSON”。
- "Use lov-xhs to research a Xiaohongshu topic and return a report."
- "Do Xiaohongshu research on ..." or "Search Xiaohongshu notes ...".

### Do not activate when

- 用户只给小红书链接并要求下载本地媒体：交给 `lov-media-crawler`。
- 用户要求发布、排期或核验小红书/视频号内容：交给 `lov-media-publisher`。
- 用户要检索本机文件、聊天记录或公众号文章：交给对应的本地搜索 Skills。
- 用户要求跨平台、全网或多数据源研究，且不限于小红书：交给 `deep-research`。

## Mode Router (mandatory)

### Report mode (default)

Use report mode when the request names a topic, question, route, plan,
comparison, recommendation, trend, selection, or strategy — including a bare
phrase such as 「冈仁波齐线路规划」. Do not ask the operator to choose between
“search” and “report” when the input is already a topic; default to report.

### Search-only mode (opt-in)

Use search-only mode only when the operator explicitly says “只搜索”, “查标题”,
“列出笔记”, “导出 JSON”, “给我原始结果”, or otherwise asks for raw discovery
rows rather than an answer. If the operator asks for both, deliver the report
first and keep the JSON as an attached source artifact.

## User Profile (cross-session)

Read the shared `user-profile/v1` contract at the start of every run. Resolve
values in this order: current request, project context, this Skill's records,
shared preferences, shared user/brand profile, then safe defaults. When the
operator directly states a durable preference or brand fact, persist it through
`scripts/profile_store.py` and report the saved profile path. Never persist
cookies, tokens, secrets, or inferred credentials. See
`references/user-profile.md` for the full contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to hand off to an
adjacent capability. The record keeps report mode, search-only export, and media
download as separate, explicit handoffs rather than hidden dependencies.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve runtime and authentication

- Run `xhs --version` and confirm `xiaohongshu-cli` is installed.
- Run `xhs status` and confirm `authenticated: true` and `guest: false`.
- If login is not active, stop and tell the operator to run `xhs login --qrcode`.
- Read `references/implementation.md` and `references/authorship-integrity.md` before building commands.
- If the CLI returns a captcha/risk-control error, preserve the raw error and
  ask the operator to complete the browser verification before retrying.

### Step 1: Classify the request and define the answer

- Apply the mode router above.
- For report mode, write down the operator's actual question in one sentence.
  Examples: “如何规划冈仁波齐转山？” or “这个主题在小红书上的主流做法是什么？”
- For the platform query, **start with the operator's exact phrase**. Do not
  silently replace 「冈仁波齐线路规划」 with a broader or different word.
- Only broaden or add alternate queries after the exact query returns zero or
  clearly irrelevant results, and state that change in the report.
- Do not add `--must-contain` title filters unless the operator explicitly
  requires terms in the title.
- Use `AskUserQuestion` only when a mandatory input is genuinely missing or the
  requested mode is impossible to infer. Do not use it to ask whether a bare
  topic should become a report; report mode is the default.

### Step 2: Report mode

1. **Discover notes.** Run the deterministic search script with the exact topic
   first, 1–3 pages, and `--sort popular` unless the operator asks otherwise.
   Save JSON with `--output`.
2. **Collect bodies.** Run `scripts/xhs_collect.py` against the same query, or
   read selected notes with `xhs read --json` when collection is unavailable.
   Save the evidence corpus with `--output`.
3. **Verify evidence.** Confirm `ok: true`; inspect `meta.matches`,
   `meta.notes_collected`, and `meta.errors`. Never fill a failed read with
   invented content.
4. **Synthesize the report.** Follow `references/research-report.md`. Answer the
   actual question first, then provide the executable plan/answer, evidence
   table, conflicts, uncertainty, and source links.
5. **Cite the evidence.** Use only `items` and `notes` for note titles,
   authors, dates, interaction counts, descriptions, and URLs. Label
   professional reasoning or recommendations as synthesis, not as platform
   fact.
6. **Save the report.** For substantial reports, write a Markdown file and
   return its absolute path together with the source-corpus path.

### Step 3: Search-only mode

- Run `scripts/xhs_search.py` with the operator's query, optional title terms,
  page count, sort, and output path.
- Confirm `ok: true`; inspect `meta.items_fetched` and `meta.matches`.
- Treat `items` as the only source for titles, authors, interaction counts,
  dates, and URLs.
- If the operator wants a ranking, sort locally by the returned numeric fields.
  Never present it as an official Xiaohongshu ranking.

### Step 4: Deliver the result

- **Report mode:** deliver the conclusion and recommendation first. Include
  `meta.matches` and `meta.notes_collected`, the evidence corpus path, and the
  report file path when one was written.
- **Search-only mode:** return the saved JSON path, or a concise source table
  when no output file was requested. Include `meta.matches`.
- Keep source text and quotations separate from authored recommendations.
- Do not expose cookies, tokens, secrets, or private session data.

### Step 5: Optional downstream handoff

Only when the operator explicitly asks to download media for a selected note,
pass that note URL to `lov-media-crawler`. Do not download media by default.

## Dependencies

- Python 3.9+
- `xiaohongshu-cli` 0.6.4+
- Active Xiaohongshu browser login
- Network access
- `lov-branding-consistency` for authored, audience-visible report copy

The Skill does not require `jq`, API keys, or an external cloud service.

## Validation gate

```bash
python3 scripts/validate_skill.py .
```

The source passes only when every local reference and script resolves, trust
files contain a real case and dimensions, and no private path or unresolved
placeholder remains.
