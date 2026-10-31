# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-branding-consistency` | Audience, brand-role, component-convention, and information-visibility gate for reader-visible text | required gate (`depends_on`) | Consult it before a fix truncates, hides, or rewrites visible copy, such as ellipsis, line-clamp, or shortened labels |
| `lov-frontend-design` | Designs or refines a distinctive, interaction-consistent frontend, including pages, components, and navigation | adjacent atom | Route new interfaces and visual redesigns there; see Overlap Decisions |
| `lov-app-generator` | Generates or standardizes a whole app, choosing web, PWA, Tauri, or native macOS | not composed | This Skill adapts an existing web project; it never scaffolds one |
| `lov-better-css` | Removes redundant CSS and refactors styles in an existing Tailwind project | not composed | This Skill adds mobile rules only and leaves unrelated styles alone |
| `lov-app-optimizer` | Fixes runtime jank, battery drain, memory growth, and leaks with before/after evidence | not composed | Performance complaints on phones go there, not to layout fixes |

## Atomic Handoffs

```text
lov-mobile-adapt
  input: an existing web project (React, Vue, Next.js, Nuxt, Svelte, plain HTML/CSS)
  steps: scripts/scan_mobile_issues.py -> user picks categories ->
         fixes from references/mobile-patterns.md -> optional page-stack navigation
  gate:  lov-branding-consistency when a fix truncates or rewrites visible text
  output: fixed project, a clean re-scan, and a 375px-viewport check
```

This Skill owns acceptance of the adaptation: the re-scan result and the mobile
viewport checks listed in its Verify step.

## Overlap Decisions

`lov-frontend-design` also changes layout and navigation. This Skill keeps the
existing design language and leaves the desktop layout unchanged at the `md:`
breakpoint and above; it only converts navigation to a mobile page stack or a
bottom tab bar when the user picks that option. A redesign of either layout is a
`lov-frontend-design` request.

## Composition Decision

Single Skill. Scanning, scoping, fixing, and re-scanning share one issue list and
one acceptance check, and the scanner is only useful inside this loop, so a Kit
adds nothing.
