# Skill Group Composition

## Nearby Skills Inspected

- `lov-skill-creator` — creates the standard trust bundle, including
  `cases/cases.json`, but stops at validated local installation. It is an
  optional upstream atom, not an invocation dependency.
- `lov-skill-publisher` — publishes validated source, updates the unified
  catalog, refreshes website caches, and verifies the live detail page. It is an
  optional downstream atom for targets that are already public.
- `lov-skill-pricing` — produces pricing evidence before a normal release. A
  case-only content update does not change pricing, so it is not composed unless
  the downstream publisher detects a commercial change.
- `lov-skill-optimizer` — audits or improves an entire Skill. It does not own
  acceptance evidence or append one case, so it is not composed.
- `lov-share-session` — reads and redacts the accepted Agent transcript, uploads
  the immutable snapshot, and returns a server-priced paid URL. **Required
  composed dependency**; this Skill must not recreate its auth or upload logic.
- LovStudio `fetchSkillShowcase` — not a Skill. It is the website consumer that
  reads the owning repository's `cases/cases.json` and refreshes under the
  `skill-cases:<id>` cache tag.

## Atomic Handoffs

- Optional upstream artifact: a validated Skill source created by
  `lov-skill-creator`; ownership ends when its local trust bundle passes.
- Core input: one completed Skill invocation, explicit user acceptance for both
  the public summary and paid transcript upload, the minimum prompt, real
  input/output evidence, and any approved public assets.
- Required intermediate artifact: `lov-share-session --json` output containing
  the paid URL, target Skill, case ID, pricing rule, and server-derived Credits
  price. Ownership returns here only after that contract validates.
- Core output: one privacy-safe, deduplicated public case in the target's
  `cases/cases.json`, with a stable ID, evidence SHA-256, and a link to the paid
  full Session. This Skill owns the correctness of that mutation.
- Optional downstream artifact: the validated target source plus case ID and
  fingerprint. `lov-skill-publisher` owns remote push, cache refresh, and the
  final public page state.
- Final acceptance for a public request belongs to this Skill only after it
  independently re-reads both the public JSON and the LovStudio detail page.

## Overlap Decisions

No inspected Skill owns the same combined outcome. Creator only creates the
initial trust bundle; Share Session owns transcript publication; Publisher
publishes arbitrary validated changes; Optimizer reviews the whole Skill. This
Skill orchestrates those atoms without copying their implementations.

## Composition Decision

This remains one orchestration Skill with a declared runtime dependency.
Qualification and mutation share one context; `lov-share-session` is the required
paid-transcript atom, and `lov-skill-publisher` remains an optional downstream
artifact handoff. A case is not written when the required Session atom fails.
