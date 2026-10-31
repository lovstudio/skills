# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-app-generator` | Generates or standardizes a whole app and declares this Skill in `depends_on` | upstream orchestrator | It calls this Skill for the server-state layer; this Skill never scaffolds apps |
| `lov-optimize-tauri-backend` | Splits the Tauri backend, consolidates commands into typed routers, and centralizes frontend `invoke()` in one adapter | adjacent atom | See Overlap Decisions |
| `lov-app-professional-design` | Diagnoses app performance architecture: startup, incremental data bridges, cache invalidation, concurrency | optional upstream atom | It may decide what to cache; this Skill implements the query layer |
| `lov-refactor-api` | Deduplicates backend APIs while keeping call contracts | not composed | Backend-side change; query keys follow whatever API it keeps |
| `lov-install-shadcn-ui` | Installs and brand-configures shadcn/ui | not composed | Sibling installer with no shared state |

## Atomic Handoffs

```text
optional: lov-app-generator (new or standardized app with server state)
                |
                v
lov-install-tanstack-query
  input: a React/TypeScript frontend (Vite, Next.js, Tauri, Electron, SPA)
  output: one QueryClientProvider, stable query keys, query/mutation wrappers,
          request flows moved to useQuery/useMutation, typecheck evidence
```

This Skill owns acceptance of the query layer: provider placement, key
stability, invalidation after writes, and the checks the repo allows.

## Overlap Decisions

`lov-optimize-tauri-backend` owns the Rust command surface and the frontend
invoke adapter that maps old command names onto consolidated routers. This Skill
owns the cache layer above it. When both apply to one app, the query wrappers
import `invoke` from that adapter rather than `@tauri-apps/api/core`, so commands
moved behind a router keep resolving.

Imperative effects stay outside the query cache in both Skills.

## Composition Decision

Single Skill. Installing the package, adding the provider, creating wrappers and
keys, and migrating request flows share one cache model and one acceptance
check; none of the steps is useful alone, so a Kit adds nothing.
