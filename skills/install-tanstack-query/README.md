# TanStack Query 接入 · TanStack Query Setup

![Version](https://img.shields.io/badge/version-0.2.3-CC785C)

Initialize or refactor a frontend project to use TanStack Query as the shared
server-state layer.

Independent source repository, also distributed through [lovstudio/skills](https://github.com/lovstudio/skills) — by [Lovstudio.AI](https://lovstudio.ai)

## Install

```bash
npx skills add lov-install-tanstack-query -g -y
```

Or through Claude Code plugin marketplace:

```text
/plugin marketplace add lovstudio/skills
/plugin install dev-tools@lovstudio
```

## Usage

Ask your coding agent:

```text
Use lov-install-tanstack-query to initialize TanStack Query in this app.
```

or:

```text
Use lov-install-tanstack-query to refactor request state into shared query keys and hooks.
```

## What It Does

- Detects existing request patterns and package manager.
- Installs `@tanstack/react-query` only when needed.
- Adds or reuses a top-level `QueryClientProvider`.
- Creates shared query keys and query/mutation wrappers.
- Refactors network-backed reads and writes into TanStack Query.
- Leaves imperative side effects outside Query when that is the safer model.

## License

MIT
