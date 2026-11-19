# Changelog

## 0.7.3

- The suanli adapter accepts a `suanli-live-checks/v1` evidence file (`evidenceFiles.liveChecks` or `--live-checks`) and upgrades the matching operations from documentation-only to `live-verified-token-mode` / `live-verified-rsa-mode`, keeping the original documentation sources and adding the check under `x-evidence.liveCheck`.
- Only successful read-only checks are accepted: write operations, non-`"0000"` results, endpoints missing from the generated contract, and credential-looking values in the file stop generation.
- The manifest reports `liveVerified` and `liveVerifiedEndpoints`; the bundle README, drilldown page, and per-command CLI help show which operations were verified live.

## 0.7.2

- The generated suanli CLI and Swagger proxy read the macOS Keychain items `suanli-token` and `suanli-llm-key` when `SUANLI_TOKEN` or `SUANLI_LLM_API_KEY` is missing, so commands work from shells that do not inherit the variables; `SUANLI_KEYCHAIN=0` turns this off.
- `--dry-run` reports where the credential came from (`flag`, `env`, `keychain`) without echoing it.

## 0.7.1

- Synced `pricing-card.yaml` to the Skill version and refreshed its basis and review trigger for four built-in targets.
- Recorded the GitHub and LovStudio distribution state in the Skill Card.

## 0.7.0

- Added a `suanli.cn` (共绩算力) target adapter: 81 Open API operations from the vendor's public Apifox share plus the 2 documented operations of its OpenAI-compatible LLM service.
- Added `scripts/suanli_discover.py`, which lists the share through its `llms.txt`, extracts each page's vendor OpenAPI fragment verbatim, and clears credential header example values before anything is written.
- Merged the 3.0.1 fragments into one OpenAPI 3.1 document: `nullable` rewritten, invalid vendor security scheme types fixed, the `token` header expressed as `ApiKeyAuth`, duplicate method + path pages merged with every source kept in `x-evidence`, and auth headers marked as inferred where the vendor page omits them.
- Every operation carries `x-observation` (`documented-apifox-openapi` or `documented-docs-example`); 39 state-changing operations are marked `x-write-operation`, and `liveVerified` stays 0 because both gateways authenticate before routing.
- The generated SDK implements token and RSA modes (signature verified byte-for-byte against the vendor's Python sample) and platform-key body encryption in 244-byte chunks; the CLI requires `--confirm-write` for writes, and the local Swagger proxy signs requests from environment variables and refuses writes unless started with `--allow-write`.

## 0.6.0

- Added a self-hosted Plane target adapter covering the full REST API v1 surface (69 paths / 130 operations).
- Evidence is the instance's own drf-spectacular export, exported through a one-off process without changing the running configuration, cross-checked by live probes (17/17 endpoints: 401 unauthenticated, 403 with an invalid key).
- Every operation carries an `x-observation` grade; write operations are marked as schema-only and were never executed.
- Generated `lov-plane-cli` builds its command table from the bundled `openapi.json` at startup, so all 130 operations are addressable without per-endpoint code.
- Corrected `servers` from the container-internal address to the proxy-exposed one; credentials stay in the environment and are never written to generated files.
- Taught `isTarget` to accept dotless self-hosted hostnames such as `localhost`.

## 0.5.0

- Added the real public `POST /graphql` contract with runnable dataset, facets, cursor-list, and rich-detail examples.
- Added SDK and generated CLI support for all four public GraphQL root queries plus arbitrary read-only query execution.
- Bundled the published `GET /graphql/schema` SDL because the service intentionally disables introspection.
- Always supplies every declared GraphQL variable because the service's constrained executor rejects omitted nullable/defaulted variables.
- Kept the existing category shortcut while avoiding fabricated REST aliases for GraphQL operations.

## 0.4.0

- Added the missing public plugin-category discovery operation through the real GraphQL `pluginFacets.categories` source.
- Added category counts to OpenAPI, Apifox, SDK, generated CLI, discovery evidence, and the API graph filter workflow.
- Kept the REST `category` filter linked to its discoverable values without inventing a non-existent `/v1/categories` route.

## 0.3.0

- Added an Apifox-ready OpenAPI artifact to every generated dshfind bundle.
- Imported the public server as an environment, declared explicit no-auth behavior, and added safe request examples for one-click debugging.
- Excluded volatile `data_version` and `cursor` defaults so imported requests do not become stale.

## 0.2.0

- Added a verified `dshfind.com` adapter for the public read-only plugin directory and standard market feed.
- Added typed OpenAPI 3.1, JavaScript SDK, API graph, task-focused CLI, saved public discovery evidence, and live regression coverage.
- Kept authenticated voting, comments, forum writes, cookies, and tokens outside the generated dshfind bundle.

## 0.1.0

- Added the internal `lov-cli2anything` Single Skill.
- Connected the Skill to the bundled cli2anything++ runtime through a safe Python wrapper.
- Recorded the verified ZenMux discovery-to-bundle case and local distribution state.
