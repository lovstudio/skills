# Skill Group Composition

## Nearby Skills Inspected

- `frontend-design`: creates or refines production frontend interfaces and supplies interaction, visual hierarchy, responsive, and accessibility requirements. It does not own the option-count threshold, value compatibility, or real scroll verification.
- `lov-fix-general`: diagnoses and repairs a reported error from reproduction through verification. It may supply a root-cause report such as a Dialog scroll lock blocking portaled content, but it does not define the reusable searchable-Select acceptance contract.
- `lov-install-shadcn-ui`: installs and configures shadcn/ui and its theme. Installation is adjacent infrastructure, not an implementation of searchable Select behavior in an existing component system.
- `lov-better-css`: refactors CSS and Tailwind usage. It may clean styles after a component change, but it does not own selection semantics, search, keyboard behavior, or popup scrolling.
- `lov-app-professional-design`: designs cross-layer performance architecture. A local Select interaction defect does not require its lifecycle and data-architecture workflow.

## Atomic Handoffs

- Upstream atom — optional `frontend-design`: input is a product or accessibility brief; output is the approved control behavior and visual constraints. Invocation ends before implementation. This Skill owns final code and interaction acceptance.
- Upstream atom — optional `lov-fix-general`: input is a reproducible Select defect; output is a root-cause report with the failing event/render path. This Skill owns the shared component repair and boundary regression matrix.
- Core atom — `lov-frontend-select-with-search`: input is a frontend repository plus a Select search or scrolling requirement; output is a compatible code patch, Select inventory, and verified search/scroll/keyboard evidence.
- Downstream atom — project test, CI, or release workflow: input is the accepted patch and verification report; output is repository-wide or release-channel confidence. It does not redefine the component contract.

All handoffs are artifact-based. There is no sibling Skill required at runtime.

## Overlap Decisions

The inspected Skills are broader design, diagnosis, installation, CSS, or architecture capabilities. None owns the same user-visible outcome. This Skill stays intentionally narrow: it implements and verifies Select threshold search, long-list scrolling, compatibility, and accessibility. It reuses an existing project primitive or component library rather than installing a new design system.

## Composition Decision

This source is a Single Skill. Inventory, implementation, modal/portal repair, accessibility, and verification are inseparable parts of one user-visible outcome and share one acceptance boundary. They are not independently useful modules that justify a self-contained Skill Kit.
