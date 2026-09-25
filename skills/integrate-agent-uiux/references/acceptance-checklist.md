# Acceptance Checklist

## Data and state

- [ ] Stable IDs survive refresh, streaming updates, and tool completion.
- [ ] User, assistant, tool, and status roles render with correct semantics.
- [ ] Commentary and final phases can be filtered without corrupting source data.
- [ ] Running, completed, and failed tools are distinguishable without color alone.
- [ ] Empty, loading, working, waiting, offline/error, completed, and resumable states are visible.
- [ ] Pending choice, confirmation, and text interactions remain actionable.

## Reading and interaction

- [ ] Markdown headings, paragraphs, lists, quotes, tables, code, inline code, and links render.
- [ ] Only `http`, `https`, `mailto`, and `tel` links can open.
- [ ] Long code/tool output is selectable, bounded, and expandable.
- [ ] Adjacent tools group without remounting an already expanded group.
- [ ] New output follows only when the reader is near the end.
- [ ] A reader away from the end gets a clear jump-to-latest control.

## Composer and recovery

- [ ] Text input remains editable while a cold but resumable session can accept continuation.
- [ ] Empty submission is rejected; duplicate in-flight submission is prevented.
- [ ] Send/retry uses a stable client request ID.
- [ ] Failed sends preserve text and attachments and expose copyable diagnostics.
- [ ] Draft clears only after confirmed success.
- [ ] Keyboard, safe area, input focus, attachment removal, and submit affordance work on target devices.

## Accessibility and localization

- [ ] Every icon-only or compact control has an accessible name and role.
- [ ] Tool expansion communicates expanded/collapsed and running/completed/failed state.
- [ ] Touch targets meet the host platform minimum.
- [ ] Text can scale and remains selectable where useful.
- [ ] Status does not rely on color alone; focus order follows reading order.
- [ ] Visible strings use the host localization path or documented copy overrides.
- [ ] Reduced-motion settings are respected when motion is added.

## Engineering evidence

- [ ] `agent_uiux.py verify` passes for the integrated component directory.
- [ ] Host formatting, lint, typecheck, tests, and build pass.
- [ ] A real conversation covers assistant Markdown, tool progress, pending interaction, retry, and final response.
- [ ] Native mobile changes are installed and verified on a real device when the host requires it.
- [ ] The final report separates verified facts from deferred or unavailable evidence.
