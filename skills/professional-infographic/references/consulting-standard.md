# Consulting Exhibit standard

“Consulting-grade” means an evidence-led Exhibit, not imitation of or affiliation
with a named firm. The page must make a defensible argument visible.

Read `exhibit-benchmark.md` before authoring or reviewing the first Exhibit in a
session.

## Contents

1. The unit of work is an Exhibit
2. Decision and evidence graph
3. Title modes and recommendation placement
4. Evidence ledger
5. Information density
6. Visual variables
7. Copy editing
8. Rejection patterns
9. Quality rubric
10. Definition of done

## 1. The unit of work is an Exhibit

An Exhibit is not a poster decorated with information. It contains:

1. a figure label;
2. a title that establishes the subject, purpose, or answer;
3. one dominant visual relationship;
4. directly attached evidence and annotations;
5. an evidence-backed recommendation after the visual in `topic` mode;
6. a note/source line;
7. restrained brand ownership.

The reading order should be clear without explanation. For most public-facing
infographics it is: topic → evidence → recommendation. For a standalone
executive Exhibit with known context, an action title may state the answer and
the tail recommendation is omitted.

## 2. Start with a decision and an evidence graph

Before layout, write:

- audience and use moment;
- decision or belief that should change;
- one governing conclusion;
- 3–7 claims, criteria, drivers, stages, or entities needed to prove it;
- exact evidence supporting every visible mark;
- assumptions and material omissions.

Map the argument:

```text
Display title or action title
├── visible claim / decision criterion
│   ├── evidence ID
│   └── visual encoding + direct annotation
├── visible claim / decision criterion
│   ├── evidence ID
│   └── visual encoding + direct annotation
├── implication / decision
└── tail recommendation in topic mode
```

Do not begin HTML until the map exists in `brief.md`.

## 3. Choose a title mode

Use `topic` mode by default when the infographic must introduce itself to a
reader. The title should name:

1. the subject;
2. the purpose or comparison job;
3. the most important dimensions when useful.

Put the specific advice, boundary, or next action after the main visual and
before the source footer.

| Weak topic title | Strong topic title |
|---|---|
| 跨端方案对比 | 移动端跨平台技术选型指南：渠道、性能与团队约束对比 |
| AI 市场趋势 | AI 原生产品增长格局：渗透率、留存与商业化路径 |
| 产品路线图 | AI 产品规模化路线图：能力 Gate、验证节点与关键依赖 |

Use `action` mode only when the audience already knows the subject and expects
an executive Exhibit. Then the title must contain a subject, directional
finding, and—when useful—a business implication.

Rules for both modes:

- Prefer one or two deliberate lines; do not let a key term break across lines.
- Keep topic titles specific enough to explain the infographic's job.
- Keep action titles specific enough to carry the conclusion without a tail repeat.
- Put recommendations only after the evidence in topic mode.
- Map the recommendation to source IDs just like any other decision mark.
- Avoid empty claims such as “至关重要”“正在改变一切”“没有绝对答案”.
- Use 12–28 semantic units as the normal title range and 42 as a hard ceiling.
- Use 8–36 semantic units for the tail recommendation and 56 as a hard ceiling.

## 4. Maintain an evidence ledger

For every value, rank, position, causal arrow, decision cell, and named fact,
record:

- evidence ID;
- exact source text or value;
- location / URL;
- unit, denominator, and period;
- fact, estimate, assumption, or interpretation;
- caveat.

In HTML, link visible marks back to the ledger with `data-source-ref="S1"`.

Rules:

- Never invent values to make a chart possible.
- Never turn adjectives into percentages.
- Label qualitative coordinates or strength explicitly as qualitative.
- Do not imply causation from correlation.
- Use a conceptual diagram when comparable evidence is missing.

## 5. Maximize encoded information, not word count

Information density is the ratio of useful distinctions to visual area.

Useful distinctions include:

- comparable values on a shared scale;
- directly labeled differences;
- conditions and branches;
- driver hierarchy;
- axis position and zones;
- milestones and gates;
- actor–capability–flow relationships;
- annotations that explain a discontinuity or decision.

Prose inside a large rectangle is not information density.

Default composition for a 16:9 Exhibit:

| Region | Target |
|---|---:|
| Brand + figure label | 3%–5% of height |
| Title region | 8%–15% |
| Main visual | 58%–75% |
| Tail recommendation in topic mode | 4%–7% |
| Notes, source, attribution | 5%–8% |

Use the space to enlarge the visual and annotations, not to create empty cards.

## 6. Use visual variables deliberately

Every use of position, length, color, shape, connection, order, or containment
must encode a named meaning.

Priority for quantitative precision:

```text
position on common scale
> length
> position on nonaligned scale
> area
> angle
> decorative color
```

Rules:

- Use color for one semantic distinction, normally decision / exception /
  category. Do not alternate colors for decoration.
- Direct-label values and series whenever space allows.
- Use a legend only when direct labels would make reading slower.
- Annotate the evidence that supports the governing conclusion.
- Use one shared scale across a comparison or small-multiple set.

## 7. Edit copy by role

Suggested budgets count one CJK character or one Latin word as one semantic
unit:

| Element | Normal | Hard ceiling |
|---|---:|---:|
| Display or action title | 12–28 | 42 |
| Tail recommendation | 8–36 | 56 |
| Deck / reading instruction | 12–32 | 56 |
| Entity or dimension label | 2–12 | 20 |
| Direct annotation | 4–18 | 28 |
| Outcome / implication | 8–28 | 48 |
| Source / note | as required | must remain readable |

Edit in this order:

1. delete repetition;
2. convert sentences into precise labels;
3. attach qualifiers to the relevant mark;
4. move methodology into the note;
5. split the story;
6. reduce font size only as the last resort.

## 8. Reject anti-patterns

Reject:

- a bento grid used because the source is long;
- three to five equal cards under an oversized title;
- a “matrix” that is only prose in aligned columns;
- a “decision tree” without testable conditions and labeled branches;
- a 2×2 with vague axes, unlabeled ends, or decorative coordinates;
- random icons, blobs, rings, gradients, fake UI, 3D, glow, or emoji;
- unsupported scores, market positions, or causal arrows;
- duplicated conclusion bands;
- a recommendation placed above the evidence in topic mode;
- a theme title with no reader job, such as only “趋势分析”;
- source notes that cannot be mapped to individual claims.

## 9. Quality rubric

Score 100 points:

| Dimension | Points | Minimum for critical dimensions |
|---|---:|---:|
| Core conclusion | 20 | 16 |
| Evidence quality | 20 | 12 |
| Visual encoding | 20 | 14 |
| Information density | 15 | 10 |
| Copy and annotations | 10 | — |
| Layout and typography | 10 | — |
| Source and brand | 5 | — |

Release threshold: 85/100 and no critical dimension below minimum.

The CLI score is a conservative machine proxy. It can detect missing semantics,
bad area ratios, empty blocks, weak evidence linkage, overflow, and similar
failures. It cannot judge truth, insight, or taste. A human/vision review of the
rendered image is always required.

## 10. Definition of done

The Exhibit is done only when:

- the title makes the subject, purpose, or answer clear in five seconds;
- the visual supports the governing conclusion;
- topic mode ends with an evidence-linked recommendation;
- action mode does not duplicate its conclusion in a tail band;
- the reader has one clear entry point and path;
- all marks map to evidence;
- variables and scales are explicit;
- notes and caveats are readable;
- removing any remaining element would weaken meaning or trust;
- the automatic gate passes;
- the rendered image passes full-page and 100% visual inspection.
