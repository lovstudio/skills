# Align WeChat UIUX — Parity Model

Use this model to identify the earliest broken layer. Later layers may compensate
for earlier mistakes, so a visually plausible screen is not proof of correctness.

## Layer stack

| Layer | Question | Typical evidence | Typical defect |
|---|---|---|---|
| Acquisition | Did the product read the correct record and assets? | database path, table, rowid, resource ID | stale database, wrong table, missing media |
| Decoding | Was packed/compressed/escaped content decoded correctly? | raw bytes, decoded XML/JSON | binary fallback, double escaping |
| Identity | Who sent, received, owns, or appears in the event? | columns, group prefix, participant fields | avatar/name/direction mismatch |
| Structure | Which types are direct versus nested? | XML/JSON hierarchy | nested quote type overrides outer type |
| Canonical semantics | What product object is this? | positive and negative rules | system event treated as file/card/video |
| Presentation contract | What normalized content do consumers receive? | typed payload | chat and export invent different text |
| Routing | Which component family owns it? | renderer branch | generic bubble used for separator/event |
| Visual grammar | How is meaning expressed? | official/current screenshots | wrong avatar, bubble, density, hierarchy |
| Interaction | What can the user do in every state? | keyboard/runtime checks | fake button, missing menu, broken IME |
| Consumer parity | Do search/copy/export/archive agree? | cross-surface assertions | raw XML leak or inconsistent label |
| Verification | Was the requested state observed? | exact fixture/runtime evidence | build success mistaken for product proof |

## Canonical object principles

### Storage type is evidence, not meaning

A database type may host several app subtypes. A nested quoted message may contain
its own type. A raw media code may overlap a structured app-message code. Resolve
meaning from the smallest sufficient set of structural facts.

### Direct child wins at its layer

When the outer object owns a direct `type`, nested content must not override it.
Parse the owner block first, then decode explicitly embedded objects.

### Positive plus negative rules

Every classifier needs:

- positive structural fields that must be present;
- the nearest ordinary object that must remain outside the classifier;
- an unknown/future variant behavior;
- preserved raw diagnostics.

Keyword-only rules are acceptable only as a narrow fallback with strict context.

### Stable identity is part of UX correctness

Preserve the exact source identity supported by the product, such as database,
table, and rowid. Search locate, copy context, exports, and diagnostics should not
replace it with approximate time, contact, or body matching.

## Failure patterns

### CSS-first compensation

Symptom: a card is visually hidden until it resembles a system notice.

Underlying defect: canonical type or component routing remains wrong, so search,
copy, export, selection, sizing, or later variants still behave as a card.

### Independent consumer parsing

Symptom: chat looks correct but export emits XML or search labels the object as a
file.

Underlying defect: each consumer interprets raw content independently instead of
using one presentation payload.

### Screenshot overreach

Symptom: one static state is copied, but focus, menu, missing media, time grouping,
or narrow width diverges.

Underlying defect: evidence captured appearance without interaction and state.

### Generic component leakage

Symptom: system events gain avatars, bubbles, badges, or action styling because
the generic message component supplies them.

Underlying defect: the semantic object was routed to the wrong component family
or the shared primitive lacks a semantic variant.

## Root-cause statement template

Write one concise engineering statement:

> The product observed [RAW STRUCTURE] but classified it as [CURRENT MEANING]
> because [EARLIEST BROKEN RULE]. The canonical object is [INTENDED MEANING],
> which requires [PRESENTATION CONTRACT] across [CONSUMERS].

Keep this statement in engineering output, not user-visible product copy.
