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
- LovStudio `fetchSkillShowcase` — not a Skill. It is the website consumer that
  reads the owning repository's `cases/cases.json` and refreshes under the
  `skill-cases:<id>` cache tag.

## Atomic Handoffs

- Optional upstream artifact: a validated Skill source created by
  `lov-skill-creator`; ownership ends when its local trust bundle passes.
- Core input: one completed Skill invocation, an explicit user acceptance, the
  minimum prompt, real input/output evidence, and any approved public assets.
- Core output: one privacy-safe, deduplicated case in the target's canonical
  `cases/cases.json`, with a stable ID and evidence SHA-256. This Skill owns the
  correctness of that mutation.
- Optional downstream artifact: the validated target source plus case ID and
  fingerprint. `lov-skill-publisher` owns remote push, cache refresh, and the
  final public page state.
- Final acceptance for a public request belongs to this Skill only after it
  independently re-reads both the public JSON and the LovStudio detail page.

## Overlap Decisions

No inspected Skill owns the same outcome. Creator only creates the initial trust
bundle; Publisher publishes arbitrary validated changes; Optimizer reviews the
whole Skill. This Skill adds the missing acceptance, privacy, duplicate, and
case-specific live verification gate without copying those broader workflows.

## Composition Decision

This is a Single Skill with deterministic Python helpers. Case qualification,
mutation, and verification share one context and one user-visible outcome. The
remote publisher remains an optional artifact-level handoff because local-only
Skills are valid targets and remote publication has its own independent account,
catalog, pricing, and channel contract.
