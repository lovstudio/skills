# Inline Media Workflow

Use this workflow when the conversation, repository, or generated artifacts
contain screenshots, diagrams, charts, before/after images, or other visual
evidence that materially improves the article.

## 1. Build a Visual Asset Inventory

List every relevant visual before drafting. Include:

- images attached in the current conversation;
- local paths supplied by the user;
- screenshots used to reproduce or verify the issue;
- generated diagrams, charts, and comparison renders;
- existing repository assets that explain the implementation or result.

Classify each item:

| Role | Use |
|------|-----|
| Problem evidence | Show the original symptom or failed state. |
| Key detail | Crop or isolate the exact visual clue that changed the investigation. |
| Before/after | Prove the user-visible effect of the change. |
| Architecture | Explain relationships that prose alone makes difficult to follow. |
| Decorative | Exclude unless it improves orientation or pacing. |

Default to including user-provided visual evidence when it directly supports
the story. Treat it as article source material, not merely internal debugging
context. Exclude an item only when it is redundant, unreadable, irrelevant, or
contains information that should not be public.

## 2. Design the Visual Narrative

Place images where the reader needs them:

1. Frame what the reader should notice.
2. Insert the image immediately after that framing sentence.
3. Add descriptive alt text that states what is visible.
4. Add an italic caption that explains why the image matters.

Use actual screenshots for observed product behavior. Use diagrams for
invisible system relationships. Keep the cover focused on discovery rather than
reusing it as evidence inside the article.

For wide desktop screenshots, add a focused crop when the critical detail would
be too small at mobile width. A six-minute technical article usually needs one
to four meaningful inline visuals when such evidence exists; use fewer when
each image already carries substantial information.

Avoid:

- a gallery detached from the relevant paragraphs;
- repeated screenshots with no distinct explanatory role;
- captions that merely repeat the alt text;
- screenshots containing tokens, private messages, personal paths, or unrelated
  identifying information;
- decorative images that interrupt a short, already-clear explanation.

## 3. Prepare Durable Assets

Preserve technical text and UI details while controlling payload size:

- prefer WebP for static screenshots;
- use quality 80-86 as a starting range;
- keep wide screenshots around 1600-2000 pixels unless fine text requires more;
- inspect the converted image before upload;
- use ordered ASCII filenames such as `01-problem-overview.webp`;
- keep local source or converted assets under a stable article-specific
  directory when the repository records publishing artifacts.

Example conversion:

```bash
cwebp -q 84 -resize 1600 0 screenshot.png -o 01-problem-overview.webp
```

Use a focused crop instead of aggressive compression when small text becomes
hard to read.

## 4. Upload Inline Assets

Upload selected files to:

```text
app-assets/blog-images/<slug>/<filename>
```

Run a dry run first:

```bash
python3 scripts/upload_blog_assets.py \
  --slug "<slug>" \
  --input "path/to/01-problem-overview.webp" \
  --input "path/to/02-key-detail.webp" \
  --env-file "$WEB_ROOT/.env.local" \
  --dry-run
```

Then repeat without `--dry-run`. Replace every local Markdown image path with
the returned public URL.

Embed each image with specific alt text and a useful caption:

```markdown
![A complete URL is split across two terminal rows, with secret.html on the second row](<public-url>)

_Figure 2: The reader sees one URL, while the terminal resolver receives two physical fragments._
```

Write the actual article and captions in Chinese unless the user requests
another language.

## 5. Verify the Published Result

After publishing:

1. Confirm the article URL returns HTTP 200.
2. Confirm every selected image URL returns HTTP 200 with an `image/*` content type.
3. Confirm the public article HTML contains every expected image URL and caption.
4. Confirm alt text is present.
5. Inspect desktop and narrow-width readability when layout or fine screenshot
   text is a material concern.
6. Confirm the image count matches the inventory's included items.

Treat missing images, local-only paths, broken URLs, absent captions, or
unreadable mobile details as publishing defects.

## 站点特定备注

- lovstudio.ai/blog 列表页是客户端渲染：`curl` 抓到的 HTML 里一篇文章都没有，grep 不到不等于没进列表；列表回读必须用 ego-browser 渲染后再查卡片（2026-09-09, a9b060d）
- 内联图按同一 object path 覆盖上传后，浏览器和 CDN 会继续返回旧图（`cacheControl=31536000`）；回读尺寸要带 `?v=<ts>` 绕开缓存，否则会误判成上传没生效（2026-09-09, a9b060d）
