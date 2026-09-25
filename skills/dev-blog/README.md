# 研发手记 · Dev Journal

![Version](https://img.shields.io/badge/version-0.5.1-CC785C)

Canonical publishing contract for Skill Publisher's Supabase-backed website blog
feed. It can write and publish a development blog post directly, and it defines
the automation semantics used by dependent skills such as `deep-research` and
`lov-distill`.

Part of [skills](https://example.com/skills/skills) — by [example.com](https://example.com)

## Install

```bash
npx skills add dev-blog -g -y
```

Requires Python 3.8+. No third-party Python packages are needed.

## Usage

Ask Claude Code:

```text
/lov-dev-blog 总结这次开发过程，生成一篇博客并同步到网站
```

The skill will gather context, draft a Chinese article, save a local Markdown
draft, inventory relevant screenshots and diagrams, generate and upload a
cover, prepare selected inline images, run a dry-run payload check, then
publish to Supabase `blog_posts` by default.

When you provide a writing style profile, the skill reads it before drafting,
extracts a portable style brief, and validates the finished article against
that brief. The profile controls voice and rhythm without overriding factual
evidence or inventing first-person experience.

When the source material contains meaningful visual evidence, the skill treats
it as part of the article rather than debugging-only context. Each selected
image receives a durable public URL, descriptive alt text, a narrative caption,
and live-page verification.

Dependent skills publish generated Markdown through the same contract:

```bash
WEB_ROOT="${SKILL_DEV_BLOG_WEB_ROOT:?set SKILL_DEV_BLOG_WEB_ROOT}"
cd "$WEB_ROOT" && pnpm run sync:research -- [markdown_path]
cd "$WEB_ROOT" && pnpm run sync:distill -- [markdown_path]
```

Those sync scripts own source-specific parsing, while `lov-dev-blog` owns
the shared `blog_posts` semantics: `source_kind`, `source_path`,
`is_visible`, `show_in_index`, and final publish status reporting.

You can also run the publisher directly:

```bash
WEB_ROOT="${SKILL_DEV_BLOG_WEB_ROOT:?set SKILL_DEV_BLOG_WEB_ROOT}"
python3 scripts/publish_blog_post.py \
  --input .output/dev-blog/example.md \
  --title "一次开发上下文如何变成可复用博客" \
  --slug "dev-context-to-blog" \
  --excerpt "把开发过程沉淀成网站博客，关键在于先结构化上下文，再用 Supabase 作为发布源。" \
  --tags "dev,skill-publisher,blog" \
  --cover "https://example.com/blog-cover.webp" \
  --env-file "$WEB_ROOT/.env.local"
```

Upload inline article images with the bundled dependency-free uploader:

```bash
WEB_ROOT="${SKILL_DEV_BLOG_WEB_ROOT:?set SKILL_DEV_BLOG_WEB_ROOT}"
python3 scripts/upload_blog_assets.py \
  --slug "dev-context-to-blog" \
  --input "cover-image/dev-context-to-blog/inline/01-problem.webp" \
  --input "cover-image/dev-context-to-blog/inline/02-result.webp" \
  --env-file "$WEB_ROOT/.env.local" \
  --dry-run
```

Repeat without `--dry-run`, embed the returned public URLs in the Markdown, and
pass `--require-inline-image` to the publisher.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | (required) | Markdown/MDX post body. |
| `--title` | (required) | Blog post title. |
| `--slug` | generated from title | URL slug. |
| `--excerpt` | first paragraph | Blog card summary. |
| `--tags` | `dev,skill-publisher` | Comma-separated tags. |
| `--author` | `Mark` | Author name. |
| `--cover` | empty | Required for published posts. Use `--draft` to skip cover while saving a hidden draft. |
| `--require-inline-image` | false | Fail when the post is expected to contain inline visual evidence but has no embedded image. |
| `--published-at` | now | ISO timestamp. |
| `--source-kind` | `dev-skill` | Stored in `blog_posts.source_kind`. |
| `--source-path` | `dev-blog:<slug>` | Stable source key. |
| `--draft` | false | Publish as hidden draft. |
| `--hide-from-index` | false | Keep visible detail page but omit from `/blog`. |
| `--env-file` | empty | Optional env file containing Supabase credentials. |
| `--dry-run` | false | Print payload without writing. |

## Supabase Target

The script upserts into `blog_posts` by `slug` and sets:

- `is_visible=true`
- `show_in_index=true`
- `source_kind=dev-skill`

It requires `NEXT_PUBLIC_SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the
environment or in the file passed through `--env-file`.

## User Configuration

Set `SKILL_DEV_BLOG_WEB_ROOT` to the website repo root used for sync scripts
and default `.env.local` lookup.

To keep a personal writing voice across articles, configure the runtime
preference `user.style_profile_path` with a readable Markdown or text profile,
or provide a profile path in the current request. Request-level instructions
take precedence, and personal absolute paths are never embedded in the public
post or the reusable Skill package.

## License

MIT
