# Discovery Playbook

Broad discovery is an agent/browser task; deterministic scripts then normalize
the observed artifacts. Search current web results when the task is run because
indexes, mirrors, and availability change.

## Query matrix

Run relevant variants in both web and image search:

- exact handle and former handles, with and without `@`;
- display name plus `site:x.com` and `site:twitter.com`;
- exact distinctive quote fragments in the original language and known
  translations;
- exact status ID and quoted `x.com/handle/status/ID`;
- observed `t.co` short links;
- handle or quote plus Chinese terms such as 截图、推特、原文、长文、删帖、爆料;
- handle or quote across news, Weibo, WeChat public pages, Telegram mirrors,
  forums, LinkedIn, TradingView, Yahoo, exchange news, and cached snippets.

Do not limit discovery to English search results. Screenshot-heavy Chinese
reposts often preserve visible text that ordinary text search does not index.

## Page inspection

For each promising result, inspect:

- visible X/Twitter embed cards and their “view on X” links;
- page source for `twitter.com/.../status/`, `x.com/.../status/`, `t.co`,
  `blockquote class=twitter-tweet`, JSON-LD, and Open Graph descriptions;
- image URLs and captions; save original image bytes before OCR;
- redirect targets for short links;
- timestamps, display names, handles, reply/quote context, and media thumbnails.

## Archive paths

- Query Wayback CDX for exact status URLs before wildcard account patterns.
- Inspect the archived payload; a `200` CDX row can still be a JavaScript shell
  or error page with no post text.
- Query Common Crawl indexes for exact URLs when Wayback lacks payload text.
- Preserve index timestamp, original URL, digest or WARC filename, and extractor.

## Stopping rule

Stop when the requested known IDs are reconciled and additional query variants
produce no new candidates, or when the user's time/scope boundary is reached.
Report queries attempted, new IDs found, recovered count, unresolved count, and
the precise reason completeness cannot be claimed.
