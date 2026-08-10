---
name: sgc-repo2docs
description: >
  Turn any folder of source material — a code repository, a pile of articles, a
  mixed knowledge dump with images — into a professional, polished Fumadocs
  (Next.js) documentation website, then deploy it to
  https://{product-id}.lovstudio.ai/docs. Works by reading the folder one unit at
  a time and incrementally growing and refining the docs structure and detail, so
  it scales to large folders and handles images as first-class content (copied
  into the site, embedded inline, auto-galleried). Trigger when the user wants to
  "generate docs", "build a docs site", "make a documentation website", "fumadocs",
  points at a code repo OR a content/article folder, or says "为项目生成文档",
  "把这个文件夹做成文档站", "做文档站", "生成文档网站", "整理成知识库网站".
license: MIT
compatibility: >
  Portable Agent Skills format. Requires Node.js 18+, npx, git, and Python 3.8+.
  Image optimization optionally uses Pillow (graceful fallback to verbatim copy).
  Deployment delegates to the sgc-deploy-to-vercel skill (Cloudflare DNS
  auto-config needs CLOUDFLARE_API_KEY). The {product-id} subdomain and
  lovstudio.ai base domain are user-configurable.
depends_on:
  - sgc-deploy-to-vercel
metadata:
  author: lovstudio
  version: "0.2.0"
  tags: docs fumadocs documentation nextjs vercel codebase articles knowledge-base images
---

# repo2docs — Folder → Polished Docs Site (incremental)

Turn any folder of source material into a professional Fumadocs documentation
website and deploy it to `https://{product-id}.lovstudio.ai/docs`.

A code repo and a folder of articles are the same thing: **a folder of source
material**. There is one unified flow, not separate modes. The difference is only
in what each file contributes — code becomes explained API/usage docs; an article
becomes a presented page; an image becomes embedded media.

The core idea: **read the folder one unit at a time and incrementally refine the
docs.** Don't read everything then write everything. Each file you ingest updates
the evolving outline and fills in or improves pages — including earlier ones. This
scales past the context window and produces a coherent, deduplicated result.

## User Configuration

Defaults are portable. Base domain is `lovstudio.ai`; subdomain is the product id.
Deploy delegates to `sgc-deploy-to-vercel` (reads `CLOUDFLARE_API_KEY`).
See `references/user-config.md`.

## When to Use

- "用 fumadocs 给这个项目生成文档站并部署到 xxx.lovstudio.ai/docs"
- "把这个装满文章和图片的文件夹整理成一个文档网站"
- A code repo, an article collection, or a mixed knowledge folder needs a polished,
  navigable, image-rich docs site

## Workflow (MANDATORY — follow in order)

### Step 0: Resolve skill root

```bash
export SKILL_DIR="${SKILL_DIR:-$(pwd)}"   # or the installed sgc-repo2docs dir
```

If any network command times out in the sandbox, export the proxy once:

```bash
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7891
```

### Step 1: Collect inputs with AskUserQuestion

**Use `AskUserQuestion` BEFORE doing anything**, unless the user already gave all:

- **Source**: GitHub URL, local folder path, or current directory?
- **Product id**: the subdomain → `{product-id}.lovstudio.ai`. Propose a slug from
  the folder/repo name; confirm.
- **Title**: human-facing name for the docs.
- **Deploy now?**: deploy to Vercel + bind subdomain immediately, or generate only.

### Step 2: Resolve the source folder

| Source | Action |
|--------|--------|
| GitHub URL | `git clone --depth 1 <url> <tmp>/src` |
| Local path | use as-is (read-only) |
| Current dir | use `$(pwd)` |

Never write into the source folder. The docs site is a **separate** directory.

### Step 3: Inventory the folder

Build a manifest of every file, classified and ordered (overview material first):

```bash
python3 "$SKILL_DIR/scripts/inventory.py" --src "<src>" --out /tmp/manifest.json
```

The manifest lists `units` (path, kind ∈ article/code/image/pdf/office/data/other,
title guess, reading `order`) and `counts`. This is cheap — it does NOT read full
contents. You read contents later, incrementally. Use `counts` to gauge scale and
to decide whether to delegate batches to subagents (see Step 5 scaling note).

### Step 4: Scaffold the Fumadocs site

```bash
python3 "$SKILL_DIR/scripts/scaffold_docs.py" \
  --product-id "<id>" --out "<docs-out-dir>" --title "<Title>" --pm pnpm
```

