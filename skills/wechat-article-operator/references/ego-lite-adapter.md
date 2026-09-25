# ego lite Adapter

Use this adapter when `ego-browser` is available and an authenticated WeChat editor session must be reused.

## Required behavior

1. Read the installed `ego-browser` Skill completely before browser work.
2. Create one isolated task space for the user goal and reuse it through verification.
3. Open the exact article entry provided or recovered from current context.
4. Observe before acting; prefer semantic controls, then visual interaction, then scoped DOM evaluation.
5. Treat the main rich-text surface as a fragile editor:
   - perform a reversible write probe before substantial insertion;
   - verify the probe visually or from editor state;
   - remove the probe and confirm no empty wrapper remains;
   - use real keyboard or paste events to synchronize editor state.
6. Save, reload, and recapture article state.
7. Complete the task space in a dedicated final browser invocation after success.

## Control handoff

- If the user takes control, stop immediately.
- Do not seize control back automatically.
- Resume only after an explicit continue instruction.
- Keep the task space only when manual work remains; otherwise close it.

## Adapter boundary

Do not expose task-space IDs, selectors, DOM markers, editor tokens, or browser profile paths as user-facing output. Return article state, mutation results, and observed verification only.
