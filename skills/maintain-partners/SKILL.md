---
name: lovstudio-maintain-partners
description: >
  Maintain the LovStudio website's partners section AND align partner logo
  rows on event posters / hero strips: reuse lovstudio-find-logo for brand
  logo discovery, normalize collected logos to a 240px-tall content canvas
  (retina-ready), rasterize SVGs via rsvg-convert before normalizing (so SVG
  viewBox padding gets cropped),
  strip embedded background rects from icon-style SVGs, composite icon +
  wordmark when only an icon is available (using brand fonts), wrap logos
  in a fixed-size grid box (96×30 with subtle border) for stable matrix
  layouts, replace existing logos with user-provided files, append new
  partners to the PARTNERS array with i18n taglines across zh-CN/en/ja/th,
  and audit the section for dead URLs / missing files / missing translations.
  Also handles cross-asset visual height parity (multi-logo strips on dark
  backgrounds, "logo 不等高", unified-color filter recipe). Trigger when the
  user mentions "合作伙伴", "partners", "trusted by", "新增 logo", "标准化 logo",
  "替换 logo", "审计合作伙伴", "维护合作伙伴", "logo 不一样高", "logo 对齐",
  "logo 大小不一致", "logo 颜色不统一", "logo 不清晰", "logo 糊了", "矩阵格子",
  "等宽 box", "图标加文字", "compose wordmark".
license: MIT
compatibility: >
  Requires the lovstudio-find-logo skill plus Python 3.8+ with Pillow
  (`pip install Pillow --break-system-packages`). Requires rsvg-convert
  (`brew install librsvg`) when the selected logo source is SVG.
  Tested on macOS; Linux should work.
depends_on:
  - lovstudio-find-logo
metadata:
  author: lovstudio
  version: "0.4.0"
  tags: [lovstudio, web, branding, i18n]
---

# maintain-partners — LovStudio 合作伙伴板块维护

Operates on `/Users/mark/lovstudio/coding/web` (the LovStudio website repo).
The partners strip lives in `app/(main)/(home)/WorkshopDispatch.tsx` as a
`PARTNERS: Partner[]` array; logos in `public/partners/<slug>/logo.png`;
taglines in `src/i18n/messages/{zh-CN,en,ja,th}.json` under `dispatch.partner*Tagline`.

## Skill Dependencies

- `lovstudio-find-logo` is required for all logo discovery. This skill must
  not scrape homepages itself or keep a separate fallback crawler.
- Use the `depends_on` frontmatter field to declare skill-level dependencies.
  This mirrors the `depends_on` field in `lovstudio-general-skills/skills.yaml`;
  unknown frontmatter keys are expected to be ignored by agents that do not
  consume dependency metadata.

## When to Use

- User asks to **add** one or more new partners (with or without a logo URL).
- User asks to **standardize / normalize** a logo (sizing wrong, white-on-white, etc.).
- User provides a local file and asks to **replace** an existing partner's logo.
- User asks to **audit** the partners section before a release.

## Standards

- Logo canvas: **80px** content height for the website partners strip
  (light grayscale, CSS `height: 32px` ≈ 2.5× density, sharp enough),
  **240px** for event posters or any retina export at `scale: 2` or higher.
- For white-on-transparent logos: invert (full or selective) so they show on
  the light grayscale strip.
- For icon-only logos < ~40px wide after normalization: pass `--show-name`
  when adding so the brand name renders next to the icon.
- Tagline format: `<品牌名> · <一句话定位>` in Chinese; mirror style in en/ja/th.

## Workflow

### Op 1: Add a new partner

1. Ask the user for the brand name + homepage URL via `AskUserQuestion`.
2. Collect the logo with `lovstudio-find-logo`:
   ```bash
   python3 ~/.claude/skills/lovstudio-find-logo/scripts/find_logo.py \
     --name "<显示名>" --url <URL> --slug <slug> --json
   ```
   Use the archived primary asset under
   `~/.lovstudio/logo-collection/<slug>/logo.<ext>`. If `find_logo.py` returns
   no candidates, stop and ask the user for a better official URL / press-kit
   URL, then rerun `find_logo.py`. Do not call a local scraper from this skill.
3. Visually verify the archived primary asset before normalizing.
4. If the primary asset is SVG, rasterize it before normalization:
   ```bash
   rsvg-convert -h 240 ~/.lovstudio/logo-collection/<slug>/logo.svg \
     -o /tmp/<slug>-raw.png
   ```
   Use the rasterized `/tmp/<slug>-raw.png` as `--src`. For non-SVG sources,
   use the archived primary asset directly.
