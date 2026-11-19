---
name: lov-cli2anything
description: >
  将已授权观察到的网站 API 转成可验证的 OpenAPI、SDK、Swagger 或任务型 CLI。适用于“把这个网站 API 变成 CLI”“生成可调用 Swagger”以及 “turn observed APIs into a CLI”。
license: MIT
metadata:
  author: LovStudio
  version: "0.7.3"
  card_standard: lovstudio/skill-card/v1
  tags:
    - api-discovery
    - cli
    - openapi
    - swagger
    - sdk
    - apifox
  compatibility: "Portable Agent Skills format. Requires Python 3.8+, Node.js 20+, and the bundled cli2anything++ project."
  dependencies: []
---

# 接口工坊 · API Studio

使用项目内的 cli2anything++ 运行时，把已授权的 API 观察证据转为可回读的
OpenAPI、JavaScript SDK、Swagger UI 或本地 CLI 包。当前内置目标适配器是
ZenMux、dshfind、自托管 Plane 与共绩算力（suanli.cn）；其他站点必须先实现并验证
目标适配器，不能伪装成已支持。

## Triggers

### Activate when

- “把这个网站的 API 变成 CLI / SDK / OpenAPI。”
- “从 ZenMux 日志接口生成可交互 Swagger。”
- “生成导入 Apifox 后可直接调试的 OpenAPI。”
- “用 cli2anything++ 分析这份授权的 API discovery 证据。”
- “Turn these authorized observed APIs into a CLI or Swagger bundle.”

### Do not activate when

- 为已有本地应用或源码项目从零设计通用 CLI；使用 `lov-cli-creator`。
- 为 uni-app 新增 FastAPI 聚合网关；使用 `lov-api-creator`。
- 用户无权访问目标账户、流量或接口，或要求导出他人的 Cookie、Token、密钥。
- 只需要调用一份现成 OpenAPI，而不需要发现、生成或封装能力。

## User Profile (cross-session)

Read `skill.yaml` on every invocation. Resolve context in this order: the current
request, project context, `skills.lov-cli2anything.records`, shared preferences,
shared user/workspace Profile, then safe defaults. Keep resolved personal values
out of the portable source.

Persist only a directly stated durable preference, such as a default output mode:

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-cli2anything \
  --path records.output_mode \
  --value '"swagger"' \
  --confirm
```

Report the saved Profile path. Never persist inferred paths, credentials, cookies,
tokens, captured payloads, or private traffic. See `references/user-profile.md`.

## Skill Group Composition

Read `references/skill-composition.md` before invoking an adjacent Skill. This is
a Single Skill backed by the cli2anything++ project; sibling Skills are optional
artifact handoffs and never hidden runtime dependencies.

## Workflow (MANDATORY)

Follow these steps in order. Do not report generated files as usable until their
manifest, OpenAPI document, runtime source, and tests have been checked.

### Step 0: Resolve runtime context

1. Resolve `SKILL_DIR` from the active Skill context.
2. Verify these required resources exist:
   - `scripts/cli2anything.py`
   - `scripts/profile_store.py`
   - `references/skill-composition.md`
3. Read the shared Profile for `lov-cli2anything`.
4. Confirm Node.js 20+ is available by running `node --version`.

If a required resource is missing, name its relative path and stop before
producing a partial result.

### Step 1: Establish target, authority, and output

- Identify the target host, intended API workflow, filter keyword, discovery
  evidence, and desired output: `bundle`, `swagger`, or `cli`.
- Confirm the user owns the account/traffic or is otherwise authorized before any
  live browser-session or traffic discovery step. Existing public or user-supplied
  discovery artifacts may be processed offline.
- Current built-in targets: `zenmux.ai` for authorized dashboard log workflows,
  `dshfind.com` for its public read-only plugin directory and market feed,
  `localhost` for a user-owned self-hosted Plane instance, and `suanli.cn` for
  the 共绩算力 Open API plus its OpenAI-compatible LLM service, built from the
  vendor's public Apifox share and docs.
  For another host, inspect the project and report that a target adapter is
  required; do not claim generic support exists.
- Default to offline supplied evidence when available. Never copy browser cookies
  or tokens into Skill files, generated examples, logs, or Profile records.

### Step 2: Generate the requested artifact

Run the project through the portable wrapper:

```bash
python3 "$SKILL_DIR/scripts/cli2anything.py" zenmux.ai \
  --filter-keyword log \
  --discovery artifacts/zenmux-discovered.json \
  --out generated/zenmux-ai-log
```

For Swagger without opening a browser:

```bash
python3 "$SKILL_DIR/scripts/cli2anything.py" zenmux.ai \
  --filter-keyword log \
  --output swagger \
  --no-open \
  --discovery artifacts/zenmux-discovered.json \
  --out generated/zenmux-ai-log
```

For a self-hosted Plane instance, export the evidence from the running container
first, then generate; the export runs as a one-off process and does not change the
instance configuration:

```bash
docker exec -e ENABLE_DRF_SPECTACULAR=1 plane-api-1 \
  sh -c 'cd /code && python manage.py spectacular --file /tmp/plane-schema.json --format openapi-json'
