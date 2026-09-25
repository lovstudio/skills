---
name: lov-dev-blog
category: Dev Tools
tagline: "Write or sync Markdown into Skill Publisher's Supabase-backed website blog feed."
description: >
  Own the Skill Publisher website blog publishing contract. Summarize the current
  development context and its screenshots, diagrams, or other visual evidence
  into a practical Chinese blog post, then publish it to Skill Publisher's Supabase
  `blog_posts` table. Also provide the automation semantics that dependent
  skills use when they sync generated Markdown artifacts to the website blog.
  Trigger when the user says "生成博客", "同步到网站博客", "总结上下文写博文",
  "开发日志", "把这些截图写进文章", "generate blog post",
  "sync to website blog", or "summarize context as blog".
license: MIT
compatibility: >
  Requires Python 3.8+. Publishing requires Supabase service-role credentials
  available in environment variables or a local .env file.
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.5.1"
  tags: dev blog supabase writing publishing
---

# 研发手记 · Dev Journal

Canonical publishing contract for Skill Publisher's website blog feed.

This skill can directly turn the current development session into a useful
Chinese technical blog post and publish it, and it also defines the automation
contract used by skills such as `deep-research` and `lov-distill` when
they publish generated Markdown artifacts to `blog_posts`.

## When to Use

- The user asks to summarize current context and write a blog post.
- The user wants a development log, incident write-up, or lessons learned article.
- The user asks to sync a generated post to the Skill Publisher website blog list.
- Another Skill Publisher skill needs to publish generated Markdown to the website
  blog system. That skill should declare `lov-dev-blog` as a dependency
  and follow this publishing contract.
- Trigger phrases: "生成博客", "同步到网站博客", "总结上下文写博文", "开发日志", "generate blog post", "sync to website blog".

## Publishing Contract

`lov-dev-blog` owns the shared `blog_posts` semantics:

- `blog_posts` is the canonical website blog target.
- `source_kind` identifies the producer, such as `dev-skill`, `deep-research`,
  or `distill`.
- `source_path` is the stable idempotency key for generated artifacts.
- `is_visible=true` means the detail page is public.
- `show_in_index=true` means the post appears in the `/blog` list; dependent
  skills may choose different defaults.
- Meaningful screenshots, diagrams, charts, and before/after images supplied by
  the user are article source material. Inventory them before drafting and
  embed the selected items as durable public assets instead of silently
  dropping them.
- Final responses from dependent skills must include
  `Published to Skill Publisher: yes/no` and the public URL when publish succeeds.

Dependent skills should not invent separate Supabase payload semantics. They may
use website sync scripts from the configured Skill Publisher website repo, but
those scripts are part of this `dev-blog` publishing contract.

Supported publishing modes:

- Direct article mode: this skill drafts a blog post, generates a cover, and
  publishes it with `scripts/publish_blog_post.py`.
- Generated artifact sync mode: a dependent skill generates Markdown, then uses
  the source-specific sync command below under this contract.

Default publishing behavior:

- Direct article mode publishes by default after a dry run, including cover
  generation/upload and the non-dry-run Supabase upsert.
- Do not ask for confirmation before publishing unless the user explicitly
  requests a confirmation gate.
- Skip publishing only when the user explicitly asks for draft/local-only/no
  publish behavior, or when a required blocker exists such as missing
  credentials, missing website repo, cover generation failure, or schema/API
  failure.

Current dependent publishing commands:

```bash
WEB_ROOT="${SKILL_DEV_BLOG_WEB_ROOT:?set SKILL_DEV_BLOG_WEB_ROOT}"
cd "$WEB_ROOT" && pnpm run sync:research -- [markdown_path]
cd "$WEB_ROOT" && pnpm run sync:distill -- [markdown_path]
```

Use dry-run or publish modes according to the dependent skill's workflow. If a
publish fails because credentials, website path, or database schema is
unavailable, keep the generated artifact and report the exact rerun command.

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: Gather Context

Collect the source material before writing:

- Recent user intent and constraints from the conversation.
- Any writing style profile explicitly supplied by the user or resolved from
  the runtime preference `user.style_profile_path`.
- Relevant files, diffs, commands, errors, and verification output.
- Every attached image, user-supplied image path, reproduction screenshot,
  generated diagram, and before/after artifact relevant to the story.
- The final decision or implementation, including tradeoffs.
- What a future reader should learn from this case.

Create a visual asset inventory before drafting whenever visual material exists.
Classify each item as problem evidence, key detail, before/after proof,
architecture explanation, or decorative. Default to including user-provided
visual evidence that materially improves understanding. Record a concrete
reason when excluding it, such as redundancy, illegibility, irrelevance, or
private information.

When the inventory contains visual material, read
`references/inline-media.md` completely before drafting or uploading assets.