5. Normalize:
   ```bash
   python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
     --src <archived-or-rasterized-logo> \
     --dst /Users/mark/lovstudio/coding/web/public/partners/<slug>/logo.png \
     --invert auto
   ```
6. Read the normalized PNG to confirm it's visible (not white-on-white).
7. Append to PARTNERS + all 4 locale JSONs:
   ```bash
   python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/add_partner.py \
     --name "<显示名>" --href "<URL>" \
     --logo "/partners/<slug>/logo.png" \
     --key partner<Slug>Tagline \
     --zh "..." --en "..." --ja "..." --th "..." \
     [--show-name]
   ```

### Op 2: Normalize an existing logo

```bash
python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
  --src public/partners/<slug>/logo.png \
  --dst public/partners/<slug>/logo.png \
  --invert auto
```

Re-read after to verify.

### Op 3: Replace logo from a user-provided file

User typically provides a path under `~/lovstudio/partners/<品牌>/<file>`.

```bash
python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
  --src "<user-provided path>" \
  --dst /Users/mark/lovstudio/coding/web/public/partners/<slug>/logo.png \
  --invert auto
```

JPEG inputs auto-strip near-white background to transparent before crop.

### Op 4: Audit

```bash
python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/audit_partners.py
# add --probe to also HTTP-check every href (slow, requires proxy)
```

Reports: missing logo files, missing i18n keys per locale, dead URLs.

### Op 5: Align a row of partner logos (cross-asset visual height parity)

**When**: putting 3+ partner logos in a single horizontal strip and they look
different sizes despite having the same CSS `height`. Common in event posters,
hero sections, "联办 / co-host" rows.

**Root cause**: each source file has different internal padding (designer
canvas margin), so two PNGs both set to `height: 24px` render at different
*visible* heights because their content occupies different fractions of the
canvas. Per-logo CSS height tweaks based on eyeballed content ratios are
unstable—different displays / scaling will diverge again.

**Reliable fix — trim at file level, uniform CSS box**:

