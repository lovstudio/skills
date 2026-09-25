# Searchable Select implementation playbook

Read this reference before changing a project. It defines the portability and verification details behind the controller workflow.

## 1. Inventory model

Create a compact matrix before implementation:

| Surface | Shared primitive | Option source | Expected count | Mode | Modal host | Existing API |
| --- | --- | --- | ---: | --- | --- | --- |
| Example field | `Select` | dynamic records | 18 | single | Dialog | controlled `value/onChange` |

Search for both shared wrappers and raw elements. In component projects, also search for Combobox, Listbox, Autocomplete, Menu, Popover, Command, Dialog, Sheet, Drawer, and form adapters. Verify runtime-generated options; static source counts are not enough.

Count actual displayed candidates. An explicit “none”, “all”, or placeholder row is a candidate because the user can select it. Optgroup headings are not candidates. The default threshold is strictly greater than 5.

## 2. Choose the smallest compatible architecture

Prefer this order:

1. Extend a project-wide Select primitive already used by the relevant call sites.
2. Configure an existing accessible Combobox/Autocomplete primitive.
3. Build a small adapter around the project's Popover and list primitives.
4. Add a new dependency only when the existing stack cannot meet accessibility and positioning requirements.

For 5 or fewer options, retain the native `<select>` when it already satisfies the product. For 6 or more, the custom branch must remain compatible with the original public API. A hidden native select can preserve form and change semantics, but it must not remain exposed as a duplicate accessible control. Framework-specific value setters and synthetic change dispatch must be verified rather than assumed.

Controlled and uncontrolled values need separate tests. Preserve empty strings, numeric-to-string conversion rules, disabled options, required state, `name`, form reset, and programmatic updates.

Multi-select is a separate interaction contract. Use a searchable multi-select listbox with visible selected values and removal behavior; never pretend a single-value combobox supports `multiple`.

## 3. Search semantics

A portable client-side matcher should:

- normalize labels and values with Unicode NFKC;
- apply locale-aware case folding;
- collapse repeated whitespace;
- split the query into non-empty terms;
- require every term to appear in the normalized label/value haystack;
- preserve source order unless the product has an explicit ranking rule.

Do not send local option labels to a remote search service unless the product requires it and privacy is addressed. For truly large or remote datasets, retain the same combobox contract but move retrieval, cancellation, loading, and error states into the project's data layer.

## 4. Popup sizing and scrolling

The listbox needs a real height boundary and scroll owner. Use a maximum height based on the viewport or positioning primitive's available-height variable, `overflow-y: auto`, overscroll containment, and `touch-action: pan-y`. Do not hide the only scroll affordance unless the product provides an equally discoverable alternative.

When a Select lives inside a modal, there may be two independent portals and two scroll locks:

```text
document body
├── Dialog portal
│   └── Dialog content and Select trigger
└── Popover portal
    └── searchable listbox
```

The Dialog can correctly lock background scrolling while incorrectly treating the Popover portal as background. The symptom is decisive: `scrollHeight` exceeds `clientHeight`, computed `overflow-y` is `auto`, but a real wheel gesture leaves `scrollTop` at zero.

Fix ownership before events:

1. Use the popup primitive's modal mode or supported allowlist so its content becomes an allowed scroll layer.
2. If supported and not clipped, portal into the modal's allowed container.
3. Register the popup content as a scroll-lock shard or equivalent.
4. Only when the library offers no ownership mechanism, document a bounded wheel/touch fallback and test nested scrolling at both ends.

Increasing `max-height`, adding a scrollbar class, or assigning `scrollTop` in a test does not prove the interaction works.

## 5. Accessibility contract

At minimum:

- trigger role `combobox`, accessible name, expanded state, and listbox relationship;
- searchbox label and active-descendant relationship where used;
- listbox/options with selected and disabled states;
- Arrow Up/Down navigation, Enter selection, Escape close, and Home/End when appropriate;
- active option scrolled into view with nearest-block behavior;
- focus moves to search on open and returns to the trigger on close;
- no duplicate native and custom controls in the accessibility tree.

Use the component library's documented accessible primitives when available. Do not combine incompatible ARIA patterns just to satisfy attribute checklists.

## 6. Verification matrix

### Static and state checks

- 0, 1, 5, 6, and many options;
- dynamic option addition/removal around the threshold;
- controlled, uncontrolled, disabled, required, empty, and form-reset behavior;
- duplicate labels with unique values;
- Chinese, Latin, mixed case, whitespace, and no-result queries.

### Real interaction checks

Open the popup in both an ordinary surface and each modal host. Read `clientHeight`, `scrollHeight`, `scrollTop`, and computed overflow for diagnosis, but send an actual mouse-wheel or trackpad event for acceptance. Confirm `scrollTop` changes, then select an item now visible after scrolling.

Repeat with keyboard navigation. Confirm escape closes only the popup, focus returns predictably, and the parent Dialog remains open. When practical, exercise touch panning on a real or emulated touch target; otherwise report it as unverified.

### Project gates

Run focused component tests when present, then typecheck, lint, tests, and build in the repository's documented order. Inspect console errors during the real interaction. Keep screenshots as supporting evidence, not as substitutes for event-state proof.

## 7. Completion report

Report:

- how many Select surfaces were inventoried and which shared primitive owns them;
- the exact threshold and whether placeholders count;
- compatibility preserved;
- the modal/portal scroll root cause and chosen ownership fix;
- real before/after scroll metrics and post-scroll selection evidence;
- keyboard, accessibility, build/test, browser, and touch coverage;
- any unsupported multi-select or remote-data boundary.
