---
name: lov-search-twitter
description: >
  搜索并恢复公开 X/Twitter 帖子的逐字正文、原帖链接与截图证据，区分现存原帖、归档、嵌入卡片、媒体引文和未恢复项；适用于“找这人的推特原文”“汇总 X 全文”与 “recover deleted tweets”。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.9+; web search or browser access is required for discovery, while OCR is optional."
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: verbatim
  tags:
    - twitter
    - x
    - source-recovery
    - screenshot-evidence
    - web-archive
---

# lov-search-twitter — 找到原帖，也说明哪些没有找到

把人物、账号、关键词、X 链接、status ID 或截图整理成可核验的原帖索引与逐字正文汇总。正文必须来自可定位证据；搜索摘要、媒体转述和 OCR 不得冒充原文。

## Triggers

### Activate when

- “帮我找这个人的推特原文 / X 原帖 / 已删除推文。”
- “把这些 tweet 链接的全文和截图证据汇总出来。”
- “根据国内转载截图反查原始 X 帖子。”
- “Recover deleted tweets”, “find the original X post”, or “compile a verbatim Twitter thread”.

### Do not activate when

- 用户只想发布或排程 X 内容：交给发布或社交媒体排程能力。
- 用户只想下载已知帖子的图片或视频：交给 `lov-media-crawler`。
- 用户只想判断一项指控是否属实，而非恢复原帖：交给 `lov-fact-check`。
- 用户要求进入私密账号、绕过登录墙、购买墙或访问控制：拒绝绕过；本 Skill 只处理用户有权访问的公开或已授权内容。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable output-language, evidence-format, or
workspace preference, persist it through `scripts/profile_store.py` and report
the saved profile path. Put Skill-specific values under `records.<field>`; use
`user.<field>` for shared values. Never persist cookies, tokens, proxy secrets,
or browser sessions. See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend an adjacent capability. Sibling Skills are optional artifact handoffs,
not hidden runtime dependencies.

## Evidence Contract

Read `references/evidence-model.md` before searching. Every claimed post must
have a status ID or an explicit `identity_unresolved` marker, a source URL, a
retrieval time, a provenance tier, and the preserved text or image hash.

The normal output class is `verbatim`:

- Preserve spelling, punctuation, line breaks, names, numbers, emoji, links,
  and visible truncation markers exactly as the source exposes them.
- Never silently translate, repair grammar, join a truncated card with a media
  paraphrase, or infer missing sentences.
- Put translations, summaries, and editorial notes in separate labelled fields.
- A Wayback CDX hit proves that a URL was captured, not that its正文 was saved.
- “Known IDs recovered” is not “complete account history”. Only claim full
  coverage after an authorized timeline enumeration or a reconciled inventory.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve root and runtime

- Use `SKILL_DIR` if provided; otherwise infer the installed Skill directory.
- Verify `$SKILL_DIR/scripts/search_twitter.py`,
  `$SKILL_DIR/references/evidence-model.md`, and
  `$SKILL_DIR/references/discovery-playbook.md` before work.
- Read the shared Profile. Current request overrides project context, Skill
  records, shared preferences, then safe defaults.
- Use Python 3.9+ for deterministic extraction. OCR and browser rendering are
  optional evidence paths, not silent dependencies.

### Step 1: Define scope and completion claim

Record the requested person, known/current/former handles, time range,
languages, expected deliverable, and whether the user means:

1. known-post recovery;
2. best-effort public discovery; or
3. complete authorized account history.

Do not ask for a technical implementation choice. If the user says “全文” but
does not provide account authorization, use best-effort public discovery and
state that account-history completeness cannot be proven.

### Step 2: Build the candidate inventory

Use at least two discovery paths from `references/discovery-playbook.md`:

- exact searches for handle, former handle, display name, distinctive quotes,
  status IDs, `x.com/.../status/...`, `twitter.com/.../status/...`, and `t.co`;