1. **Normalize every logo** to identical content height. Default raster file
   target is **240px** (3× density for retina poster export at `scale: 2`;
   80px gives only 1.7× and looks soft after PNG export). Use `--invert off`
   if the source is already light-on-transparent (don't double-invert):
   ```bash
   for f in lujiazui juanyi citic-bookstore citic-thinker-lab; do
     python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
       --src ~/lovstudio/partners/<brand>/<file>.png \
       --dst <event-assets>/partners/$f.png \
       --height 240 --invert auto
   done
   ```
   **Always normalize from the original source**, never from a previously
   normalized 80px file (upscaling = blurry — burned by this on juanyi).

2. **For SVG sources, rasterize first**. `normalize_logo.py` operates on
   raster pixels and **cannot crop SVG viewBox padding**. Without this step
   an SVG always renders smaller than rasterized PNG siblings:
   ```bash
   rsvg-convert -h 720 brand.svg -o /tmp/brand-raw.png   # 3× of 240
   python3 ~/.claude/skills/lovstudio-maintain-partners/scripts/normalize_logo.py \
     --src /tmp/brand-raw.png --dst <event-assets>/partners/brand.png \
     --height 240 --invert off
   ```
   `rsvg-convert` ships with `librsvg` (`brew install librsvg`).

3. **For SVG with embedded background rect** (icon wrapped in a black/colored
   rounded square — common in app-icon-style SVGs from `find-logo`), strip
   the background before rasterizing, otherwise filter `brightness(0)
   invert(1)` flattens it into a solid white block that hides the icon:
   ```bash
   # Drop the outer <rect fill="#000"...> wrapper
   sed -E 's|<rect[^/]*fill="#0+"[^/]*/>||' brand.svg > /tmp/brand-clean.svg
   rsvg-convert -h 720 /tmp/brand-clean.svg -o /tmp/brand-raw.png
   ```

4. **Wrap each logo in a fixed-size box** (recommended over auto-width flex):
   ```html
   <span class="ps-logo-box"><img src="..." class="ps-logo"></span>
   ```
   ```css
   .ps-logo-box {
     width: 96px; height: 30px;             /* fixed grid cell */
     display: inline-flex;
     align-items: center; justify-content: center;
     border: 1px solid rgba(255,255,255,0.10);
     border-radius: 4px;
     padding: 3px 6px;
     box-sizing: border-box;
   }
   .ps-logo { max-width: 100%; max-height: 100%; width: auto; height: auto; display: block; }
   ```
   Fixed boxes give a stable matrix look — narrow logos (icon-only) and wide
   logos (icon + wordmark) all occupy the same footprint, with the asset
   scaled to fit. Auto-width flex (the older recipe) makes per-row total
   widths unpredictable as logos get added/removed.

5. **Dark-background unification** — when the row sits on a dark canvas
   (e.g. event poster), most brand logos are designed for white BG and look
   inconsistent (some have black text, some have brand-colored marks). The
   stable recipe:
   ```css
   .ps-logo { filter: brightness(0) invert(1) opacity(0.88); }
   /* logos already white-on-transparent — opt out of inversion */
   .ps-logo.ps-logo-original { filter: opacity(0.88); }
   ```
   `brightness(0)` flattens all colors to black, then `invert(1)` produces
   uniform white at the configured opacity. The `.ps-logo-original` escape
   hatch is for source files that are already white-on-transparent (white
   SVG variants from a brand kit) so you don't double-process them into
   invisible black-on-dark.

6. **Icon-only SVG → composite icon + wordmark** — if the brand SVG only
   has an icon (no "BrandName" wordmark beside it), don't ship just the icon
   in a 96×30 box (it'll look like an unidentified mark). Compose the
   wordmark with PIL using the brand's own font when possible:

   ```python
   from PIL import Image, ImageDraw, ImageFont, ImageOps
   # 1. rasterize cleaned SVG, invert white→black so default filter works
   icon = Image.open('/tmp/brand-icon.png').convert('RGBA')
   r, g, b, a = icon.split()
   inv = Image.merge('RGB', (ImageOps.invert(r), ImageOps.invert(g), ImageOps.invert(b)))
   icon = Image.merge('RGBA', (*inv.split(), a))
   icon = icon.crop(icon.getbbox())
   target_h = 240
   icon = icon.resize((int(icon.width * target_h / icon.height), target_h), Image.LANCZOS)
   # 2. render wordmark in brand font (find-logo bundles fonts/ when found)
   font = ImageFont.truetype('partners/<brand>/fonts/<Family>.ttf', 150)
   # 3. compose icon + gap + text on transparent canvas
   ```
   The PNG goes through the same `brightness(0) invert(1)` filter as raster
   logos — match colors with all other entries automatically. Use the brand's
   own font (often shipped under `<brand>/fonts/` by the find-logo skill);
   fall back to system SF / Helvetica only if no brand font is available.

7. **Anti-pattern — do not** try to fix alignment by setting per-logo
   heights like `.ps-logo-juanyi { height: 26px }`. It's brittle (every new
   logo needs another magic number), unstable across browsers, and breaks
   the moment a designer reships the source asset with different padding.

## CLI Reference

### normalize_logo.py
| Flag | Default | Notes |
|---|---|---|
| `--src` | required | input image (PNG/JPG/rasterized SVG) |
| `--dst` | required | output PNG path; parent dirs auto-created |
| `--height` | `80` | target content height. **Use 240 for retina poster export** (`scale: 2`) — 80 looks soft after 2× downscale. |
| `--invert` | `auto` | `auto` / `off` / `full` / `selective` (selective preserves colored icons) |

### add_partner.py
| Flag | Notes |
|---|---|
| `--name` | display name (CJK ok) |
| `--href` | brand URL |
| `--logo` | path under `/public`, e.g. `/partners/foo/logo.png` |
| `--key` | i18n key, e.g. `partnerFooTagline` |
| `--zh / --en / --ja / --th` | tagline strings (all required) |
| `--show-name` | render name next to icon for narrow logos |

### audit_partners.py
| Flag | Notes |
|---|---|
| `--probe` | HTTP-probe every href (slow, needs proxy env vars) |

## Network proxy

Sandbox child processes don't inherit the system ClashX proxy. Before
fetching logos with `lovstudio-find-logo` or probing partner URLs, export:

```bash
export https_proxy=http://127.0.0.1:7890 \
       http_proxy=http://127.0.0.1:7890 \
       all_proxy=socks5://127.0.0.1:7891
```

`audit_partners.py` already injects these for `curl` invocations.

## Dependencies

```bash
git clone https://github.com/lovstudio/find-logo-skill ~/.claude/skills/lovstudio-find-logo
pip install Pillow --break-system-packages
brew install librsvg  # for SVG logo sources
```