Resolve writing style in this order: the current request, project context,
`user.style_profile_path`, `brand.tone`, then this Skill's default style rules.
When a style profile path is available, read the file completely and read
`references/writing-style.md` before drafting. Turn the profile into a compact
style brief covering voice, perspective, paragraph rhythm, structure,
vocabulary, evidence, emotional arc, rhetorical habits, and prohibitions.
Never hardcode a personal profile path into the reusable Skill or expose a
private local path in the public article.

Style changes presentation, not truth. Use first-person claims only when the
source context supports that the named author actually performed or witnessed
the action. If a configured profile cannot be read, report the path as a local
draft blocker instead of silently claiming the article matches it.

If the topic or audience is unclear, use `AskUserQuestion` for one concise
question. The publish target defaults to the Skill Publisher website blog; ask about
the target only if the user mentions multiple possible destinations. Do not ask
for fields that can be inferred from the current context.

### Step 2: Draft the Article

Write in Chinese for two audiences:

- Primary: Mark, as a durable record of the work.
- Secondary: developers or AI builders who may hit a similar issue.

Use this structure unless the context clearly calls for a different one:

1. `# <title>`
2. Opening: what problem triggered the work and why it mattered.
3. Context: project/background, only enough for the reader to orient.
4. Process: the key investigation path, failed assumptions, and turning points.
5. Solution: what changed, why this shape fits the system.
6. Takeaways: reusable engineering lessons.

Style rules:

- Apply the resolved style brief before the generic rules below. A user's
  explicit per-article instruction overrides their stored profile.
- Prefer concrete nouns, file/table names, commands, and exact constraints.
- Avoid generic AI productivity claims.
- Do not include secrets, tokens, private customer details, or raw `.env` values.
- Keep code excerpts short and only when they explain the decision.
- Place each selected visual immediately after the paragraph that frames what
  the reader should notice.
- Give every inline image descriptive alt text and a caption that explains why
  it matters. For a wide screenshot, add a focused crop when the critical detail
  would become too small on mobile.
- Use screenshots as evidence, diagrams for invisible relationships, and the
  cover for discovery. Do not treat the cover as a substitute for inline
  explanatory media.
- The post body must be valid Markdown/MDX.

Before accepting the draft, run the style-profile validation in
`references/writing-style.md`. Revise mismatches that affect voice, rhythm,
evidence, or prohibited language; do not mechanically copy catchphrases,
emotional outbursts, or personal anecdotes from the reference corpus.

### Step 3: Prepare Metadata

Derive these fields:

| Field | Rule |
|-------|------|
| `title` | Specific, readable Chinese title. |
| `slug` | ASCII lowercase kebab-case; if Chinese title has no ASCII, use a short English slug. |
| `excerpt` | 1-2 sentence summary under 180 chars. |
| `tags` | 2-5 tags, include `dev` and a concrete domain tag. |
| `author` | Default `Mark`. |
| `cover` | Required. Generate a 16:9 WebP cover and upload it before publishing. |
| Inline media | Required when the visual inventory contains meaningful evidence. |
| `source_kind` | Default `dev-skill`. |

### Step 4: Save Draft Locally

Create a temporary Markdown file in the current project, normally:

```bash
mkdir -p .output/dev-blog
```

Use a filename based on the slug, for example:

```text
.output/dev-blog/<slug>.md
```

Report the absolute path of the draft if publishing is skipped or fails.

### Step 5: Generate and Upload Cover

Every published blog post must have a cover image.

Use `baoyu-cover-image` to generate a 16:9 cover from the article title,
excerpt, tags, and core message. Keep it lightweight and suitable for blog
cards:

- Aspect: 16:9.
- Recommended dimensions: `type=minimal`, `rendering=hand-drawn`, `mood=subtle`.
- Visual direction: use an Anthropic-like minimalist editorial spot illustration style: warm off-white background, muted terracotta/sage/lavender accents, thin black hand-drawn linework, one small central metaphor, generous whitespace.
- Text: prefer `text=none` for blog list covers unless the user explicitly asks for title text; the page already renders the article title next to the image.
- Avoid dense tech UI, glowing cyber effects, gradients, charts, readable text, logos, and complex scenes.
- Save the `baoyu-cover-image` source and prompt files under `cover-image/<slug>/`.
- Convert the generated `cover.png` to WebP.
- Storage path: `app-assets/blog-covers/baoyu/anthropic-minimal/<slug>.webp`.
- Upload metadata: `contentType=image/webp`, `cacheControl=31536000`, `upsert=true`.
- Public URL: pass this value to the publish command using `--cover`.

Do not embed secrets, internal tokens, raw logs, or private customer details in
the image. If image generation fails, do not publish without a cover; save the
draft path and report the blocker.

### Step 6: Prepare and Upload Inline Media

When the visual asset inventory contains meaningful evidence:

1. Select only visuals with a distinct narrative role.
2. Crop or redact unrelated private details.
3. Convert static screenshots to WebP while keeping text legible.
4. Store durable local artifacts under an article-specific directory.
5. Run `scripts/upload_blog_assets.py` with `--dry-run`, then upload.
6. Replace local image paths in the draft with the returned public URLs.
7. Add specific Chinese alt text and explanatory captions.

