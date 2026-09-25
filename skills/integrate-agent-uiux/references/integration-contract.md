# Agent UI Integration Contract

## Boundary

The UI is a controlled consumer of normalized state. It must not know provider
payloads, gateway routes, database records, token secrets, or reconnection rules.

```text
provider or local runtime
        -> host transport/domain layer
        -> one normalized adapter
        -> AgentConversation props
        -> transcript, interaction, composer
```

The host owns fetching, streaming, persistence, cancellation, authentication,
and send idempotency. The UI owns presentation, ephemeral expansion state,
draft interaction, accessibility, and user-visible failure recovery.

## Normalized entities

### AgentMessage

- `id`: stable across refreshes; never use array index.
- `role`: `user`, `assistant`, `tool`, or `status`.
- `content`: display-ready text after removing internal orchestration metadata.
- `format`: `markdown`, `plain`, or `code`.
- `timestamp`: ISO string or `null`.
- `title`: optional localized display label.
- `agentPhase`: `commentary` or `final` for assistant messages.
- `toolCallId`: stable provider call ID when available.
- `toolStatus`: `running`, `completed`, or `failed` for tool messages.

### AgentSessionState

Use one visible state at a time: `idle`, `working`, `waiting`, `error`, or
`completed`. Keep `canSend`, `canResume`, and optional diagnostic `contextId`
separate from the state label; status is not automatically an action.

### PendingInteraction

Represent choice, confirmation, and free-text questions as bounded display data.
The UI returns selected values to a host callback. Provider-specific submission
syntax stays in the adapter.

### AgentAttachment

UI attachments contain an opaque ID, display name, kind, and optional local
preview URI. Never treat a phone/browser filename as a trusted backend path.

## Adapter invariants

1. Normalize at one seam; do not scatter provider checks across components.
2. Preserve message order and stable IDs through background refresh.
3. Merge call/result events by `toolCallId` where the provider splits them.
4. Mark only the latest unresolved tool event as running when status is inferred.
5. Strip internal metadata before display, but retain raw data in the host layer
   when audit/debug access is authorized.
6. Limit large tool payload previews and keep full details user-expandable.
7. Keep pending interactions separate from transcript text so they remain usable.

## Send and retry contract

`onSend` receives trimmed text, attachments, and a stable `clientRequestId`.
The host must reuse that ID when retrying an unconfirmed request. On failure:

- keep the draft and attachments;
- show a short user-facing explanation;
- expose copyable diagnostic detail including the request/context ID;
- do not append a user message until the host's optimistic-update policy is explicit;
- allow retry without duplicating a confirmed turn.

Clear the draft only after the host callback resolves. Disable duplicate submit
while the same request is in flight.

## Realtime and scroll contract

- Hydrate a coherent snapshot first, then apply ordered updates or refetch after
  scoped invalidations.
- Coalesce rapid updates; avoid rerendering the entire list per token.
- Auto-follow only when the user is already near the bottom.
- If the user has scrolled away, retain position and show “jump to latest”.
- Reconnect or reconcile in the host layer without replacing valid content with
  an empty loading state.

## Platform mapping

The bundled React Native and React templates intentionally share `types.ts`,
`model.ts`, and `markdown.ts`. The platform view layer maps the same semantic
tokens into `StyleSheet` values or CSS custom properties. Applications may swap
the Markdown renderer or virtualized list later without changing the adapter.
