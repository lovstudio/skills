# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-wdb-cli` | upstream atom | Owns key preparation and read-only, isolated WeChat queries. This Skill consumes its `chats --format jsonl` export; it never opens a database itself. Handoff artifact: `messages.jsonl` + the two usernames. |
| `lov-mobile-infographic` | downstream atom | Owns card scaffolding, the `data-*` contract, rendering, and the readability audit. This Skill hands over three SVG figures plus `card-data.json`; the card Skill owns final layout and the release gate. |
| `lov-professional-infographic` | alternative downstream | Use instead of `lov-mobile-infographic` when the user wants a 16:9 desktop exhibit rather than a phone card. Same figure data, different layout owner. |
| `lov-gen-card` | not composed | Produces collectible or illustrated knowledge cards from structured content; its acceptance criteria (illustration, series structure) do not fit a data argument. |
| `baoyu-wechat-summary`, `lov-daily-post` | not composed | Both summarize conversations into text digests; they do not quantify reciprocity or measure topic composition, and neither produces a data card. |

## Atomic Handoffs

```text
lov-wdb-cli (optional upstream)
  messages.jsonl + me/other usernames
                |
                v
lov-do-they-love-me  (core atom)
  metrics.json · matrix.json · labels.jsonl · accuracy.json
  composition.json · figures/*.svg · card-data.json
                |
                v
lov-mobile-infographic (optional downstream)
  card.html · card.png · card.audit.json
```

Every arrow is an artifact on disk, not a hidden runtime import. If the upstream
query Skill is unavailable, the analysis still runs on any JSONL export with the
documented fields; if the downstream card Skill is unavailable, the quantified
and semantic results are still a complete answer.

## Overlap Decisions

- The core outcome — what this chat actually contains, measured and semantically
  split — exists in no other local Skill; digest and card Skills both start from
  material that is already summarized.
- Topic classification, calibration, and the activity index stay in this Skill
  rather than being pushed into `lov-wdb-cli`: they are analysis over an export,
  not database access, and keeping them here leaves the query Skill read-only.
- Card layout stays downstream. This Skill only emits figure fragments whose
  colour references resolve inside the card's own palette.

## Composition Decision

`lov-do-they-love-me` is a **Single Skill**. Its stages (quantify → label → compose →
figures) are steps of one user-visible outcome in a fixed order and have no
independent audience of their own, so wrapping them in a Kit would add
indirection without adding a usable entry point. The two neighbours remain
optional, artifact-level handoffs.
