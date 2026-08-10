# Exhibit grammar and semantic contracts

Choose a template from the information relationship. Style never overrides
semantic fit. Use one primary grammar and, at most, one secondary annotation
device.

## Contents

1. Selection
2. Shared DOM contract
3. Eight template contracts
4. Composition
5. Template-specific visual review

## Selection

| Relationship | Template | Required visual job |
|---|---|---|
| Alternatives × consistent criteria | `comparison-matrix` | Encode aligned differences and a decision |
| Sequential yes/no constraints | `decision-tree` | Route the reader through testable conditions |
| Result → drivers → subdrivers | `driver-tree` | Decompose one outcome using consistent logic |
| Entities on two independent axes | `positioning-map` | Reveal zones, clusters, whitespace, or a target position |
| Start + gains − losses = end | `waterfall` | Explain value movement on one additive scale |
| Time / maturity with dependencies | `roadmap` | Show phases, milestones, gates, and critical path |
| Actors → capabilities → outcomes | `operating-model` | Explain interfaces, ownership, and flows |
| Repeated comparison on one scale | `small-multiples` | Expose a pattern across comparable panels |

Do not choose:

- a matrix when criteria are not consistent;
- a decision tree when branches are merely categories;
- a driver tree when children do not explain the same parent metric;
- a positioning map when axes are dependent or vague;
- a waterfall when components are not additive;
- a roadmap when there is no time, maturity, or dependency;
- an operating model for a flat component list;
- small multiples when scales or units differ.

## Shared DOM contract

The poster must declare:

```html
<article
  class="poster"
  data-template="comparison-matrix"
  data-mode="qualitative"
  data-aspect="16:9"
  data-title-mode="topic"
>
```

Required shared semantics:

- `[data-region="header"]`
- `[data-region="visual"]`
- `[data-region="recommendation"][data-audit="recommendation"]` in `topic` mode
- `[data-region="footer"]`
- `[data-primary-block]`
- `[data-encoding="position color"]`
- `[data-source-ref="S1"]`
- `[data-annotation]`
- `[data-decision]`

`topic` mode requires one recommendation after the main visual and before the
source footer. It must carry `data-source-ref`. `action` mode omits this region
because its title already states the conclusion.

Allowed encoding tokens:

```text
position length color shape connection order containment
```

Quantitative or mixed Exhibits also require `[data-unit]`.

## Template contracts

### `comparison-matrix`

Minimum:

- 3 `[data-entity]`;
- 3 `[data-dimension]`;
- 6 `[data-data-point]`;
- 1 `[data-annotation]`;
- 1 `[data-decision]`;
- 2 encoding tokens.

Use a shared row/column grammar. A cell must encode a value, category, or
decision—not a paragraph. Highlight only decision-changing differences.

### `decision-tree`

Minimum:

- 3 `[data-condition]`;
- 4 `[data-branch]`;
- 3 `[data-outcome]`;
- 4 `[data-connector]`;
- 1 `[data-decision]`;
- 2 encoding tokens.

Every condition must be testable. Label branches directly with yes/no or named
states. Put outcomes at terminal nodes. A vertical stack of boxes with side
arrows is not sufficient.

### `driver-tree`

Minimum:

- 5 `[data-driver]`;
- 3 distinct `[data-level]` values;
- 4 `[data-connector]`;
- 2 `[data-annotation]`;
- 2 encoding tokens.

All children of one parent must answer the same decomposition question. Mark
assumptions when branches are not exhaustive or mutually exclusive.

### `positioning-map`

Minimum:

- 2 `[data-axis]`;
- 4 `[data-axis-end]`;
- 4 `[data-zone]`;
- 4 `[data-data-point]`;
- 2 `[data-annotation]`;
- 1 `[data-decision]`;
- 2 encoding tokens.

Name both axis ends and explain the units or qualitative basis. Label zones
with business meaning. Plot direct labels; avoid large floating cards. Say
explicitly when positions are judgment rather than measurement.

### `waterfall`

Minimum:

- 4 `[data-data-point]`;
- 1 `[data-baseline]`;
- 1 `[data-unit]`;
- 2 `[data-annotation]`;
- 1 `[data-decision]`;
- 2 encoding tokens.

Use one additive unit and reconcile start to end. Encode positive and negative
movement consistently. Annotate the largest driver or surprising offset.

### `roadmap`

Minimum:

- 3 `[data-phase]`;
- 4 `[data-milestone]`;
- 2 `[data-gate]`;
- 3 `[data-connector]`;
- 1 `[data-decision]`;
- 2 encoding tokens.

Differentiate milestones from gates. Show dependencies or critical path. A
calendar-colored task list is not a roadmap.

### `operating-model`

Minimum:

- 2 `[data-actor]`;
- 3 `[data-capability]`;
- 3 `[data-flow]`;
- 2 `[data-outcome]`;
- 3 `[data-connector]`;
- 2 `[data-annotation]`;
- 2 encoding tokens.

Actors, capabilities, flows, and outcomes need distinct visual grammar. Label
non-obvious flows. Avoid all-to-all networks.

### `small-multiples`

Minimum:

- 3 `[data-panel]`;
- 6 `[data-data-point]`;
- 1 `[data-unit]`;
- 2 `[data-annotation]`;
- 1 `[data-decision]`;
- 2 encoding tokens.

Use the same axes, period, unit, panel size, and encoding across every panel.
Annotate the cross-panel pattern, not each obvious value.

## Composition

- Default to `16:9` at 1600 × 900 for the master Exhibit.
- Keep header at 7%–18% of canvas area and the main visual at 58%–82%.
- In `topic` mode, reserve a compact tail row for the recommendation; do not
  move it into the header or below the source footer.
- Use direct labels and thin rules instead of large card containers.
- Use alignment before boxes; use boxes only for real grouping or state.
- Keep brand and attribution subordinate.
- Recompose `4:5`, `1:1`, and `A4` derivatives; never crop the master.

## Visual review by template

Ask:

- Matrix: Can differences be scanned down columns without reading sentences?
- Tree: Can every path be followed without guessing branch meaning?
- Driver tree: Does each level answer one consistent “why/how much” question?
- Positioning: Are axes independent, directional, and defensible?
- Waterfall: Does every component reconcile mathematically?
- Roadmap: Are gates and dependencies more visible than task descriptions?
- Operating model: Are roles, capabilities, flows, and outcomes distinguishable?
- Small multiples: Can the cross-panel pattern be seen before reading labels?
