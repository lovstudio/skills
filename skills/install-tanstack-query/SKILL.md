---
name: lov-install-tanstack-query
description: >
  Initialize or refactor a frontend project to use TanStack Query as the
  unified server-state layer. Use when the user asks to install TanStack Query,
  initialize query infrastructure, migrate ad hoc fetch/invoke/useEffect request
  state, standardize query keys, or make app network requests share one cache
  model. Also trigger when the user mentions "初始化 TanStack Query",
  "重构网络请求", "统一请求缓存", "install-tanstack-query",
  "TanStack Query refactor", or "useInvokeQuery".
license: MIT
compatibility: >
  React / TypeScript / JavaScript frontend projects, including Vite, Next.js,
  Tauri, Electron, and SPA apps. Requires the project's package manager.
metadata:
  author: contributors
  version: "0.1.1"
  tags: tanstack-query react-query frontend refactor tauri network
---

# install-tanstack-query — TanStack Query 初始化与重构

Use this skill to add TanStack Query to a project or refactor existing request
state into a shared query/mutation layer.

## When to Use

- The user asks to install or initialize TanStack Query / React Query.
- The project has repeated `useEffect + useState + fetch/invoke` request code.
- The user wants all network-backed reads to share cache, refetch, invalidation,
  and loading/error behavior.
- A Tauri app uses many `invoke()` reads that should be treated as server state.
- The user mentions RTK Query but the project already uses, or prefers,
  TanStack Query.

## Workflow

### Step 1: Read Local Rules First

Before changing files, inspect local instructions and project shape:

```bash
pwd
find .. -name AGENTS.md -print
rg -n "@tanstack/react-query|react-query|@reduxjs/toolkit|createApi|useQuery|useMutation|fetch\\(|invoke\\(" package.json src app pages components 2>/dev/null
```

Honor project-specific constraints. If local instructions say not to run
`build`, do not run it. Prefer `rg` and inspect existing patterns before
adding new abstractions.

### Step 2: Classify Request Code

Separate code into three buckets:

| Bucket | Examples | TanStack Query? |
|---|---|---|
| Server state reads | list/get/search/version/status/catalog/settings loaded from network or Tauri backend | Yes, `useQuery` |
| Server state writes | save/delete/toggle/install request, followed by cache changes | Yes, `useMutation` |
| Imperative side effects | terminal I/O, file open, clipboard, app relaunch, installer progress events, streaming channels | Usually no |

Do not force command-style effects into Query just to make the code look
uniform. The goal is unified server state, not hiding every side effect.

### Step 3: Install Only If Needed

Check `package.json` first. If TanStack Query is absent, detect package manager
from lockfiles and install:

```bash
pnpm add @tanstack/react-query
npm install @tanstack/react-query
yarn add @tanstack/react-query
bun add @tanstack/react-query
```

Only add persistence or devtools when the project already uses them or the user
explicitly asks:

```bash
pnpm add @tanstack/react-query-persist-client @tanstack/query-sync-storage-persister
pnpm add -D @tanstack/react-query-devtools
```

### Step 4: Add Provider

Add one top-level `QueryClientProvider` near the app root. Keep it consistent
with the existing architecture.

Recommended defaults:

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: Infinity,
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

root.render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
);
```

Adjust defaults for product needs. Data that changes frequently should use a
shorter `staleTime`, polling, streaming, or explicit invalidation.

### Step 5: Create Shared Query Infrastructure

Prefer small local wrappers over scattering raw `useQuery` calls everywhere.

For Tauri apps:

```ts
import { invoke } from "@tauri-apps/api/core";
import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
  type UseQueryOptions,
  type UseMutationOptions,
} from "@tanstack/react-query";

type InvokeQueryOptions<TQueryFnData, TData> = Omit<
  UseQueryOptions<TQueryFnData, Error, TData, QueryKey>,
  "queryKey" | "queryFn"
>;

export function useInvokeQuery<TQueryFnData, TData = TQueryFnData>(
  queryKey: QueryKey,
  command: string,
  args?: Record<string, unknown>,
  options?: InvokeQueryOptions<TQueryFnData, TData>,
) {
  return useQuery<TQueryFnData, Error, TData, QueryKey>({
    queryKey,
    queryFn: () => invoke<TQueryFnData>(command, args),
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    ...options,
  });
}

type InvokeMutationOptions<T, V> = Omit<UseMutationOptions<T, Error, V>, "mutationFn">;

export function useInvokeMutation<T, V = void>(
  command: string,
  invalidateKeys?: QueryKey[],
  options?: InvokeMutationOptions<T, V>,
) {
  const queryClient = useQueryClient();
  return useMutation<T, Error, V>({
    mutationFn: (variables) => invoke<T>(command, variables as Record<string, unknown>),
    ...options,
    onSuccess: (data, variables, context, mutation) => {
      options?.onSuccess?.(data, variables, context, mutation);
      invalidateKeys?.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: key });
      });
    },
  });
}
```

Add stable query keys:

```ts
export const queryKeys = {
  projects: ["projects"] as const,
  settings: ["settings"] as const,
};
```

For REST apps, use the same structure but wrap the project's API client instead
of Tauri `invoke()`.

### Step 6: Refactor Incrementally

Start with duplicated and user-visible requests:

1. Replace manual read state:

```tsx
const { data = [], isLoading, error, refetch } = useInvokeQuery<Item[]>(
  queryKeys.items,
  "list_items",
);
```

2. Replace write requests:

```tsx
const saveItem = useInvokeMutation<Item, { item: Item }>(
  "save_item",
  [queryKeys.items],
);
```

3. Use `queryClient.setQueryData()` for optimistic toggles when the UX needs
instant feedback.

4. Keep local UI state local. Dialog open state, form drafts, selected tabs,
and filters usually do not belong in TanStack Query.

5. Do not break existing streaming subscriptions. If a stream already pushes
data into `queryClient.setQueryData()`, keep that pattern.

### Step 7: Verification

Run the lightest reliable checks allowed by the repo:

```bash
pnpm exec tsc --noEmit --pretty false
npm run typecheck
yarn typecheck
bun run typecheck
```

Do not run heavy builds or dev server commands if local instructions forbid
them. For UI-heavy changes, suggest browser verification or screenshots after
type checks pass.

## Final Response Checklist

Report:

- What query provider/wrappers/keys were added or reused.
- Which request flows moved to TanStack Query.
- Which imperative flows intentionally stayed command-driven.
- Which checks were run and whether any warnings remain.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
