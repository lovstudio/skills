# Yoda Mobile Patterns Used as Reference

This Skill derives its baseline from an inspected mobile Agent session surface.
It copies interaction principles and public data shapes, not product branding,
private data, gateway credentials, or repository-specific state stores.

## Inspected seams

- `apps/mobile/src/App.tsx`: session detail screen, transcript rendering, tool
  expansion, Markdown blocks, safe links, scroll-follow behavior, composer, and
  user-visible retry diagnostics.
- `apps/mobile/src/markdown.ts`: dependency-free block and inline Markdown parser.
- `src/shared/mobile-session-display.ts`: reply-detail filtering and removal of
  orchestration-only metadata.
- `src/shared/mobile-tool-transcript.ts`: adjacent tool grouping, stable group
  identity, readable previews, and expanded formatting.
- `src/shared/mobile-session-interaction.ts`: bounded structured questions.
- `src/shared/mobile-api.ts`: display-ready message, session, interaction, and
  idempotent input contracts.

## Reusable decisions

1. **Four transcript roles.** User, assistant, tool, and status blocks have
   different semantics; role must not be inferred from visual alignment.
2. **Assistant phases.** Commentary and final output remain distinguishable so a
   user can choose concise or detailed display without losing the source record.
3. **Tool groups are progressive disclosure.** Consecutive tool events share a
   compact row, show running/completed/failed state, and expand on demand.
4. **Stable identity prevents remount churn.** A growing tool group keeps the
   first tool message ID while the latest entry changes.
5. **Markdown is bounded and safe.** Headings, paragraphs, lists, quotes, tables,
   code, emphasis, inline code, and allowlisted links cover the mobile reading
   path without rendering arbitrary HTML.
6. **Table cards fit narrow screens.** Each row becomes a label/value card rather
   than forcing a horizontally compressed grid.
7. **The transcript stays readable.** User blocks are visually distinct, Agent
   output favors document-like reading, and tool payloads use monospace detail.
8. **Live status is placed near the navigation/title context.** It is visible
   without consuming the transcript or masquerading as a primary action.
9. **Refresh is coherent.** Valid content stays visible while a scoped session
   invalidation schedules a bounded refresh.
10. **Send failure preserves work.** Draft and attachment selections survive an
    unconfirmed send, and diagnostic IDs are copyable for recovery.

## Intentional changes for portability

- Product names, colors, icons, localized copy, transport routes, and runtime IDs
  are injectable host concerns.
- Components receive controlled props rather than reading a global store.
- The templates avoid UI dependencies and expose a small theme contract.
- React Web uses semantic HTML and CSS; React Native uses platform primitives.
- The scaffold is a starting implementation. A host may replace rendering
  internals while retaining normalized types and acceptance behavior.
