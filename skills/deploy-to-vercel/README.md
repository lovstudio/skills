# lov-deploy-to-vercel

![Version](https://img.shields.io/badge/version-2.1.0-CC785C)

One-command frontend deployment to Vercel with automatic custom domain + Cloudflare DNS setup.

Part of [skill-publisher/skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add skill-publisher/skills --skill lov-deploy-to-vercel -y -g
```

Requires: `vercel` CLI, `curl`, `python3`

## Usage

```
/deploy-vercel                          # deploy to Vercel (auto-detect framework)
/deploy-vercel sbti.example.com        # deploy + configure custom domain + DNS
/deploy-vercel --preview                # preview deployment only
```

## What It Does

1. Detects framework (Vite / Next.js / CRA / static)
2. Creates `vercel.json` SPA rewrites if needed
3. Deploys to Vercel production
4. Adds custom domain + sets alias
5. Auto-configures Cloudflare DNS CNAME record
6. Verifies site is live

## Options

| Option | Description |
|--------|-------------|
| `<domain>` | Custom domain (e.g. `app.example.com`) |
| `--preview` | Preview deploy only |
| `--no-dns` | Skip Cloudflare DNS setup |
| `--link-only` | Link project without deploying |

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `CLOUDFLARE_API_KEY` | For DNS auto-config | Cloudflare API Token with DNS:Edit |

## License

MIT