# lovstudio:find-logo

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

Fetch a brand/product logo from public sources (Clearbit, og:image, favicon),
score candidates (prefer wide-aspect + transparent), and archive the winner
plus alternates under `~/.lovstudio/logo-collection/<slug>/`.

Useful for building website partner strips, PPT footer rows, poster
credits — anywhere you need a lineup of logos that look consistent.

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/find-logo-skill ~/.claude/skills/lovstudio-find-logo
```

Stdlib only — no `pip install` needed.

## Usage

```bash
# by name
python3 ~/.claude/skills/lovstudio-find-logo/scripts/find_logo.py --name "Anthropic"

# by URL (more reliable for non-.com or ambiguous brands)
python3 ~/.claude/skills/lovstudio-find-logo/scripts/find_logo.py \
  --name "xAI" --url https://x.ai

# machine-readable output for chaining
python3 ~/.claude/skills/lovstudio-find-logo/scripts/find_logo.py \
  --url https://stripe.com --json
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--name` | — | Brand/product name. Used for slug + meta. |
| `--url` | — | Official URL or bare domain. Overrides the name-based guess. |
| `--slug` | slugified name | Override the archive directory slug. |
| `--out` | `~/.lovstudio/logo-collection` | Archive root. |
| `--keep-alts` | `2` | How many runner-up candidates to keep. |
| `--json` | off | Emit JSON to stdout. |

At least one of `--name` or `--url` is required.

## What gets archived

```
~/.lovstudio/logo-collection/<slug>/
├── logo.<ext>      # highest-scoring candidate
├── alt-1.<ext>     # runner-ups (count = --keep-alts)
├── alt-2.<ext>
└── meta.json       # brand, source URL per candidate, dims, format, alpha, score
```

## How candidates are scored

Higher is better. Intended to bubble up **wide-aspect + transparent** logos
so they line up cleanly next to each other.

| Factor | Points |
|--------|--------|
| Format SVG / PNG / WebP / JPG / ICO | +40 / +20 / +10 / -10 / -20 |
| Has alpha (transparent) | +30 |
| Aspect ≥ 2:1 (banner) | +25 |
| Aspect ≥ 1.3:1 (landscape) | +10 |
| Aspect ≈ 1:1 (square) | -5 |
| Aspect tall / portrait | -15 |
| Short edge ≥ 128 / ≥ 64 / < 32 px | +15 / +5 / -20 |
| Payload < 400 bytes (stub) | -30 |

## Sources probed, in order

1. **Clearbit Logo API** — `https://logo.clearbit.com/<domain>` (unauthenticated tier).
2. **og:image / twitter:image + `<link rel="icon">`** — scraped from the brand's homepage. Usually wins because sites ship a proper share card.
3. **Google s2 favicon** — `https://www.google.com/s2/favicons?domain=<domain>&sz=256` as a safety net.

If all three fail, the script exits `2` with `status: "no-candidates"`. The
calling agent is expected to fall back to a web search for a press-kit page.

## License

MIT