Sets `basePath: '/docs'` and resets `content/docs/` to a placeholder. See
`references/fumadocs.md` for layout, the `/docs` double-prefix gotcha, and
components.

### Step 5: Copy images into the site

```bash
python3 "$SKILL_DIR/scripts/copy_assets.py" \
  --src "<src>" --site "<docs-out-dir>" --out /tmp/assets-map.json
```

This copies (and, if Pillow is present, downsizes/transcodes HEIC/TIFF/BMP) every
image into `public/assets/...` and returns a `{source-path: /assets/...}` map.
Reference images in MDX with the **root-relative** web path from the map
(`![](/assets/foo.png)`) — with basePath `/docs`, Next resolves it to
`/docs/assets/foo.png` automatically.

### Step 6: Incremental authoring loop (the core)

Initialize the outline from the folder's top-level structure — by default,
**preserve the source directory hierarchy as the sidebar** (a folder → a sidebar
group, its `meta.json`). Then walk `units` in `order` and, for each unit:

1. **Read** the unit (the file contents).
2. **Place it** in the evolving outline: a new page, a section of an existing
   page, or merged into a group index. Update the relevant `meta.json`.
3. **Write or refine** the MDX page:
   - For **articles/notes/PDF/office**: present the content as a real page —
     preserve the author's substance; clean up formatting; embed its images via
     the assets map; if a folder holds many images, render a gallery/grid.
   - For **code**: write explained docs — purpose, install, usage, public API,
     examples — derived from the code, README, and comments. Don't dump source.
   - For **images** with no surrounding article: group them into a gallery page
     for their folder.
4. **Refine backward**: as later units add context, improve earlier pages, the
   intro, cross-links, and sidebar order. The structure is *emergent and
   incrementally polished*, not one-shot.

Quality bar: a **professional, polished** site — coherent IA, working internal
links, real content (never lorem ipsum), inviting landing page, images that render
crisply. Use Fumadocs components (`<Cards>`, `<Tabs>`, `<Steps>`, `<Callout>`,
`<ImageZoom>`/gallery) per `references/fumadocs.md`.

**Scaling note (large folders)**: when `counts` is large, delegate batches to
subagents (Explore / general-purpose). Give each a slice of `units` + the assets
map; have it return structured page contributions and outline deltas (which group,
which order). The main thread owns and merges the evolving IA so the result stays
coherent. Don't let subagents each invent a separate top-level structure.

### Step 7: Verify the build locally

```bash
cd "<docs-out-dir>" && pnpm build    # must succeed — fix MDX/link/image errors
```

### Step 8: Deploy (if requested)

Delegate to `sgc-deploy-to-vercel` — do NOT reimplement Vercel/DNS here.
Ensure `package.json` "name" is a valid lowercase slug, then deploy with domain
`{product-id}.lovstudio.ai`. The site serves at `…/docs` via the basePath. After
deploy, **verify the live URL returns 200** (curl), not just that the alias was set.

## CLI Reference

`scripts/inventory.py` — enumerate + classify a folder:

| Argument | Default | Description |
|----------|---------|-------------|
| `--src` | (required) | Source folder |
| `--out` | stdout | Manifest JSON path |
| `--max-bytes` | `2000000` | Skip title-reading files larger than this |

`scripts/copy_assets.py` — images → `public/assets/`:

| Argument | Default | Description |
|----------|---------|-------------|
| `--src` | (required) | Source folder |
| `--site` | (required) | Fumadocs site root |
| `--max-width` | `1600` | Downscale wider images (needs Pillow) |
| `--no-optimize` | off | Copy verbatim, never transcode/resize |
| `--out` | stdout | Asset path-map JSON |

`scripts/scaffold_docs.py` — scaffold the site:

| Argument | Default | Description |
|----------|---------|-------------|
| `--product-id` | (required) | Slug → `{id}.lovstudio.ai` |
| `--out` | (required) | Output dir (separate from source) |
| `--title` | `=product-id` | Human-facing title |
| `--pm` | `pnpm` | Package manager |

## Dependencies

- Node.js 18+, `npx`, `git`, Python 3.8+
- Optional: Pillow (`pip install Pillow`) for image optimization
- Vercel CLI (`npm i -g vercel`) for deploy
- `sgc-deploy-to-vercel` skill (Vercel + Cloudflare DNS)

For Fumadocs structure, components, and config, see `references/fumadocs.md`.
