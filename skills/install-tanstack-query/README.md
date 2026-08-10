# lov-install-tanstack-query

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

Initialize or refactor a frontend project to use TanStack Query as the shared
server-state layer.

Independent source repository, also distributed through [skill-publisher dev-skills](https://example.com/skills/dev-skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add skill-publisher/install-tanstack-query-skill --all -g
```

The aggregate bundle remains available:

```bash
npx skills add skill-publisher/dev-skills --all -g
```

Or through Claude Code plugin marketplace:

```text
/plugin marketplace add skill-publisher/dev-skills
/plugin install dev-tools@lov-dev
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
