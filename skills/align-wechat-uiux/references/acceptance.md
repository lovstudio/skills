# Parity Case and Acceptance Contract

Use one case per semantic discrepancy. Multiple screenshots may belong to one
case when they represent states of the same canonical object.

## Required case sections

### Identity

- `case_id`: stable kebab-case ID.
- `surface`: product surface such as `chat.timeline` or `contacts.profile`.
- `platform`: matching WeChat platform/version/theme context.
- `status`: `observed`, `modeled`, `implemented`, or `verified`.

### Evidence

- `official_reference`: what official behavior was observed and where.
- `product_observation`: current product behavior and exact entry.
- `raw_record`: raw XML/JSON/database/event facts.
- `implementation`: relevant parser/model/component/style/test symbols.

Evidence entries may be file paths, URLs, stable record IDs, screenshot labels,
or precise textual observations. Keep private data out of reusable examples.

### Semantic contract

- `storage_types`: outer and nested types with ownership.
- `canonical_type`: stable product meaning.
- `participants`: sender, target, conversation, direction rules.
- `content_source`: authoritative display text/media/state source.
- `identity_fields`: exact source identity retained.
- `raw_invariants`: structural facts that define the classifier.
- `downstream_consumers`: surfaces that must share the presentation.

### Experience contract

- `required`: layout, content, controls, state, and interaction that must exist.
- `forbidden`: misleading artifacts that must be absent.
- `responsive`: narrow/wide expectations.
- `accessibility`: names, keyboard, focus, semantics.
- `error_and_debug`: user-facing explanation and copyable diagnostic expectations.

### Verification

- `parser_checks`: positive, negative, unknown/future fixtures.
- `consumer_checks`: chat/search/copy/export/archive/notification assertions.
- `visual_checks`: official/product comparison states.
- `runtime_checks`: exact record or deterministic fixture observed in the app.
- `quality_commands`: focused tests, relevant suite, typecheck, lint, build.
- `integration_checks`: branch/main state and re-run requirements.

## Status rules

| Status | Minimum evidence |
|---|---|
| `observed` | official/current discrepancy recorded |
| `modeled` | canonical semantics and affected layers established |
| `implemented` | code and deterministic gates pass |
| `verified` | downstream, visual/interaction, and requested runtime path observed |

Do not mark `verified` when `runtime_checks` is empty or unavailable. If runtime
inspection is outside the task or blocked by current state, keep `implemented`
and name the exact gap.

## Minimum fixture matrix

1. Exact positive fixture from the reported case.
2. Nearest ordinary negative fixture.
3. One nested/escaped or group/direct variant when hierarchy matters.
4. One unknown or missing-field fallback when the format can evolve.

## Review questions

### Semantics

- Does the canonical type describe user meaning rather than storage encoding?
- Are direct and nested types assigned to the correct owner?
- Are identity and direction correct in direct and group conversations?
- Is raw diagnostic data preserved without leaking into product copy?

### UI and interaction

- Is the correct component family used?
- Are avatars, bubbles, timestamps, labels, badges, and actions present only when meaningful?
- Are hover, focus, pressed, selected, loading, disabled, error, and missing states covered?
- Is an input IME-safe?
- Is technical error detail copyable?

### Consumers

- Do chat, search, copy, export, archive, notification, and analysis agree?
- Can exact search/location still use stable source identity?
- Do old cached objects use the same presentation compatibility layer?

### Completion

- Was the exact requested state observed after integration?
- Were project-native tests run from the real integrated tree?
- Are version/platform limitations explicit?