docker cp plane-api-1:/tmp/plane-schema.json "$SKILL_DIR/artifacts/plane-schema.raw.json"

python3 "$SKILL_DIR/scripts/cli2anything.py" localhost \
  --output cli --no-link --no-open \
  --discovery artifacts/plane-discovered.json \
  --out generated/lov-plane-cli
```

The Plane bundle grades every operation with `x-observation`: `live-probe-401-403`
for endpoints confirmed by unauthenticated/invalid-key probes, and
`vendor-generated-schema` for the rest. Write operations are additionally marked
`x-write-operation` and must not be reported as executed. `servers` must name the
proxy-exposed address first and the container-internal one second. The generated
CLI builds its command table from the bundled `openapi.json` at startup, so its
command count must equal the manifest `operationCount`.

For 共绩算力 (`suanli.cn`), collect evidence from public pages only; no console
login or API key is needed. Write the curated discovery file beside the fragments
(auth rules, LLM operations, gateway probes, doc conflicts; see the adapter's
`createSuanliOpenapi` checks), keep both outside the Skill when they belong to a
client project, then generate:

```bash
python3 "$SKILL_DIR/scripts/suanli_discover.py" \
  --out <evidence-dir>/suanli-apifox-fragments.json \
  --docs-out <evidence-dir>/suanli-docs-pages.json

python3 "$SKILL_DIR/scripts/cli2anything.py" suanli.cn \
  --output bundle,swagger,cli --no-link --no-open \
  --discovery <evidence-dir>/suanli-discovered.json \
  --out <output-dir>
```

The discovery script needs PyYAML and, as a precaution, clears example values of
credential headers (`token`, `sign_str`) before writing evidence. Every operation is graded `documented-apifox-openapi` or
`documented-docs-example`; both gateways authenticate before routing, so
unauthenticated probes cannot confirm individual endpoints. After the user runs
read-only calls with their own key, record each successful call in a
`suanli-live-checks/v1` file (endpoint, request summary, `code`, data shape; never
the key) referenced as `evidenceFiles.liveChecks` in the discovery file or passed
with `--live-checks`; those operations become `live-verified-token-mode` (or
`-rsa-mode`) and count toward the manifest `liveVerified`. The adapter rejects
write operations, failed results, unknown endpoints, and credential-looking values
in that file. The SDK signs `{path}\n{version}\n{timestamp}\n{token}\n{body}`
(GET signs `path?query`), encrypts flagged bodies with the platform public key in
244-byte chunks before signing, and treats any envelope `code` other than `"0000"`
as an error. The generated CLI refuses write operations without `--confirm-write`,
and the Swagger proxy refuses them unless started with `--allow-write`. When
`SUANLI_TOKEN` or `SUANLI_LLM_API_KEY` is missing, both read the macOS Keychain items
`suanli-token` and `suanli-llm-key`; `SUANLI_KEYCHAIN=0` turns this off.

Use `--output cli` only when a task-focused generated CLI is requested. Do not
run `npm link` unless local installation is part of the current request; pass
`--no-link` for generation-only work.

For the public dshfind plugin directory CLI:

```bash
python3 "$SKILL_DIR/scripts/cli2anything.py" dshfind.com \
  --filter-keyword plugins \
  --output cli \
  --no-link \
  --no-open \
  --discovery artifacts/dshfind-discovered.json \
  --out generated/cli-dshfind-com
```

The dshfind bundle also writes `apifox/openapi.json` and
`apifox/README.md`. The Apifox contract must define the public server, explicit
no-auth security, and safe request examples that do not pin stale
`data_version` or `cursor` values. It must expose the public GraphQL
`pluginFacets.categories` query as a standalone category-discovery operation so
callers can discover valid REST `category` filter values before listing plugins.
It must also expose the real read-only `POST /graphql` request shape, runnable
examples for all four public root queries (`dataset`, `plugin`, `plugins`, and
`pluginFacets`), and the published `GET /graphql/schema` SDL. Do not invent
REST-looking aliases for GraphQL operations.

### Step 3: Validate the result

For a generated bundle, verify:

- `manifest.json` names the expected target and scope;
- `openapi.json` parses as OpenAPI 3.1 and contains the expected operations;
- `api-graph.json` contains the workflow edges required by the selected scope;
- `sdk/index.mjs` and any generated CLI entrypoint pass `node --check`;
- dshfind output includes an Apifox OpenAPI with an imported server, explicit
  no-auth security, safe default examples, the generic GraphQL POST operation,
  and the published SDL;
- Swagger mode writes `swagger/index.html`, `swagger/drilldown.html`, and
  `swagger/server.mjs` without embedding cookies or API keys.

Run the maintained project regression suite after behavior changes:

```bash
python3 "$SKILL_DIR/scripts/cli2anything.py" --project-test
```

Report the concrete output directory, selected target/scope, validation result,
and any missing target adapter or live authorization evidence.

## Dependencies

- Python 3.8+ for the Skill wrapper and Profile reader.
- Node.js 20+ and npm dependencies declared by cli2anything++.
- An authorized account/browser session only for live browser-session workflows.
- No third-party credentials are required for offline generation from an existing
  discovery artifact.
