# cli2anything++

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

cli2anything++ is an authorization-first CLI for turning observed API behavior into:

- an OpenAPI 3.1 contract
- a lightweight JavaScript SDK
- a repeatable discovery evidence file

The repository is also the canonical source of the internal Agent Skill
`lov-cli2anything`; `SKILL.md` and the Node runtime ship together so catalog
mirrors and local installations retain the complete executable project.

## Install the Skill

```bash
npx lovstudio skills add cli2anything -g -y
```

The installed Skill is invoked as `lov-cli2anything`.

The ZenMux target validates the requested workflow:

- log list: `POST /api/api_key/activity`
- log activity detail: `GET /api/api_key/activity/{requestId}`
- generation metadata: `GET /api/v1/management/generation?id=...`
- generation metadata fallback: `GET /api/v1/generation?id=...` (deprecated but observed in the current frontend bundle)
- raw request payload: `GET /api/v1/generation/request?id=...&type=userRequest|providerRequest`
- raw response payload: `GET /api/v1/generation/response?id=...&type=userResponse|providerResponse`

Use this only with accounts and traffic you are authorized to inspect.

## Quick Start

```bash
cd cli2anything-plus-plus
npm install
npm test
npm run discover:zenmux
npm run generate:zenmux
node ./bin/cli2anything.mjs zenmux.ai --filter-keyword log
```

The generated OpenAPI file is written to:

```text
openapi/zenmux.openapi.json
```

Discovery evidence is written to:

```text
artifacts/zenmux-discovered.json
```

The `cli2anything` entrypoint generates a focused SDK/OpenAPI bundle:

```bash
cli2anything zenmux.ai --filter-keyword log
cli2anything zenmux.ai --filter-keyword log --output swagger
cli2anything zenmux.ai --filter-keyword log --output cli
```

Local equivalent before installing/linking the package:

```bash
node ./bin/cli2anything.mjs zenmux.ai --filter-keyword log
```

Default output:

```text
generated/zenmux-ai-log/
```

That bundle includes `manifest.json`, `openapi.json`, `discovery.filtered.json`, and a portable `sdk/` folder. For ZenMux `log`, the dependency closure includes API key filter endpoints, finish reason filters, generation metadata, and request/response payload APIs.

`--output swagger` additionally writes a local Swagger UI and opens a localhost page backed by a browser-session proxy:

```text
generated/zenmux-ai-log/swagger/index.html
generated/zenmux-ai-log/swagger/server.mjs
```

Swagger `Try it out` does not require manual Cookie/API key input. Requests go to the local proxy, then the proxy executes same-origin `fetch` inside the logged-in ZenMux browser page through the cli2anything++ browser bridge.

By default, Swagger mode reuses your existing Chrome through one universal local unpacked extension bridge:

```bash
cli2anything zenmux.ai --filter-keyword log --output swagger
```

The command opens the global extension folder and `chrome://extensions`. Load this folder once; every generated target and every active local Swagger server can use the same extension. By default cli2anything++ writes:

```text
~/.cli2anything-plus-plus/browser-extension
```

Set `--extension-dir <path>` or `CLI2ANYTHING_EXTENSION_DIR` if you want a different fixed extension folder.

Swagger `Try it out` goes through the local proxy, then the extension injects the request into a matching site tab, reusing that site's existing login.

CDP mode is still available when you explicitly want it, but Chrome 136+ does not allow remote debugging against the default data directory. Use it only with an already-debuggable browser or an isolated profile:

```bash
cli2anything zenmux.ai --filter-keyword log --output swagger --browser-bridge cdp --browser-profile isolated
```

`--output cli` writes a local CLI package named `cli-zenmux-ai`, links it with `npm link`, and opens the generated package directory:

```bash
cli-zenmux-ai logs:list --cdp http://127.0.0.1:9222 --days 1
cli-zenmux-ai logs:detail <requestId> --cdp http://127.0.0.1:9222
cli-zenmux-ai filters:finish-reasons --cdp http://127.0.0.1:9222
```

## SDK Usage

ZenMux exposes two auth surfaces in this workflow:

- `GET /api/v1/management/generation` is the documented management API and uses `ZENMUX_API_KEY`.
- `POST /api/api_key/activity` and `GET /api/api_key/activity/{requestId}` are dashboard-derived endpoints. A live API-key-only smoke test reached the endpoint but returned `missing csrf token`, so those calls need an authenticated console `Cookie` plus CSRF token.
- The public frontend bundle currently uses `XSRF-TOKEN` cookie -> `X-XSRF-TOKEN` header and sends `x-api-version: 2026-04-20`. The SDK defaults to that header shape; override with `ZENMUX_CSRF_HEADER` or `ZENMUX_API_VERSION` if ZenMux changes it.

```js
import { ZenMuxClient } from "./src/zenmux-client.mjs";

const client = new ZenMuxClient({
  apiKey: process.env.ZENMUX_API_KEY,
  cookie: process.env.ZENMUX_COOKIE,
  csrfToken: process.env.ZENMUX_CSRF_TOKEN || process.env.ZENMUX_XSRF_TOKEN
});

const logs = await client.listLogs({
  startTime: Date.now() - 24 * 60 * 60 * 1000,
  stopTime: Date.now(),
  pageNo: 1,
  pageSize: 20
});

const requestId = logs.data?.[0]?.requestId;
const detail = await client.getLogDetail(requestId, {
  includePayloads: true,
  requestType: "userRequest",
  responseType: "userResponse"
});
```

## CLI Usage

```bash
ZENMUX_COOKIE='...' ZENMUX_XSRF_TOKEN='...' node ./bin/cli2anything.mjs logs:list --days 1
ZENMUX_API_KEY=... ZENMUX_COOKIE='...' ZENMUX_XSRF_TOKEN='...' node ./bin/cli2anything.mjs logs:detail <requestId>
```

The SDK keeps payloads protocol-native, so text, image `inlineData`, file data, tool calls, and provider-specific fields are preserved rather than flattened.

## Browser Session Mode

For the no-manual-secret path, attach to a browser that the user has already logged into. The SDK executes same-origin `fetch` inside that browser page, so cookies and XSRF stay inside the browser context and are not copied into config files.

Chrome needs a DevTools endpoint before tools can attach. A dedicated profile is the least surprising local setup:

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --user-data-dir="$PWD/.chrome-profile" \
  https://zenmux.ai/platform/logs
```

After logging in once in that browser window:

```bash
node ./bin/cli2anything.mjs browser:logs:list --cdp http://127.0.0.1:9222 --days 1
node ./bin/cli2anything.mjs browser:logs:detail <requestId> --cdp http://127.0.0.1:9222
node ./bin/cli2anything.mjs browser:capture-zenmux --cdp http://127.0.0.1:9222 --seconds 20
```

`browser:capture-zenmux` redacts credential-bearing headers and records body shapes by default. Use `--include-bodies` only when the account data is safe to persist locally.
