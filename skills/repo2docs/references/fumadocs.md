# Fumadocs reference (for repo2docs)

Just enough Fumadocs to author and configure a polished docs site served under
`/docs`. For the authoritative, version-current docs, see
https://fumadocs.dev — this file captures the decisions that matter for this
skill, not the full framework.

## Scaffolding

`create-fumadocs-app` is the official scaffolder. The skill calls it
non-interactively via `scripts/scaffold_docs.py`. Relevant flags (confirmed CLI
surface):

```
--template +next+fuma-docs-mdx     # Next.js + Fumadocs MDX (default we use)
--src                              # put app/ and content/ under src/
--install                          # install deps
--no-git                           # we manage git ourselves
--search orama                     # built-in client search
--pm pnpm|npm|yarn|bun
```

Other templates exist (`waku`, `react-router`, `tanstack-start`, `+static`). We
default to Next.js because Vercel + basePath is the smoothest path to
`{id}.lovstudio.ai/docs`.

## Directory layout (with `--src`)

```
src/
  app/
    (home)/            # optional landing area
    docs/
      [[...slug]]/page.tsx   # renders a doc page
      layout.tsx             # DocsLayout (sidebar, nav)
    layout.config.tsx        # shared nav/links/title
    layout.tsx               # RootProvider
  content/
    docs/
      index.mdx
      meta.json              # sidebar order for this folder
      guides/
        meta.json
        *.mdx
  lib/
    source.ts                # loader() binding content → source
source.config.ts             # defineDocs / frontmatter schema
next.config.mjs
```

Without `--src`, drop the `src/` prefix (`app/`, `content/`, `lib/`).

## The `/docs` basePath — the key gotcha

The site must live at `domain/docs`, NOT `domain/`. Two distinct concerns:

1. **Next.js `basePath`** — makes the WHOLE app serve under `/docs`. Set in
   `next.config.mjs`:
   ```js
   const config = {
     basePath: '/docs',
     // ...
   };
   ```
   `scaffold_docs.py` injects this automatically. With basePath set, Next.js
   prefixes all routes and assets with `/docs`; `<Link>` hrefs stay root-relative
   (`/guides/x`) and Next adds the prefix.

2. **Fumadocs page routing** — the docs themselves already mount at `/docs`
   inside the app (the `app/docs/` route). With Next `basePath: '/docs'` ALSO
   set, the docs pages would end up at `/docs/docs`. Pick ONE of:
   - **Recommended**: keep Fumadocs at the app ROOT (move the docs route to
     `app/[[...slug]]/`) and rely on Next `basePath: '/docs'` to provide the
     `/docs` prefix. Simpler mental model: app root = docs, basePath shifts
     everything to `/docs`.
   - Or: leave Fumadocs at `app/docs/` and do NOT set Next basePath — but then
     the deploy must route the subdomain root to it, which is messier.

   Default to the first. After scaffolding, if the template put docs under
   `app/docs/`, move it to the root route group so basePath alone yields `/docs`.
   Verify with `pnpm build` + `pnpm start` then `curl localhost:3000/docs`.

If a page renders 404 under `/docs`, it's almost always a double-prefix
(`/docs/docs`) or a missing basePath. Check both.

## Authoring MDX

Front-matter per page:

```mdx
---
title: Getting Started
description: Install and run your first command
---
```

`meta.json` controls sidebar order and grouping per folder:

```json
{
  "title": "Guides",
  "pages": ["installation", "configuration", "deployment"]
}
```

Use `"---Section---"` separators and `"[Label](url)"` items in `pages` for
dividers/external links.

## Built-in MDX components (import from fumadocs-ui)

Use these for a polished, non-boilerplate feel:

- `<Cards>` / `<Card>` — link grids on landing/index pages
- `<Tabs>` / `<Tab>` — multi-language install or code variants
- `<Steps>` / `<Step>` — numbered getting-started sequences
- `<Callout type="info|warn|error">` — admonitions
- `<TypeTable>` — render prop/config tables for API reference
- Auto syntax-highlighted code fences (```ts, ```bash) with copy buttons

Example index page:

```mdx
---
title: MyProduct
description: Short tagline
---

import { Cards, Card } from 'fumadocs-ui/components/card';

<Cards>
  <Card title="Getting Started" href="/getting-started" />
  <Card title="Guides" href="/guides" />
  <Card title="API Reference" href="/api" />
</Cards>
```

## Branding (optional, Lovstudio Warm Academic)

Fumadocs theming is Tailwind-based. To match Lovstudio, set CSS variables in the
global stylesheet:
- primary / accent → terracotta `#CC785C`
- background → `#F9F9F7`, foreground → `#181818`

Keep it light-touch; a clean default Fumadocs theme already looks professional.

## Build & verify

```bash
pnpm build         # fails loudly on broken MDX links / bad imports
pnpm start         # serve the production build
curl -sI localhost:3000/docs | head -1   # expect 200
```

Fix all build errors before deploying — Vercel will fail the same way.
