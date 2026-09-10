# Research Report Contract

This Skill defaults to a **source-backed research report** when the operator
supplies a topic, question, plan, comparison, or a bare phrase such as
「冈仁波齐线路规划」. Search JSON is an intermediate evidence layer, not the
default final answer.

## Mode decision

- **Report mode (default):** a topic, question, guide, plan, comparison,
  recommendation, route, strategy, trend, or selection request.
- **Search-only mode (opt-in):** the operator explicitly asks to search notes,
  inspect titles, filter multiple title terms, export JSON, or list raw rows.
- If the operator asks for a report but the request is too broad to answer
  from one platform, keep the report focused on Xiaohongshu and state the
  platform boundary; hand off to `deep-research` only for a genuinely
  multi-source or non-Xiaohongshu research request.

## Required report shape

1. **结论先行** — answer the operator's actual question in 3–7 bullets or a
   compact table. Do not open with the search process.
2. **可执行方案** — for planning requests, provide the route/plan/steps,
   milestones, dependencies, budget or resource notes where evidenced, and
   decision points.
3. **证据层** — include a source table with note title, author, publication
   label, interaction fields when useful, and the original note URL. Use only
   values returned by `xhs_search.py` and `xhs_collect.py`.
4. **差异与不确定性** — show conflicts between notes, missing information,
   and facts that require an official or on-site check.
5. **边界** — distinguish source-derived facts from standard professional
   reasoning or recommendations. Never present a recommendation as a platform
   fact.
6. **交付物** — return the report in the conversation and save a Markdown file
   when the report is substantial. Keep the source corpus JSON path visible.

## Evidence rules

- `items` and `notes` are the source of truth for titles, authors, dates,
  interaction counts, URLs, and note bodies.
- Quote or paraphrase note content without inventing missing facts.
- Do not claim an official Xiaohongshu ranking; local sorting is explicitly a
  Skill-side ordering.
- When the corpus is small, contradictory, or mostly promotional, say so.
- Separate safety-critical guidance from user anecdotes. For medical,
  permit, border, legal, or weather-critical decisions, recommend confirming
  with an official source or qualified professional.
- Do not download note media unless the operator explicitly requests it.

## Minimum machine-readable evidence

The collect step must produce:

```json
{
  "ok": true,
  "meta": {
    "query": "冈仁波齐线路规划",
    "items_fetched": 22,
    "matches": 21,
    "notes_requested": 12,
    "notes_collected": 12,
    "errors": []
  },
  "notes": [
    {
      "id": "note-id",
      "title": "原始标题",
      "author": "作者昵称",
      "desc": "原始正文",
      "published_at": "07-12",
      "likes": 69,
      "comments": 56,
      "collects": 89,
      "shares": 29,
      "url": "https://www.xiaohongshu.com/explore/note-id"
    }
  ]
}
```

If note-body collection fails, report the failure and do not fill the gap with
invented content.
