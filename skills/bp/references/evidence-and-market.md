# Evidence and Market Sizing

## Evidence classes

Every material claim belongs to one class:

| Class | Meaning | How to present |
|---|---|---|
| Fact | Directly supported by a reliable source | State with source and as-of date |
| Inference | Reasoned conclusion from facts | Label as inference and show bridge |
| Assumption | Planning input not yet verified | Label and sensitivity-test |
| Missing | Necessary evidence not yet available | Keep as a named gap, never fill by intuition |

## Source hierarchy

Prefer sources in this order:

1. Product database, payment processor, analytics, contracts, repository history.
2. Direct customer interviews, support conversations, signed pilots, orders.
3. Official government, company, exchange, standards, or research data.
4. Reputable analyst/research reports with disclosed methodology.
5. Quality secondary reporting.
6. Search snippets, social posts, and unsourced aggregations only as leads.

Time-sensitive facts must be checked live. Capture the date and exact URL. If a
source is inaccessible, say so in the report.

## Evidence ledger format

| ID | Claim | Status | Source | As of | Slide | Notes / next action |
|---|---|---|---|---|---|---|
| E-001 | ... | fact | URL or dashboard export | YYYY-MM-DD | 6 | ... |

Use stable IDs in the outline so charts and slide copy can be traced back.

## TAM / SAM / SOM methodology

Do not paste a broad “AI will be worth $X trillion” forecast into a deck. Build a
bridge from actual buyer to price.

### TAM

All plausible buyers × annual value of the complete category.

```text
TAM = global buyer count × realistic annual spend per buyer
```

Use a top-down source only as a cross-check.

### SAM

The part of TAM reachable by current product scope, geography, regulation, and sales
motion.

```text
SAM = target buyer count in reachable segments × current annual contract value
```

### SOM

A three-to-five-year operating plan, not a percentage chosen for visual symmetry.

```text
SOM = acquired accounts × annual price × expected retention
```

Show the channel capacity or sales capacity that makes acquired accounts credible.

## Scenario model

Use at least two scenarios:

- conservative: slower conversion, lower price, longer sales cycle;
- base: management plan;
- upside: only if named leading indicators improve.

Never present the upside case as a forecast. Put assumptions next to the chart.

## Metric hygiene

- Distinguish downloads, clones, activated users, active users, retained users, and
  paid users.
- Distinguish trial, activation, conversion, renewal, and revenue.
- Use cohorts for retention; do not infer retention from cumulative installs.
- Define the period, denominator, timezone, duplicates, bots, and internal usage.
- Put “as of YYYY-MM-DD” on changing metrics.
- When the number is zero, say zero; the honest gap can define the financing thesis.