Use the storage path:

```text
app-assets/blog-images/<slug>/<ordered-filename>.webp
```

Example:

```bash
WEB_ROOT="${SKILL_DEV_BLOG_WEB_ROOT:?set SKILL_DEV_BLOG_WEB_ROOT}"
python3 scripts/upload_blog_assets.py \
  --slug "<slug>" \
  --input "path/to/01-problem-overview.webp" \
  --input "path/to/02-key-detail.webp" \
  --env-file "$WEB_ROOT/.env.local" \
  --dry-run
```

Repeat without `--dry-run` after inspecting the manifest. Follow
`references/inline-media.md` for selection, compression, placement, captions,
and responsive-readability checks.

### Step 7: Publish to Supabase

Run a dry run first and inspect the payload:

```bash
WEB_ROOT="${SKILL_DEV_BLOG_WEB_ROOT:?set SKILL_DEV_BLOG_WEB_ROOT}"
python3 scripts/publish_blog_post.py \
  --input .output/dev-blog/<slug>.md \
  --title "<title>" \
  --slug "<slug>" \
  --excerpt "<excerpt>" \
  --tags "dev,skill-publisher" \
  --cover "<public-cover-url>" \
  --env-file "$WEB_ROOT/.env.local" \
  --require-inline-image \
  --dry-run
```

Add `--require-inline-image` whenever the visual inventory selected one or more
inline assets. Omit the flag only when no meaningful inline visual exists. The
publisher rejects local or relative image paths in public posts.

Then publish:

Publish by default after the dry run succeeds. Do not ask for confirmation
before running the non-dry-run publish command unless the user explicitly asks
for a confirmation gate. If the user asks for draft/local-only/no publish, stop
after saving the draft and report the absolute draft path.

```bash
WEB_ROOT="${SKILL_DEV_BLOG_WEB_ROOT:?set SKILL_DEV_BLOG_WEB_ROOT}"
python3 scripts/publish_blog_post.py \
  --input .output/dev-blog/<slug>.md \
  --title "<title>" \
  --slug "<slug>" \
  --excerpt "<excerpt>" \
  --tags "dev,skill-publisher" \
  --cover "<public-cover-url>" \
  --env-file "$WEB_ROOT/.env.local" \
  --require-inline-image
```

The script upserts by `slug`, sets `is_visible=true`, `show_in_index=true`, and
uses `source_kind=dev-skill`. A successful publish returns `/blog/<slug>`.

### Step 8: Verify the Public Article

Treat publication as complete only after checking the reader-visible result:

- the article URL returns HTTP 200;
- title, excerpt, cover, and visibility match the intended payload;
- every selected inline image URL returns HTTP 200 with an `image/*` content
  type;
- the public article contains the expected image URLs, alt text, and captions;
- the rendered `<img>` count matches the selected visual inventory;
- wide screenshots remain understandable at narrow reading widths, using a
  focused crop when necessary.

If the article uses inline visuals, a successful database upsert alone is not a
complete verification.

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | Markdown/MDX post body. |
| `--title` | (required) | Blog post title. |
| `--slug` | generated from title | URL slug. Use ASCII kebab-case. |
| `--excerpt` | first paragraph | Blog card summary. |
| `--tags` | `dev,skill-publisher` | Comma-separated tags. |
| `--author` | `Mark` | Author name. |
| `--cover` | (required by this workflow) | Public cover image URL. Generate and upload before publishing. |
| `--require-inline-image` | false | Fail when a visually sourced article contains no inline image. |
| `--published-at` | now | ISO timestamp. |
| `--source-kind` | `dev-skill` | Stored in `blog_posts.source_kind`. |
| `--source-path` | `dev-blog:<slug>` | Stable source key for traceability. |
| `--draft` | false | Set `is_visible=false`. |
| `--hide-from-index` | false | Set `show_in_index=false`. |
| `--env-file` | empty | Local `.env` file to load credentials from. |
| `--dry-run` | false | Print payload without writing to Supabase. |

## User Configuration

Set `SKILL_DEV_BLOG_WEB_ROOT` to the Skill Publisher website repo root. The
publisher also accepts `--env-file`, so users can keep Supabase credentials in
their own project-specific environment file.

Set the runtime preference `user.style_profile_path` to a readable Markdown or
text style profile when blog drafts should consistently follow a personal
writing voice. An explicit profile in the current request takes precedence.

## Dependencies

No third-party Python dependencies.

Publishing requires:

- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

Never print or copy these values into the article or final response.

## Additional Resources

- `references/inline-media.md` - Visual inventory, image selection, compression,
  upload, placement, captions, and live verification.
- `references/writing-style.md` - Style-profile resolution, extraction,
  authenticity boundaries, and pre-publish validation.
- `scripts/upload_blog_assets.py` - Deterministic uploader for public inline
  blog images.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
