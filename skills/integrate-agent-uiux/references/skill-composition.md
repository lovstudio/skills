# Skill Group Composition

## Nearby Skills Inspected

| Skill | Actual routing contract | Classification |
| --- | --- | --- |
| `lov-app-generator` | Creates or standardizes an entire React/Vite, Next.js, PWA, or Tauri application shell, including branding and delivery wiring. | upstream atom |
| `lov-mobile-adapt` | Scans and repairs mobile Web overflow, breakpoints, touch targets, safe areas, and navigation structure. | downstream atom |
| `frontend-design` | Builds or refines production frontend surfaces, visual hierarchy, interactions, responsiveness, and accessibility. | downstream atom |
| `lov-app-professional-design` | Repairs application performance architecture, lifecycle ownership, incremental data flow, and bounded concurrency. | not composed |
| `lov-integrate-lovstudio-llm-skill` | Connects a host app to LovStudio model APIs and related backend contracts. | upstream atom |

No inspected Skill owns the complete output of this Skill: a normalized Agent
conversation contract, reusable transcript/composer components, target-stack
scaffolding, host adapter guidance, and conversation-specific acceptance tests.

## Atomic Handoffs

| Stage | Owner | Input artifact | Output artifact | Acceptance owner |
| --- | --- | --- | --- | --- |
| Optional app creation | `lov-app-generator` | product brief | runnable app shell with package manifest | app generator owns the shell; this Skill owns only the later Agent UI integration |
| Optional model connection | LLM integration capability | provider/API requirements | typed send and stream/domain adapter | provider integration owns transport correctness; this Skill owns visible conversation behavior |
| Core Agent UI integration | `lov-integrate-agent-uiux` | existing project plus message/send contracts | normalized adapter, transcript, composer, theme binding, and verification report | this Skill owns all conversation UI acceptance criteria |
| Optional mobile repair | `lov-mobile-adapt` | integrated Web surface | responsive and safe-area corrections | mobile adaptation owns generic mobile layout; this Skill rechecks conversation behavior |
| Optional visual refinement | `frontend-design` | working Agent conversation components | host-specific visual polish using existing tokens | frontend design owns visual polish; this Skill retains message/state semantics |

Every handoff occurs through files or typed contracts. None is a runtime Skill
dependency. A caller may use only the core stage when the host app already exists.

## Overlap Decisions

- App generation is intentionally not duplicated: this Skill requires an existing
  host and adds only Agent conversation components and adapters.
- Generic responsive scanning is not duplicated: bundled components include safe
  defaults, while project-wide mobile remediation remains outside this Skill.
- Visual design is constrained to a semantic, tokenized baseline. Bespoke art
  direction remains a separate downstream task.
- Backend model access is not implemented in the component templates. The host
  passes controlled messages, state, interactions, and callbacks.
- Performance architecture is invoked only when live transcript transport or
  rendering exposes a measured lifecycle/throughput problem; it is not required
  for ordinary integration.

## Composition Decision

This source is a **Single Skill**. Auditing, normalizing, scaffolding, integrating,
and verifying are inseparable stages of one user-visible outcome. The React Native
and React templates are platform variants of the same contract, not independently
triggerable products. A Skill Kit would add routing overhead without creating a
meaningful standalone module boundary.
