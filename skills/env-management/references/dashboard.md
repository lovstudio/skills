# Dashboard interaction contract

The Dashboard is an operations ledger, not a secret editor. Its visual direction is an industrial paper console: warm ledger surface, dark ink, sharp signal colors, mono operational labels, and dense but readable account rows.

## Information hierarchy

1. Summary strip: total Keys, active bindings, expiring Keys, invalid Keys.
2. Filters: platform, account, health, and text search.
3. Key ledger: locator, variable, backend, effective health, expiry, validation age, and target chips.
4. Binding desk: target, variable name, and selected locator.
5. Status desk: administrative status and manual validation result.

Secret values and secret references are absent from every response and DOM node.

## Controls

- Status is displayed as a badge, not styled like an action.
- Binding and status mutations use labeled controls because the consequences are operational and not obvious from icons.
- One primary action appears per mutation form.
- There is no destructive control in the Dashboard.
- Every field has a visible label, keyboard focus state, validation message, and disabled pending state.

## Responsive and accessibility acceptance

- At narrow widths, the summary becomes two columns and each ledger row becomes a labeled record instead of a clipped table.
- Keyboard traversal reaches filters, rows, and forms in reading order.
- Color is never the only health signal; every badge includes text.
- Live mutation results use an `aria-live` region.
- Motion respects `prefers-reduced-motion`.
