# BP Skill Kit Composition

## Principle

Composition is file-based, not conversation-based. Every module shares a stable BP
workspace so users can stop, switch agents, or resume later without losing state.

## Module boundaries

| Module | Owns | Must not own |
|---|---|---|
| `bp-outline` | Facts, assumptions, positioning, page argument | Visual decoration and slide export |
| `bp-deck` | Style, layout, rendering, branding, export | New business facts or unsupported copy |
| `bp-polish` | Adversarial review, exact revisions, targeted correction | Silent changes to evidence or complete regeneration by default |

## Handoff states

```text
MATERIALS
   │
   ▼
OUTLINE_DRAFT ── evidence gate ──► OUTLINE_APPROVED
                                      │
                                      ▼
                                  DECK_DRAFT
                                      │
                                visual + claim gate
                                      │
                                      ▼
                                  DECK_READY
```

An evidence blocker moves `DECK_DRAFT` back to `OUTLINE_DRAFT`. A visual defect keeps
the workflow in `DECK_DRAFT` and regenerates only affected slides.

## User-intent routing

- A noun usually selects an artifact: “大纲” → outline, “PPT/PDF” → deck.
- A quality complaint selects polish: “不专业 / 太技术 / 图表乱 / 页面拖沓”.
- “完整 / 从项目材料开始 / 融资 BP” selects the full pipeline.
- Explicit scope always wins over automatic routing.

## Interaction budget

Collect decisions once and persist them in `brief.md` or `deck-manifest.md`.

- Outline questions: audience/stage, financing ask, source scope.
- Deck questions: visual direction and required format.
- Polish questions: review mode only when the request does not reveal it.

Do not ask the same question again in a later module.

## Completion rules

- Outline route ends with three Markdown artifacts and evidence gaps.
- Deck route ends with PPTX, PDF, preview, and manifest.
- Polish route ends with a scored report and applied or explicitly proposed fixes.
- Full route ends only when all three contracts are satisfied.
