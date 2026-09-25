# Product OnePage layouts and DOM contract

## Shared contract

```html
<main
  class="onepage"
  data-layout="launch-story"
  data-style="editorial-tech"
  data-aspect="4:5"
>
```

Required selectors:

- `[data-region="header"]`
- `[data-region="hero"]`
- `[data-region="product"]`
- `[data-region="proof"]`
- `[data-region="action"]`
- `[data-region="footer"]`
- `[data-role="category"]`
- `[data-role="headline"]`
- `[data-role="product-stage"]`
- two to four `[data-role="feature"]`
- one or more `[data-role="proof"][data-source-ref]`
- exactly one primary `[data-role="cta"]` with a real destination
- `.brand-lockup img`
- `.source-note[data-audit="source"]`
- `.generation-note[data-audit="attribution"]`

Generated supporting images declare `data-generated="true"` and
`data-text-free="true"`. Real product artifacts use
`data-authenticity="real"`; conceptual representations use
`data-authenticity="conceptual"`.

## Composition

| Region | Target canvas area |
|---|---:|
| Header/brand | 4%–10% |
| Hero copy/orientation | 16%–30% |
| Product stage | 35%–58% |
| Proof and action | 12%–25% |
| Footer/source | 3%–7% |

## Layouts

### `launch-story`

Use for a new product, major release, or flagship offer. Lead with promise and
category, stage one product artifact at dominant scale, then show two or three
mechanisms, proof, and CTA.

### `problem-solution`

Use when adoption begins with a costly before-state. Encode before → mechanism →
after through position, contrast, and product evidence. Avoid invented before/
after metrics.

### `product-tour`

Use when workflow differentiates the product. Show three to five real steps or
states connected through one reading path. Each step needs an artifact or
specific mechanism, not a feature paragraph.

### `proof-led`

Use when adoption depends on trust. Place the strongest verified artifact,
case, or metric near the headline; product mechanism explains why the outcome
is credible. Keep sources visible.

### `comparison`

Use for a real before/after or alternative decision with consistent criteria.
Direct-label differences. State when judgment is qualitative. Give the product
the decision role only when evidence supports it.

### `event-launch`

Use for dated launches, events, limited campaigns, and waitlists. Date, time,
location/host, availability, and CTA are exact. The visual hierarchy prioritizes
event identity and action over feature detail.

## Recomposition rules

- `4:5`: default feed master; balanced product stage and proof.
- `9:16`: shorten copy, enlarge CTA, keep critical content inside mobile safe zones.
- `1:1`: retain thesis, one product cue, one proof, and action.
- `16:9`: place copy and product stage side by side.
- `A4`: increase reading-distance contrast and reserve print-safe margins.

Create a new composition for each aspect. Cropping a master fails the contract.
