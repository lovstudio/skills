---
name: lov-find-logo
description: >
  Fetch a company/product logo from public sources (Clearbit, og:image,
  favicon) given a brand name or URL, score candidates (wide-aspect +
  transparent preferred), and archive the best + runner-ups to
  the configured logo collection directory.
  Trigger when the user says "find logo", "找 logo", "抓 logo",
  "收集 logo", "brand asset", "需要 <brand> 的 logo",
  or wants logos laid out for a website/PPT/poster.
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only — no pip deps).
  Cross-platform: macOS, Windows, Linux.
metadata:
  author: contributors
  version: "0.3.0"
  tags: [branding, assets, logo, scraping]
---

# find-logo — collect brand logos, prefer wide + transparent

Takes a brand name or URL, probes Clearbit + the site's own og:image /
`<link rel=icon>` / favicon, scores each candidate, and archives the best
one plus a couple of alternates into the configured collection directory.

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
python3 scripts/find_logo.py --name "Anthropic" --url https://anthropic.com --json
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
  **not supported** — if you have a direct image URL, save it into the configured
  collection directory under `<slug>/logo.<ext>` and hand-write `meta.json`
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
| `--out` | `SKILL_FIND_LOGO_OUTPUT_DIR` or `~/.skill-publisher/logo-collection` | Archive root. |
| `--keep-alts` | `2` | How many runner-up candidates to keep as `alt-N.<ext>`. |
| `--json` | off | Emit a JSON result to stdout (use this when chaining). |

At least one of `--name` or `--url` is required.

## Archive Layout

```
~/.skill-publisher/logo-collection/
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

## User Configuration

Default archive files live under `~/.skill-publisher/logo-collection/`. Override this
per run with `--out`, or set `SKILL_FIND_LOGO_OUTPUT_DIR` for the skill.

## Known Limits

- The name → domain guess is a crude lowercase-strip + `.com` suffix. For
  anything not on `.com`, pass `--url` explicitly.
- No Clearbit API key is used — we hit the unauthenticated endpoint, which
  covers most major brands but not all.
- `WebSearch` fallback is Claude's responsibility, not the script's.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
