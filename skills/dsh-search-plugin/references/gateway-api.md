# dshfind Plugin Gateway API

Verified 2026-08-27 against the OpenAPI document at
`https://dshfind.lovstudio.ai/openapi.json` and live probes. The gateway is
public, read-only, and needs no authentication. Production base URL per the
spec servers: `https://api.dshfind.com`. Override with the `DSHFIND_BASE_URL`
environment variable or the CLI `--base-url` flag when a mirror is needed.

## Health

`GET /healthz` returns `{"status": "ok", "plugins_loaded": N, ...}`. Check it
first when a search returns unexpected errors.

## Suggest

`GET /v1/suggest?q=<keyword>` returns up to 10 suggestion items:
`{"items": [{"type", "id", "label", "sub", "href", "stars", "featured"}]}`.
The keyword needs at least two trimmed characters; longer is better.

## List and filter plugins

`GET /v1/plugins` supports the query parameters `page`, `per_page` (max 100),
`q` (max 64 chars), `category`, `language`, `grade` (S/A/B/C), `owner`, `tag`,
`min_score` (0-100), `featured`, `official`, `archived`. Response:
`{"data": [Plugin], "page", "per_page", "total", "total_pages",
"data_version", "as_of", "generated_at"}`.

## Plugin detail

`GET /v1/plugins/{owner}/{repo}?snapshot_days=<1-90, default 7>` returns the
Plugin fields plus `i18n` (localized description, intro, highlights for
`en`, `ja`, `ko`, `zh`), `snapshots` (daily star history), `growth`
(`window_days`, `stars`, `contributors`), `data_version`, and `as_of`.

## Catalog snapshot

`GET /v1/catalog?data_version=<optional>` returns the whole catalog:
`{"data": [Plugin], "total", "data_version", "as_of", "generated_at"}`.

## Standard DSH market catalog

`GET /market/manifest.json` is the standard DSH catalog-source manifest:
`providerId` `com.dshfind.catalog`, transport `https-json` with endpoint
`https://api.dshfind.com/market/v1/plugins`, supported query keys `q`,
`category`, `cursor`, `limit` (default 50, max 100).

`GET /market/v1/plugins?q&category&limit&cursor` returns a MarketPage:
`{"schemaVersion", "generatedAt", "revision", "items": [MarketItem],
"page": {"nextCursor", "total"}}`. A MarketItem carries `id`, `name`,
`displayName`, `summary`, `repository.url`, `package.registry` and
`package.name` (npm), `publisher.name` and `publisher.url`, `categories`,
`latestVersion`, and `updatedAt`.

## GraphQL

`POST /graphql` with `{"query", "variables", "operationName"}` runs a public
read-only operation. Useful operations from the published SDL:

- `query DshFindDataset { dataset { dataVersion asOf } }`
- `query DshFindFacets { pluginFacets { categories { value count }
  languages { value count } tags { value count } grades { value count } } }`
- `query DshFindPlugins($first: Int = 20, $after: String, $filter: PluginFilter,
  $sort: PluginSort = DEFAULT, $order: SortOrder = DESC) {
  plugins(first: $first, after: $after, filter: $filter, sort: $sort,
  order: $order) { nodes { fullName name owner description category grade
  score stars } pageInfo { hasNextPage endCursor } } }`

## Plugin fields used by search and fit analysis

| field | meaning |
| --- | --- |
| `full_name` | `owner/repo` |
| `description` | short English/Chinese one-liner |
| `tags` | topic tags, e.g. cordis, memory, web-ui |
| `language` | primary implementation language |
| `stars`, `contributors` | GitHub popularity and team size |
| `pushed_at` | last push, freshness signal |
| `archived` | repo archived by its owner |
| `category` | catalog category, e.g. skin, memory, automation |
| `score` | 0-100 quality score, or null when unrated |
| `grade` | S/A/B/C derived tier, or null when unrated |
| `scored_at`, `score_version` | score provenance |
| `is_featured`, `is_official`, `is_insider` | catalog placement flags |
| `is_risky`, `risk_note` | risk flag and its note |
| `is_plugin` | whether the repo is a DSH plugin rather than an app |
| `install` | `kind` in release / npm / git / build-required / not-installable; `source` in manual / auto; `cmd`; `pkg_name`; `pkg_version`; `npm_published` |
| `first_seen_at`, `last_synced_at` | index lifecycle |
| `url`, `repository_url` | canonical links |

## Behavior notes

- A keyword needs at least two trimmed characters; empty or weak results mean
  retry with synonyms, a category facet, or a broader keyword, then the
  `/v1/catalog` or `/graphql` endpoints before concluding absence.
- `score` and `grade` can be null for newly indexed plugins; treat null as
  unrated, never as failure. Use stars, `pushed_at`, `description`, and the
  `install` evidence instead.
- `install.kind` decides the usable path: `npm` (install the package), `git`
  (clone and mount from source), `release` (download an artifact),
  `build-required` (needs a local build), `not-installable` (app or web UI,
  not a plugin package).
- The gateway rate-limits; on HTTP 429 back off and retry once.
