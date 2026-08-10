# sgc-repo2docs

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

Turn **any folder of source material** — a code repository, a pile of articles, a
mixed knowledge dump with images — into a professional **Fumadocs** documentation
website, and deploy it to `https://{product-id}.lovstudio.ai/docs`.

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## What it does

```
 a folder        inventory     scaffold Fumadocs      incremental         deploy
 of source   ──▶  + classify ──▶  (Next.js,       ──▶  authoring loop ──▶  {id}.lovstudio.ai
 (URL|local)      files          basePath=/docs)       (read 1 unit →      /docs
                                  + copy images          place → write →
                                  into public/           refine backward)
```

A code repo and a folder of articles are the same thing: a folder of source
material. One unified flow handles both. Instead of "read everything then write
everything", the agent reads **one unit at a time** and incrementally grows and
refines the docs structure and detail — so it scales past the context window and
stays coherent. Images are first-class: copied into the site, embedded inline,
auto-galleried.

## Install

```bash
git clone https://github.com/lovstudio/repo2docs-skill "${LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}/sgc-repo2docs"
```

Requires:
- Node.js 18+, `npx`, `git`, Python 3.8+
- Optional: Pillow (`pip install Pillow`) for image downscale/transcode
- Vercel CLI (`npm i -g vercel`) for deployment
- The [`sgc-deploy-to-vercel`](https://github.com/lovstudio/deploy-to-vercel-skill)
  skill (handles Vercel + Cloudflare DNS for the subdomain)

## Usage

Trigger it in any Claude Code session:

> 用 fumadocs 给 github.com/acme/widget 生成文档站，部署到 widget.lovstudio.ai/docs

> 把 ~/notes/handbook 这个装满文章和图片的文件夹整理成文档站

The skill asks for the source, product id, title, and whether to deploy, then
inventories → scaffolds → copies images → authors incrementally → (optionally) ships.

## Scripts

| Script | Purpose |
|--------|---------|
| `inventory.py` | Enumerate + classify a folder into an ordered manifest (overview first) |
| `copy_assets.py` | Copy images into `public/assets/` (+ optional downscale/transcode), emit a path map |
| `scaffold_docs.py` | Run `create-fumadocs-app`, set `basePath: '/docs'`, reset content |

```bash
SKILL_DIR="${LOVSTUDIO_SKILLS_INSTALL_DIR:?}/sgc-repo2docs"
python3 "$SKILL_DIR/scripts/inventory.py"    --src ./my-folder --out manifest.json
python3 "$SKILL_DIR/scripts/scaffold_docs.py" --product-id widget --out ./widget-docs --title "Widget"
python3 "$SKILL_DIR/scripts/copy_assets.py"  --src ./my-folder --site ./widget-docs --out assets-map.json
```

See [`SKILL.md`](SKILL.md) for the full incremental workflow and the CLI reference.

## How the `/docs` path works

The site is served under `/docs` via Next.js `basePath: '/docs'`, set
automatically by the scaffold script. Reference images with root-relative
`/assets/...` paths — Next resolves them to `/docs/assets/...`. See
[`references/fumadocs.md`](references/fumadocs.md) for routing details and the
common double-prefix gotcha.

## License

MIT
