---
name: lovstudio:find-logo
description: >
  Fetch a company/product logo from public sources (Clearbit, og:image,
  favicon) given a brand name or URL, score candidates (wide-aspect +
  transparent preferred), and archive the best + runner-ups to
  ~/.lovstudio/logo-collection/<slug>/.
  Trigger when the user says "find logo", "找 logo", "抓 logo",
  "收集 logo", "brand asset", "需要 <brand> 的 logo",
  or wants logos laid out for a website/PPT/poster.
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only — no pip deps).
  Cross-platform: macOS, Windows, Linux.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: [branding, assets, logo, scraping]
---

# find-logo — collect brand logos, prefer wide + transparent

Takes a brand name or URL, probes Clearbit + the site's own og:image /
`<link rel=icon>` / favicon, scores each candidate, and archives the best
one plus a couple of alternates into `~/.lovstudio/logo-collection/<slug>/`.

## When to Use

- User asks to collect one or more brand logos for a slide/poster/site lineup
- User names companies to drop into a partners/press strip
- User gives a URL and wants its logo pulled down cleanly

## Workflow (MANDATORY)

### Step 1: Identify each brand

Accept any mix of names and URLs. If the user gave only a name with no obvious
domain, ask — don't silently guess `.com` (script will guess, but for non-US or
ambiguous brands that fails).

Use `AskUserQuestion` when:
- Brand name is ambiguous (e.g. "Apple" = fruit vs. Inc.)
- No URL and the domain isn't guessable (`xAI` → `x.ai`, not `xai.com`)
- User gave a list without URLs

### Step 2: Fetch — one brand per invocation

```bash
python3 ~/.claude/skills/lovstudio-find-logo/scripts/find_logo.py \
  --name "Anthropic" --url https://anthropic.com --json
```

For a batch, loop; the script is idempotent per `<slug>/` (re-runs overwrite).

### Step 3: Inspect score; fall back to WebSearch if needed

- Exit code `0` → logo archived. The printed `score` is your quality signal:
  - `≥ 60` — solid: SVG or transparent PNG with wide/square aspect
  - `20–60` — usable: probably a favicon or small PNG
  - `< 20` — weak: only ICO or tiny stub found
- Exit code `2` / `status: "no-candidates"` → script found nothing.
  Do NOT give up. Use `WebSearch` for `"<brand> logo svg site:*.com"` or the
  brand's press-kit page, then re-invoke with `--url <direct-image-url>` is
  **not supported** — if you have a direct image URL, `curl -o` it into
  `~/.lovstudio/logo-collection/<slug>/logo.<ext>` and hand-write `meta.json`
  using the existing layout as a template.

### Step 4: Report

Report back with the archive path and the primary's aspect + format. If the
score is weak, tell the user and offer to retry with a specific press-kit URL
or Wikipedia SVG.

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--name` | — | Brand/product name. Used for slug + meta. |
| `--url` | — | Official URL or bare domain. Overrides the name-based domain guess. |
| `--slug` | slugified name | Override the directory slug under the archive root. |
| `--out` | `~/.lovstudio/logo-collection` | Archive root. |
| `--keep-alts` | `2` | How many runner-up candidates to keep as `alt-N.<ext>`. |
| `--json` | off | Emit a JSON result to stdout (use this when chaining). |

At least one of `--name` or `--url` is required.

## Archive Layout

```
~/.lovstudio/logo-collection/
├── anthropic/
│   ├── logo.png            # primary (highest score)
│   ├── alt-1.png           # runner-ups
│   ├── alt-2.png
│   └── meta.json           # sources, scores, dimensions, fetched_at
├── vercel/
│   ├── logo.png            # 1200x628 transparent banner
│   └── ...
└── stripe/
    ├── logo.svg
    └── ...
```

## Scoring Heuristic (why a candidate wins)

- Format: SVG (+40) > PNG (+20) > WebP (+10) > JPG (-10) > ICO (-20)
- Transparency: `+30` if alpha channel present (SVG always counts)
- Aspect ratio: `+25` for wide (≥2:1), `+10` for landscape (≥1.3:1),
  `-5` for square, `-15` for tall/portrait
- Short edge: `+15` if ≥128px, `+5` if ≥64px, `-20` if <32px
- Size sanity: `-30` if payload <400 bytes (almost certainly a stub)

This matches the "prefer 长条形 + rgba" preference — wide transparent logos
come out on top, square favicons land as alternates.

## Dependencies

Stdlib only (urllib, html.parser, argparse). No `pip install` required.

## Known Limits

- The name → domain guess is a crude lowercase-strip + `.com` suffix. For
  anything not on `.com`, pass `--url` explicitly.
- No Clearbit API key is used — we hit the unauthenticated endpoint, which
  covers most major brands but not all.
- `WebSearch` fallback is Claude's responsibility, not the script's.
