---
name: lovstudio:deploy-to-vercel
category: Dev Tools
tagline: "Deploy frontend to Vercel with auto Cloudflare DNS + custom domain setup."
description: >
  Deploy frontend projects to Vercel with automatic custom domain setup.
  Handles Vite, Next.js, CRA, and static sites. Auto-configures Cloudflare DNS
  CNAME records and Vercel domain aliases. Supports SPA routing via vercel.json.
  Trigger when user says "deploy to vercel", "部署到 vercel", "vercel deploy",
  or mentions a *.lovstudio.ai / custom domain with vercel deployment.
license: MIT
compatibility: >
  Requires vercel CLI (`npm i -g vercel`), gh CLI, and curl.
  Cloudflare DNS auto-config requires CLOUDFLARE_API_KEY env var.
metadata:
  author: lovstudio
  version: "2.0.0"
  tags: deploy vercel cloudflare dns frontend
---

# deploy-vercel — One-Command Frontend Deployment

Deploy frontend projects to Vercel with automatic custom domain and DNS setup.

## When to Use

- User says "deploy to vercel" or "部署到 xxx.lovstudio.ai"
- After building a frontend project that needs hosting
- When setting up a custom domain on an existing Vercel deployment

## Arguments

Pass via `$ARGUMENTS`:

| Argument | Example | Description |
|----------|---------|-------------|
| `<domain>` | `sbti.lovstudio.ai` | Custom domain to configure |
| `--preview` | | Deploy preview only (skip `--prod`) |
| `--no-dns` | | Skip Cloudflare DNS auto-config |
| `--link-only` | | Only link project, don't deploy |

## Workflow

### Step 1: Detect Project Type

```bash
if [ -f "vite.config.ts" ] || [ -f "vite.config.js" ]; then
  FRAMEWORK="vite"
elif [ -f "next.config.js" ] || [ -f "next.config.mjs" ]; then
  FRAMEWORK="next"
elif grep -q "react-scripts" package.json 2>/dev/null; then
  FRAMEWORK="cra"
else
  FRAMEWORK="static"
fi
```

### Step 2: Ensure vercel.json for SPA

For Vite/CRA (SPA) projects, create `vercel.json` if missing:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/" }
  ]
}
```

**Skip for Next.js** — it handles routing natively.

### Step 3: Deploy to Vercel

```bash
# Check CLI
vercel --version || npm i -g vercel

# Deploy (use project name from package.json "name" field)
# IMPORTANT: package.json "name" must be lowercase, no special chars
PROJECT_NAME=$(node -p "require('./package.json').name" 2>/dev/null || basename "$PWD")
vercel --yes --prod
```

**Known issue**: If `package.json` name contains uppercase or invalid chars,
vercel will error with "Project names must be lowercase". Fix the name first.

### Step 4: Configure Custom Domain (if provided)

```bash
DOMAIN="<user-provided-domain>"  # e.g. sbti.lovstudio.ai

# 1. Add domain to Vercel project
vercel domains add "$DOMAIN"

# 2. Set alias to point domain to latest deployment
PROD_URL=$(vercel ls --prod 2>&1 | grep -oE 'https://[^ ]+\.vercel\.app' | head -1)
vercel alias set "$PROD_URL" "$DOMAIN"
```

**CRITICAL**: `vercel domains add` alone is NOT enough. You MUST also run
`vercel alias set` to actually route traffic. Without it, the domain returns
ERR_CONNECTION_CLOSED.

### Step 5: Auto-Configure Cloudflare DNS

**Requires**: `CLOUDFLARE_API_KEY` env var (API Token with DNS edit permission).

```bash
# Extract base domain and subdomain
# e.g. "sbti.lovstudio.ai" → base="lovstudio.ai", sub="sbti"
BASE_DOMAIN=$(echo "$DOMAIN" | awk -F. '{print $(NF-1)"."$NF}')
SUBDOMAIN=$(echo "$DOMAIN" | sed "s/\.$BASE_DOMAIN$//")

# 1. Get zone ID
ZONE_ID=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=$BASE_DOMAIN" \
  -H "Authorization: Bearer $CLOUDFLARE_API_KEY" \
  -H "Content-Type: application/json" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")

# 2. Check if record already exists
EXISTING=$(curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$DOMAIN&type=CNAME" \
  -H "Authorization: Bearer $CLOUDFLARE_API_KEY" | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")

# 3. Create or update CNAME → cname.vercel-dns.com
if [ -z "$EXISTING" ]; then
  curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CLOUDFLARE_API_KEY" \
    -H "Content-Type: application/json" \
    --data "{\"type\":\"CNAME\",\"name\":\"$SUBDOMAIN\",\"content\":\"cname.vercel-dns.com\",\"ttl\":1,\"proxied\":false}"
else
  curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$EXISTING" \
    -H "Authorization: Bearer $CLOUDFLARE_API_KEY" \
    -H "Content-Type: application/json" \
    --data "{\"type\":\"CNAME\",\"name\":\"$SUBDOMAIN\",\"content\":\"cname.vercel-dns.com\",\"ttl\":1,\"proxied\":false}"
fi
```

**IMPORTANT**: `proxied` must be `false` (DNS only). Cloudflare proxy conflicts
with Vercel's SSL certificate provisioning.

If `CLOUDFLARE_API_KEY` is not set, print manual DNS instructions instead:
```
Add DNS record:
  Type: CNAME
  Name: <subdomain>
  Target: cname.vercel-dns.com
  Proxy: OFF (DNS only)
```

### Step 6: Verify

```bash
# Wait for DNS + SSL propagation
sleep 5
HTTP_CODE=$(curl -sI "https://$DOMAIN" -o /dev/null -w '%{http_code}')
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ $DOMAIN is live"
else
  echo "⚠ HTTP $HTTP_CODE — SSL may still be provisioning, try again in 1-2 min"
fi
```

### Step 7: Output Summary

```
✓ Framework: vite
✓ Deployed: https://xxx.vercel.app
✓ Domain: https://sbti.lovstudio.ai
✓ DNS: CNAME sbti → cname.vercel-dns.com (Cloudflare)
✓ Settings: https://vercel.com/<scope>/<project>/settings
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| ERR_CONNECTION_CLOSED | Domain added but no alias set | Run `vercel alias set <url> <domain>` |
| "Project names must be lowercase" | package.json name invalid | Fix name field |
| SSL not provisioning | Cloudflare proxy ON | Set DNS to "DNS only" (no orange cloud) |
| 404 on sub-routes | SPA missing rewrites | Add vercel.json with rewrites |
| DNS resolves to 198.18.x.x | Local proxy (Clash etc.) | Normal — check with `dig @8.8.8.8` |
| `CLOUDFLARE_API_KEY` not found | Token not in env | Add to `~/.zshrc`: `export CLOUDFLARE_API_KEY=...` |