- Chinese web and image search across news, Weibo, WeChat, Telegram, forums,
  repost pages, and screenshot-heavy results;
- page source, embedded X cards, structured data, link redirects, and media
  articles;
- Wayback CDX and Common Crawl URL indexes.

Extract candidate URLs/IDs from saved text without network access:

```bash
python3 "$SKILL_DIR/scripts/search_twitter.py" discover \
  --input search-results.txt --pretty > candidates.json
```

Maintain an inventory row for every candidate. Do not discard unavailable or
duplicate-looking IDs until URL, timestamp, and text relationships are checked.

### Step 3: Recover known posts

For each handle/status ID, query both public renderers concurrently, then fall
back to exact Wayback captures and optionally Common Crawl:

```bash
python3 "$SKILL_DIR/scripts/search_twitter.py" recover HANDLE \
  --ids-file ids.txt --common-crawl --pretty > recovered.json
```

FxTwitter and VXTwitter agreement is a `two-renderer-match`, useful for detecting
truncation or extraction errors. It is not proof that two independent authors
published the same text. Prefer the longest exact variant only when normalized
texts differ solely by URL expansion or presentation whitespace; otherwise keep
both variants and mark `conflict`.

### Step 4: Preserve screenshot and OCR evidence

For every screenshot, save the original bytes before cropping or annotating.
Record source page URL, capture time, SHA-256, visible account/status clues, and
whether it is an X card, repost screenshot, or ordinary media article. Register
the file deterministically:

```bash
python3 "$SKILL_DIR/scripts/search_twitter.py" evidence screenshot.png \
  --kind screenshot_copy --source-url SOURCE_URL \
  --ocr-file screenshot.ocr.txt --pretty > screenshot-evidence.json
```

OCR is a derived transcription. Preserve it separately from `verbatim_text`,
and mark ambiguous characters. A crop may improve readability but must refer to
the hash of its uncropped parent when available.

### Step 5: Reconcile and grade evidence

Assign exactly one primary provenance tier from `references/evidence-model.md`.
Use the strongest evidence actually observed, retain weaker corroboration, and
keep conflicts visible. Never promote a search snippet, translation, or media
paraphrase to `live_original` or `archived_original`.

### Step 6: Deliver the result

Produce:

1. scope and retrieval date;
2. candidate/original-post index with URL, ID, timestamp, status and provenance;
3. a verbatim section containing only recoverable text;
4. a screenshot evidence section with hashes and source pages;
5. an explicit unrecovered/conflict section;
6. a coverage statement such as “7 of 15 known IDs recovered”, never an
   unsupported “all posts recovered”.

Label `原文`, `OCR 转写`, `媒体引文`, `摘要`, `翻译`, and `编辑说明` separately.
When a user asks for original text, a summary is not a substitute.

### Step 7: Validate

- Re-open every source URL or retained file used for the final claim.
- Recompute screenshot hashes and verify output counts against the inventory.
- Spot-check line breaks and truncation markers against rendered evidence.
- Run the offline tests when the CLI changes:

```bash
python3 -m unittest discover -s "$SKILL_DIR/tests" -v
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
```

Report remaining gaps and access limitations with the finished files.

## Authorization Boundary

- The default workflow is zero-login and never reads browser cookies.
- If complete active-account enumeration genuinely requires `twscrape` or an X
  session, explain why and obtain explicit authorization before using it.
- Keep user-owned credentials in an OS credential store or current process
  environment. Never place them in Profile, source, reports, tests, or chat.
- Do not evade suspensions, private-account controls, paywalls, rate limits, or
  platform protection.

## Dependencies

- Python 3.9+ standard library for `scripts/search_twitter.py`.
- Network access for live renderers and web archives.
- Web/image search or a browser for broad discovery and rendered screenshots.
- Optional OCR engine for screenshot transcription.
- Optional `twscrape` only after explicit authorization for account enumeration.
