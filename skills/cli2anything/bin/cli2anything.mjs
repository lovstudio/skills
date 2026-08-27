#!/usr/bin/env node
import { spawn } from "node:child_process";
import { chmod, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { createServer as createNetServer } from "node:net";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createZenmuxOpenapi } from "../src/zenmux-openapi.mjs";
import { createZenmuxApiGraph } from "../src/api-graph.mjs";
import { createDrilldownHtml } from "../src/drilldown-html.mjs";
import { ZenMuxClient } from "../src/zenmux-client.mjs";
import { BrowserPageSession } from "../src/browser-cdp.mjs";
import { ZenMuxBrowserClient } from "../src/zenmux-browser-client.mjs";

const ZENMUX_HOME = "https://zenmux.ai/";
const ZENMUX_LOGS_URL = "https://zenmux.ai/platform/logs";
const EXTENSION_BRIDGE_VERSION = "0.1.9";
const CDN_BASE = "https://cdn.marmot-cloud.com/page/tbox-router-home/";

async function main() {
  const [command, ...args] = process.argv.slice(2);
  try {
    if (isTarget(command)) return await cli2Anything(command, args);
    if (command === "discover-zenmux") return await discoverZenmux(args);
    if (command === "generate-zenmux") return await generateZenmux(args);
    if (command === "logs:list") return await listLogs(args);
    if (command === "logs:detail") return await logDetail(args);
    if (command === "browser:capture-zenmux") return await browserCaptureZenmux(args);
    if (command === "browser:logs:list") return await browserListLogs(args);
    if (command === "browser:logs:detail") return await browserLogDetail(args);
    usage();
    process.exit(command ? 1 : 0);
  } catch (error) {
    if (String(error?.body?.message || error?.message || "").toLowerCase().includes("csrf")) {
      console.error("ZenMux rejected the dashboard log request because a console CSRF/session credential is missing.");
      console.error("Set ZENMUX_COOKIE and ZENMUX_CSRF_TOKEN or ZENMUX_XSRF_TOKEN, or pass equivalent headers through the SDK.");
    }
    console.error(error?.stack || error?.message || String(error));
    process.exit(1);
  }
}

function usage() {
  console.log(`cli2anything++

Commands:
  cli2anything <host> [--filter-keyword <keyword>] [--depth <n>]
                                  Generate an API SDK/OpenAPI bundle.
                                  Without --filter-keyword, include all discovered APIs.
                                  --depth 0 means no route depth limit.
                                  Add --output swagger to open Swagger UI.
                                  Add --output cli to create/link cli-<host>.
                                  Swagger uses --browser-profile existing by default.
  discover-zenmux --out <file>     Fetch public ZenMux bundles and record endpoint evidence.
  generate-zenmux --out <file>     Write the observed ZenMux OpenAPI 3.1 contract.
  logs:list [--days 7]             Call ZenMux dashboard log list with console auth.
  logs:detail <requestId>          Call activity, generation, request, and response payload APIs.
  browser:capture-zenmux           Capture ZenMux API traffic from an attached logged-in browser.
  browser:logs:list [--days 7]     Call ZenMux log list inside an attached logged-in browser.
  browser:logs:detail <requestId>  Call ZenMux detail APIs inside an attached logged-in browser.

Examples:
  cli2anything zenmux.ai --output swagger
  cli2anything zenmux.ai --output swagger --depth 0
  cli2anything zenmux.ai --filter-keyword log
  cli2anything zenmux.ai --filter-keyword log --output swagger
  cli2anything zenmux.ai --filter-keyword log --output swagger --restart-existing-browser
  cli2anything zenmux.ai --filter-keyword log --output swagger --browser-profile isolated
  cli2anything zenmux.ai --filter-keyword log --output cli
  node ./bin/cli2anything.mjs zenmux.ai --filter-keyword log
  node ./bin/cli2anything.mjs discover-zenmux --out ./artifacts/zenmux-discovered.json
  node ./bin/cli2anything.mjs generate-zenmux --out ./openapi/zenmux.openapi.json
  ZENMUX_COOKIE='...' ZENMUX_XSRF_TOKEN='...' node ./bin/cli2anything.mjs logs:list --days 1
  node ./bin/cli2anything.mjs browser:logs:list --cdp http://127.0.0.1:9222 --days 1
`);
}

async function cli2Anything(target, args) {
  const host = normalizeTargetHost(target);
  const filterKeyword = normalizeOptionalKeyword(getArg(args, "--filter-keyword"));
  const depth = parseDepth(getArg(args, "--depth") ?? "0");
  const hasExplicitDepth = args.includes("--depth");
  const outputMode = getArg(args, "--output") || "bundle";
  if (!["bundle", "swagger", "cli"].includes(outputMode)) {
    throw new Error("--output must be one of: swagger, cli");
  }
  if (host !== "zenmux.ai") {
    throw new Error(`No built-in target plugin for ${host}. Current MVP supports zenmux.ai.`);
  }

  const outDir = getArg(args, "--out") || (
    outputMode === "cli"
      ? `generated/cli-${slugify(host)}`
      : filterKeyword
        ? `generated/${slugify(host)}-${slugify(filterKeyword)}`
        : `generated/${slugify(host)}`
  );
  const discovery = getArg(args, "--discovery")
    ? JSON.parse(await readFile(resolve(getArg(args, "--discovery")), "utf8"))
    : await discoverZenmuxData({ filterKeyword, depth, forceAllRoutes: !filterKeyword || hasExplicitDepth });
  const apiPackage = createZenmuxFilteredPackage({ target: host, filterKeyword, discovery, depth });
  const openapi = createZenmuxOpenapiForPackage({ apiPackage });
  const apiGraph = createZenmuxApiGraph({ target: host, filterKeyword: apiPackage.manifest.filterKeyword, manifest: apiPackage.manifest });

  await writeJson(`${outDir}/manifest.json`, apiPackage.manifest);
  await writeJson(`${outDir}/discovery.filtered.json`, apiPackage.filteredDiscovery);
  await writeJson(`${outDir}/openapi.json`, openapi);
  await writeJson(`${outDir}/api-graph.json`, apiGraph);
  await writeText(`${outDir}/README.md`, createGeneratedReadme(apiPackage.manifest));
  await writeSdkBundle(`${outDir}/sdk`);

  if (outputMode === "swagger") {
    const swaggerPath = `${outDir}/swagger/index.html`;
    const drilldownPath = `${outDir}/swagger/drilldown.html`;
    const serverPath = `${outDir}/swagger/server.mjs`;
    const extensionDir = getArg(args, "--extension-dir") || process.env.CLI2ANYTHING_EXTENSION_DIR || defaultExtensionDir();
    const extensionDisplayDir = resolve(extensionDir);
    const browserBridge = getArg(args, "--browser-bridge") || process.env.CLI2ANYTHING_BROWSER_BRIDGE || "extension";
    await rm(`${outDir}/extension`, { recursive: true, force: true });
    await writeText(swaggerPath, createSwaggerHtml({ manifest: apiPackage.manifest, openapi, extensionDir: extensionDisplayDir }));
    await writeText(drilldownPath, createDrilldownHtml({ manifest: apiPackage.manifest, openapi, apiGraph, extensionDir: extensionDisplayDir }));
    await writeText(serverPath, createSwaggerServer({ extensionDir: extensionDisplayDir, targetHost: apiPackage.manifest.target }));
    await writeSwaggerExtension(extensionDir);
    if (!args.includes("--no-open")) {
      const port = await findOpenPort(Number(getArg(args, "--port") || "47831"));
      const cdpEndpoint = getArg(args, "--cdp") || process.env.API_DRAG_CDP_ENDPOINT || "http://127.0.0.1:9222";
      const targetUrl = getArg(args, "--url") || ZENMUX_LOGS_URL;
      const browserProfile = getArg(args, "--browser-profile") || process.env.CLI2ANYTHING_BROWSER_PROFILE || "existing";
      if (browserBridge === "cdp") {
        await ensureCdpBrowser({
          cdpEndpoint,
          url: targetUrl,
          userDataDir: resolve(`${outDir}/.chrome-profile`),
          profileMode: browserProfile,
          restartExisting: args.includes("--restart-existing-browser"),
          autoLaunch: !args.includes("--no-launch-browser")
        });
      }
      await startSwaggerServer({
        serverPath,
        port,
        cdpEndpoint,
        targetUrlIncludes: getArg(args, "--target-url-includes") || "zenmux.ai",
        url: targetUrl,
        browserBridge,
        browserProfile,
        restartExisting: args.includes("--restart-existing-browser")
      });
      const swaggerUrl = `http://127.0.0.1:${port}/`;
      await openPath(swaggerUrl);
      if (browserBridge === "extension") {
        await openPath(extensionDir);
        await openPath("chrome://extensions");
      }
      console.log(`swagger ${swaggerUrl}`);
      if (browserBridge === "extension") {
        console.log(`extension ${extensionDisplayDir}`);
      }
    } else {
      console.log(`swagger ${swaggerPath}`);
      console.log(`extension ${extensionDisplayDir}`);
    }
  }

  if (outputMode === "cli") {
    await writeCliPackage(outDir, apiPackage.manifest);
    if (!args.includes("--no-link")) await runCommand("npm", ["link"], { cwd: resolve(outDir) });
    if (!args.includes("--no-open")) await openPath(outDir);
    console.log(`cli cli-${slugify(host)}`);
  }

  console.log(`generated ${outDir}`);
  console.log(`primary endpoints: ${apiPackage.manifest.primaryEndpoints.length}`);
  console.log(`dependency endpoints: ${apiPackage.manifest.dependencyEndpoints.length}`);
}

async function discoverZenmux(args) {
  const out = getArg(args, "--out") || "artifacts/zenmux-discovered.json";
  const filterKeyword = normalizeOptionalKeyword(getArg(args, "--filter-keyword"));
  const depth = parseDepth(getArg(args, "--depth") ?? "0");
  const discovered = await discoverZenmuxData({ filterKeyword, depth, forceAllRoutes: !filterKeyword || args.includes("--depth") });
  await writeJson(out, discovered);
  console.log(`wrote ${out}`);
}

async function discoverZenmuxData(options = {}) {
  const html = await fetchText(ZENMUX_HOME);
  const routeMap = parseRouteMap(html);
  const routeNames = selectZenmuxRoutes(routeMap, options);
  const chunkFiles = new Set();

  for (const route of routeNames) {
    for (const index of routeMap.r[route] || []) {
      const file = routeMap.f[index]?.[0];
      if (file?.endsWith(".js")) chunkFiles.add(file);
    }
  }

  const chunks = [];
  for (const file of chunkFiles) {
    const url = CDN_BASE + file;
    const text = await fetchText(url);
    chunks.push({
      file,
      url,
      endpoints: extractEndpoints(text),
      evidence: extractEvidence(text)
    });
  }

  const discovered = {
    target: "zenmux.ai",
    discoveredAt: new Date().toISOString(),
    filterKeyword: normalizeOptionalKeyword(options.filterKeyword),
    depth: options.depth ?? 0,
    routeCount: routeNames.length,
    routes: Object.fromEntries(routeNames.map((route) => [route, routeMap.r[route] || []])),
    chunks,
    normalizedEndpoints: normalizeDiscoveredEndpoints(chunks)
  };

  return discovered;
}

async function generateZenmux(args) {
  const out = getArg(args, "--out") || "openapi/zenmux.openapi.json";
  await writeJson(out, createZenmuxOpenapi());
  console.log(`wrote ${out}`);
}

async function listLogs(args) {
  const days = Number(getArg(args, "--days") || "7");
  const now = Date.now();
  const startTime = now - days * 24 * 60 * 60 * 1000;
  const pageNo = Number(getArg(args, "--page") || "1");
  const pageSize = Number(getArg(args, "--page-size") || "20");
  const client = new ZenMuxClient();
  const data = await client.listLogs({ startTime, stopTime: now, pageNo, pageSize });
  console.log(JSON.stringify(data, null, 2));
}

async function logDetail(args) {
  const requestId = args.find((arg) => !arg.startsWith("--"));
  if (!requestId) throw new Error("logs:detail requires <requestId>");
  const includePayloads = !args.includes("--no-payloads");
  const client = new ZenMuxClient();
  const data = await client.getLogDetail(requestId, { includePayloads });
  console.log(JSON.stringify(data, null, 2));
}

async function browserCaptureZenmux(args) {
  const out = getArg(args, "--out") || "artifacts/zenmux-browser-capture.json";
  const url = getArg(args, "--url") || ZENMUX_LOGS_URL;
  const seconds = Number(getArg(args, "--seconds") || "20");
  const includeBodies = args.includes("--include-bodies");
  const urlIncludes = getArg(args, "--url-includes") || "/api/";
  const session = await connectZenmuxBrowser(args, { url });

  try {
    const capture = await session.captureNetwork({
      seconds,
      includeBodies,
      urlIncludes,
      onReady: args.includes("--no-navigate") ? undefined : () => session.navigate(url)
    });
    await writeJson(out, capture);
    console.log(`wrote ${out}`);
  } finally {
    session.close();
  }
}

async function browserListLogs(args) {
  const days = Number(getArg(args, "--days") || "7");
  const now = Date.now();
  const startTime = now - days * 24 * 60 * 60 * 1000;
  const pageNo = Number(getArg(args, "--page") || "1");
  const pageSize = Number(getArg(args, "--page-size") || "20");
  const session = await connectZenmuxBrowser(args, { url: getArg(args, "--url") || ZENMUX_LOGS_URL });

  try {
    const client = new ZenMuxBrowserClient(session);
    const data = await client.listLogs({ startTime, stopTime: now, pageNo, pageSize });
    console.log(JSON.stringify(data, null, 2));
  } finally {
    session.close();
  }
}

async function browserLogDetail(args) {
  const requestId = args.find((arg) => !arg.startsWith("--"));
  if (!requestId) throw new Error("browser:logs:detail requires <requestId>");
  const includePayloads = !args.includes("--no-payloads");
  const session = await connectZenmuxBrowser(args, { url: getArg(args, "--url") || ZENMUX_LOGS_URL });

  try {
    const client = new ZenMuxBrowserClient(session);
    const data = await client.getLogDetail(requestId, { includePayloads });
    console.log(JSON.stringify(data, null, 2));
  } finally {
    session.close();
  }
}

async function connectZenmuxBrowser(args, options = {}) {
  return BrowserPageSession.connect({
    cdpEndpoint: getArg(args, "--cdp") || process.env.API_DRAG_CDP_ENDPOINT || "http://127.0.0.1:9222",
    url: options.url || ZENMUX_LOGS_URL,
    targetUrlIncludes: getArg(args, "--target-url-includes") || "zenmux.ai",
    apiVersion: getArg(args, "--api-version") || process.env.ZENMUX_API_VERSION,
    xsrfCookieName: getArg(args, "--xsrf-cookie") || "XSRF-TOKEN",
    xsrfHeaderName: getArg(args, "--xsrf-header") || "X-XSRF-TOKEN"
  });
}

function parseRouteMap(html) {
  const match = html.match(/<script type="umi-route-chunk-files-map">([\s\S]*?)<\/script>/);
  if (!match) throw new Error("ZenMux route chunk map not found");
  return JSON.parse(match[1]);
}

function selectZenmuxRoutes(routeMap, { filterKeyword, depth = 0, forceAllRoutes = false } = {}) {
  const routes = Object.keys(routeMap.r || {}).sort();
  const keyword = normalizeOptionalKeyword(filterKeyword);
  if (!routes.length) return [];
  if (!keyword || forceAllRoutes) return routes.filter((route) => depth === 0 || routeDepth(route) <= depth);

  if (isLogKeyword(keyword)) {
    const logRoutes = ["/platform/logs", "/platform/logs/detail/:id"].filter((route) => routeMap.r?.[route]);
    if (logRoutes.length) return logRoutes;
  }

  return routes.filter((route) => route.toLowerCase().includes(keyword.toLowerCase()));
}

function routeDepth(route) {
  return String(route || "")
    .split(/[/?#]/)[0]
    .split("/")
    .filter(Boolean).length;
}

function extractEndpoints(text) {
  const endpoints = new Set();
  const requestPattern = /request\)?\(\s*(["`])([^"`]+)\1\s*,\s*\{method:\s*(["`])([A-Z]+)\3/g;
  let match;
  while ((match = requestPattern.exec(text))) {
    endpoints.add(`${match[4]} ${normalizePath(match[2])}`);
  }

  const fetchTemplatePattern = /fetch\(`([^`]+)`\)/g;
  while ((match = fetchTemplatePattern.exec(text))) {
    if (match[1].includes("/api/")) {
      endpoints.add(`GET ${normalizePath(match[1])}`);
    }
  }

  return [...endpoints].sort();
}

function extractEvidence(text) {
  const needles = [
    "api/api_key/activity",
    "api/api_key/activity/",
    "api/v1/generation",
    "/api/v1/generation/request",
    "/api/v1/generation/response",
    "userRequest",
    "providerRequest",
    "userResponse",
    "providerResponse"
  ];

  return needles
    .map((needle) => {
      const index = text.indexOf(needle);
      if (index === -1) return null;
      return {
        needle,
        snippet: text.slice(Math.max(0, index - 220), Math.min(text.length, index + 320)).replace(/\s+/g, " ")
      };
    })
    .filter(Boolean);
}

function createZenmuxFilteredPackage({ target, filterKeyword, discovery, depth = 0 }) {
  const semanticKeyword = normalizeOptionalKeyword(filterKeyword);
  const scope = semanticKeyword ? "filtered" : "all";
  const scopeLabel = semanticKeyword || "all";
  const endpointCatalog = [
    {
      endpoint: "POST /api/api_key/activity",
      role: "primary:list",
      capability: "log.list",
      reason: "Query the Logs table by time, API key, request id, model, provider, and finish reason."
    },
    {
      endpoint: "GET /api/api_key/activity/{id}",
      role: "primary:activity-detail",
      capability: "log.activityDetail",
      reason: "Fetch dashboard activity detail for one request id."
    },
    {
      endpoint: "GET /api/v1/generation",
      canonicalEndpoint: "GET /api/v1/management/generation",
      role: "dependency:generation-metadata",
      capability: "log.detail.generation",
      reason: "Fetch generation usage, latency, billing, native token, and rating metadata. OpenAPI prefers the documented management URL and keeps this observed URL as fallback."
    },
    {
      endpoint: "GET /api/v1/generation/request?id={value}&type={value}",
      role: "dependency:raw-request-payload",
      capability: "log.detail.requestPayload",
      reason: "Fetch user/provider request payloads for text, image, file, tool-call, and provider-native inputs."
    },
    {
      endpoint: "GET /api/v1/generation/response?id={value}&type={value}",
      role: "dependency:raw-response-payload",
      capability: "log.detail.responsePayload",
      reason: "Fetch user/provider response payloads, including streamed or provider-native result shapes."
    },
    {
      endpoint: "GET /api/api_key/list",
      role: "dependency:list-filter",
      capability: "log.filters.apiKeys",
      reason: "Populate API key filter options used by the Logs UI."
    },
    {
      endpoint: "GET /api/api_key/list_all",
      role: "dependency:list-filter",
      capability: "log.filters.apiKeysAll",
      reason: "Populate API key selector data used by Logs and adjacent dashboard controls."
    },
    {
      endpoint: "GET /api/api_key/finish_reasons",
      role: "dependency:list-filter",
      capability: "log.filters.finishReasons",
      reason: "Populate finish reason filter options used by the Logs UI."
    }
  ];

  const discoveredEndpoints = new Set(discovery.normalizedEndpoints || []);
  const selected = selectEndpointsForScope({ endpointCatalog, discoveredEndpoints, filterKeyword: semanticKeyword });
  const primaryEndpoints = selected.filter((item) => !item.role.startsWith("dependency:"));
  const dependencyEndpoints = selected.filter((item) => item.role.startsWith("dependency:"));
  const selectedEndpointSet = new Set(selected.flatMap((item) => [item.endpoint, item.canonicalEndpoint].filter(Boolean)));
  const filteredChunks = (discovery.chunks || [])
    .map((chunk) => ({
      ...chunk,
      endpoints: scope === "all"
        ? [...(chunk.endpoints || [])]
        : (chunk.endpoints || []).filter((endpoint) => selectedEndpointSet.has(endpoint)),
      evidence: filterEvidenceForScope(chunk.evidence || [], semanticKeyword)
    }))
    .filter((chunk) => chunk.endpoints.length || chunk.evidence.length);

  const filteredDiscovery = {
    target,
    scope,
    filterKeyword: semanticKeyword,
    depth,
    generatedAt: new Date().toISOString(),
    strategy: scope === "all"
      ? "all discovered frontend routes + static endpoint extraction"
      : isLogKeyword(semanticKeyword)
        ? "semantic route filter + dependency closure"
        : "keyword endpoint filter",
    sourceRoutes: discovery.routes,
    chunks: filteredChunks,
    selectedEndpoints: selected,
    normalizedEndpoints: [...selectedEndpointSet]
  };

  return {
    manifest: {
      name: `${target}:${scopeLabel}`,
      target,
      scope,
      filterKeyword: scopeLabel,
      requestedFilterKeyword: semanticKeyword,
      depth,
      generatedAt: filteredDiscovery.generatedAt,
      strategy: filteredDiscovery.strategy,
      outputs: {
        openapi: "openapi.json",
        apiGraph: "api-graph.json",
        discovery: "discovery.filtered.json",
        sdk: "sdk/index.mjs"
      },
      transportModes: [
        "browser-session: same-origin fetch inside the user's logged-in browser via CDP; no manual cookie/API key input",
        "direct-http: explicit API key/session headers for automation environments"
      ],
      primaryRoutes: Object.keys(discovery.routes || {}),
      primaryEndpoints,
      dependencyEndpoints,
      capabilities: selected.map(({ capability, includedEndpoint, role, reason, observed }) => ({
        capability,
        endpoint: includedEndpoint,
        role,
        observed,
        reason
      }))
    },
    filteredDiscovery
  };
}

function createZenmuxOpenapiForPackage({ apiPackage }) {
  const openapi = createZenmuxOpenapi();
  const selected = apiPackage.filteredDiscovery.selectedEndpoints || [];
  const genericOperations = [];

  openapi.components ||= {};
  openapi.components.schemas ||= {};
  openapi.components.schemas.AnyJson = {
    description: "Generic JSON placeholder for endpoints discovered from frontend bundles before response samples are promoted into typed schemas.",
    oneOf: [
      { type: "object", additionalProperties: true },
      { type: "array", items: true },
      { type: "string" },
      { type: "number" },
      { type: "integer" },
      { type: "boolean" },
      { type: "null" }
    ]
  };

  for (const item of selected) {
    const parsed = parseEndpointSignature(item.includedEndpoint || item.endpoint);
    if (!parsed) continue;
    const methodKey = parsed.method.toLowerCase();
    if (hasOpenapiOperation(openapi, parsed.path, methodKey)) continue;
    openapi.paths[parsed.path] ||= {};
    openapi.paths[parsed.path][methodKey] = createGenericOpenapiOperation({ item, parsed });
    genericOperations.push(`${parsed.method} ${parsed.path}`);
  }

  if (genericOperations.length) {
    const tags = new Set((openapi.tags || []).map((tag) => tag.name));
    if (!tags.has("Discovered")) openapi.tags = [...(openapi.tags || []), { name: "Discovered" }];
    openapi.info = {
      ...openapi.info,
      title: apiPackage.manifest.scope === "all" ? "ZenMux Discovered API" : openapi.info.title,
      description: `${openapi.info.description}\n\ncli2anything++ also included ${genericOperations.length} generic discovered operation(s) from frontend bundle analysis.`
    };
  }

  return openapi;
}

function hasOpenapiOperation(openapi, path, methodKey) {
  if (openapi.paths[path]?.[methodKey]) return true;
  const normalizedPath = normalizeTemplatePath(path);
  return Object.entries(openapi.paths || {}).some(([candidate, pathItem]) => {
    return normalizeTemplatePath(candidate) === normalizedPath && Boolean(pathItem?.[methodKey]);
  });
}

function normalizeTemplatePath(path) {
  return String(path || "").replace(/\{[^}]+\}/g, "{}");
}

function parseEndpointSignature(endpoint) {
  const match = String(endpoint || "").trim().match(/^([A-Z]+)\s+(.+)$/);
  if (!match) return null;
  const [, method, rawTarget] = match;
  const [rawPath, rawQuery = ""] = rawTarget.split("?");
  const path = normalizeOpenapiPath(rawPath);
  const query = parseEndpointQuery(rawQuery);
  return { method, path, query };
}

function normalizeOpenapiPath(path) {
  return String(path || "/")
    .replace(/^\/?/, "/")
    .replace(/\/+$/, "") || "/";
}

function parseEndpointQuery(query) {
  if (!query) return [];
  return query
    .split("&")
    .map((part) => part.split("=")[0])
    .map((name) => decodeURIComponent(name || "").trim())
    .filter(Boolean)
    .filter((name, index, names) => names.indexOf(name) === index);
}

function createGenericOpenapiOperation({ item, parsed }) {
  const parameters = [
    { $ref: "#/components/parameters/ApiVersionHeader" },
    ...extractPathParams(parsed.path),
    ...parsed.query.map((name) => ({
      name,
      in: "query",
      required: false,
      schema: { type: "string", default: genericParamDefault(name) },
      example: genericParamDefault(name)
    }))
  ];
  const operation = {
    tags: ["Discovered"],
    operationId: createOperationId(parsed.method, parsed.path),
    summary: `${parsed.method} ${parsed.path}`,
    description: `${item.reason || "Discovered from ZenMux frontend route bundles."} This generic operation is intentionally broad until concrete samples are captured.`,
    security: [
      { consoleCookie: [], csrfToken: [] },
      { bearerAuth: [], csrfToken: [] }
    ],
    parameters,
    responses: {
      "200": {
        description: "Discovered endpoint response",
        content: {
          "application/json": {
            schema: { $ref: "#/components/schemas/AnyJson" }
          }
        }
      },
      default: { $ref: "#/components/responses/Error" }
    }
  };

  if (!["GET", "HEAD"].includes(parsed.method)) {
    operation.requestBody = {
      required: false,
      content: {
        "application/json": {
          schema: { $ref: "#/components/schemas/AnyJson" },
          example: {}
        }
      }
    };
  }

  return operation;
}

function extractPathParams(path) {
  const params = new Set();
  for (const match of String(path).matchAll(/\{([^}]+)\}/g)) params.add(match[1]);
  return [...params].map((name) => ({
    name,
    in: "path",
    required: true,
    schema: { type: "string", default: genericParamDefault(name) },
    example: genericParamDefault(name)
  }));
}

function genericParamDefault(name) {
  if (String(name).toLowerCase().includes("id")) return "paste-id";
  if (String(name).toLowerCase() === "type") return "value";
  return "value";
}

function createOperationId(method, path) {
  const parts = String(path)
    .replace(/[{}]/g, "")
    .split("/")
    .filter(Boolean)
    .map((part) => part.replace(/[^a-zA-Z0-9]+/g, " "))
    .join(" ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace(/\s+/g, "");
  return `${method.toLowerCase()}${parts || "Root"}`;
}

function selectEndpointsForScope({ endpointCatalog, discoveredEndpoints, filterKeyword }) {
  if (!filterKeyword) {
    return [...discoveredEndpoints].sort().map((endpoint) => createDiscoveredEndpoint(endpoint, "all"));
  }

  if (isLogKeyword(filterKeyword)) {
    return endpointCatalog.map((item) => ({
      ...item,
      observed: discoveredEndpoints.has(item.endpoint),
      includedEndpoint: item.canonicalEndpoint || item.endpoint
    }));
  }

  const lowerKeyword = filterKeyword.toLowerCase();
  return [...discoveredEndpoints]
    .filter((endpoint) => endpoint.toLowerCase().includes(lowerKeyword))
    .sort()
    .map((endpoint) => createDiscoveredEndpoint(endpoint, filterKeyword));
}

function createDiscoveredEndpoint(endpoint, scopeLabel) {
  const method = endpoint.split(/\s+/, 1)[0] || "GET";
  const path = endpoint.slice(method.length).trim();
  return {
    endpoint,
    role: `discovered:${method.toLowerCase()}`,
    capability: endpointCapability(endpoint),
    reason: scopeLabel === "all"
      ? "Discovered from ZenMux frontend route bundles."
      : `Discovered from ZenMux frontend route bundles while filtering for ${scopeLabel}.`,
    observed: true,
    includedEndpoint: endpoint,
    method,
    path
  };
}

function endpointCapability(endpoint) {
  const [method, ...pathParts] = String(endpoint).split(/\s+/);
  return `${String(method || "GET").toLowerCase()}.${pathParts.join(" ").replace(/\?.*$/, "").replace(/^\/+/, "").replace(/[{}]/g, "").replace(/[^a-zA-Z0-9]+/g, ".").replace(/^\.+|\.+$/g, "") || "endpoint"}`;
}

function filterEvidenceForScope(evidence, filterKeyword) {
  if (!filterKeyword) return [...evidence];
  if (isLogKeyword(filterKeyword)) return evidence.filter((item) => isLogEvidence(item));
  const lowerKeyword = filterKeyword.toLowerCase();
  return evidence.filter((item) => `${item?.needle || ""} ${item?.snippet || ""}`.toLowerCase().includes(lowerKeyword));
}

function isLogEvidence(evidence) {
  const text = `${evidence?.needle || ""} ${evidence?.snippet || ""}`.toLowerCase();
  return [
    "activity",
    "generation",
    "request",
    "response",
    "userrequest",
    "providerrequest",
    "userresponse",
    "providerresponse",
    "finish_reasons",
    "api_key/list"
  ].some((needle) => text.includes(needle));
}

async function writeSdkBundle(outDir) {
  const files = [
    "zenmux-client.mjs",
    "zenmux-client.d.ts",
    "zenmux-browser-client.mjs",
    "zenmux-browser-client.d.ts",
    "browser-cdp.mjs",
    "extension-bridge.mjs",
    "json-shape.mjs"
  ];
  for (const file of files) {
    const text = await readFile(new URL(`../src/${file}`, import.meta.url), "utf8");
    await writeText(`${outDir}/${file}`, text);
  }

  await writeText(`${outDir}/index.mjs`, [
    'export { ZenMuxClient, ZenMuxApiError } from "./zenmux-client.mjs";',
    'export { ZenMuxBrowserClient } from "./zenmux-browser-client.mjs";',
    'export { BrowserPageSession, CdpConnection, CdpError } from "./browser-cdp.mjs";',
    'export { ExtensionBridgeSession, ExtensionBridgeError } from "./extension-bridge.mjs";',
    ""
  ].join("\n"));
}

function createGeneratedReadme(manifest) {
  return `# cli2anything++ Generated SDK

Target: ${manifest.target}
Scope: ${manifest.scope}
Filter keyword: ${manifest.requestedFilterKeyword || "(none)"}
Discovery depth: ${manifest.depth === 0 ? "unlimited" : manifest.depth}

## Included APIs

Primary:
${manifest.primaryEndpoints.map((item) => `- ${item.includedEndpoint}: ${item.reason}`).join("\n")}

Dependencies:
${manifest.dependencyEndpoints.map((item) => `- ${item.includedEndpoint}: ${item.reason}`).join("\n")}

## Browser-session usage

\`\`\`bash
open -na "Google Chrome" --args \\
  --remote-debugging-port=9222 \\
  --user-data-dir="$PWD/.chrome-profile" \\
  https://zenmux.ai/platform/logs

node ../../bin/cli2anything.mjs browser:logs:list --cdp http://127.0.0.1:9222 --days 1
node ../../bin/cli2anything.mjs browser:logs:detail <requestId> --cdp http://127.0.0.1:9222
\`\`\`

## SDK usage

\`\`\`js
import { BrowserPageSession, ZenMuxBrowserClient } from "./sdk/index.mjs";

const session = await BrowserPageSession.connect({
  cdpEndpoint: "http://127.0.0.1:9222",
  url: "https://zenmux.ai/platform/logs",
  targetUrlIncludes: "zenmux.ai"
});

const client = new ZenMuxBrowserClient(session);
const logs = await client.listLogs({ pageNo: 1, pageSize: 20 });
const detail = await client.getLogDetail(logs.data?.[0]?.requestId);
session.close();
\`\`\`
`;
}

function createSwaggerHtml({ manifest, openapi, extensionDir }) {
  const swaggerSpec = createBrowserSessionSwaggerSpec(openapi);
  const extensionHelp = `Load or reload ${extensionDir} in chrome://extensions, then open ${manifest.target}.`;
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(manifest.target)} ${escapeHtml(manifest.filterKeyword)} API</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; background: #ffffff; }
      .topbar { display: none; }
      #banner { padding: 12px 24px; border-bottom: 1px solid #e6e6e6; font: 14px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      #banner strong { margin-right: 12px; }
      #banner code { background: #f6f6f6; padding: 2px 5px; border-radius: 4px; }
      #bridge-status { display: inline-block; margin-left: 12px; padding: 2px 7px; border-radius: 999px; background: #fff4d6; color: #7a4b00; }
      #bridge-status.connected { background: #e6f8ed; color: #106b35; }
      #bridge-help { margin-left: 8px; color: #666; }
      .nav-link { margin-left: 12px; padding: 3px 8px; border: 1px solid #d8dde5; border-radius: 999px; color: #1d2430; text-decoration: none; }
      .nav-link:hover { border-color: #9aa5b5; }
    </style>
  </head>
  <body>
    <div id="banner"><strong>cli2anything++</strong> ${escapeHtml(manifest.target)} / ${escapeHtml(manifest.filterKeyword)} - browser-session proxy enabled; no manual Cookie/API key input.<a class="nav-link" href="/drilldown">Drilldown</a><span id="bridge-status">Checking bridge...</span><span id="bridge-help"></span></div>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      const spec = ${JSON.stringify(swaggerSpec)};
      const extensionHelp = ${JSON.stringify(extensionHelp)};
      window.addEventListener("load", () => {
        monitorBridge();
        SwaggerUIBundle({
          spec,
          dom_id: "#swagger-ui",
          deepLinking: true,
          requestInterceptor: (request) => {
            if (!request.url || request.url.startsWith("/__cap/")) return request;
            const targetUrl = new URL(request.url, spec.servers?.[0]?.url || "https://${manifest.target}").toString();
            const originalMethod = request.method || "GET";
            const originalHeaders = request.headers || {};
            const originalBody = request.body;
            request.url = "/__cap/proxy";
            request.method = "POST";
            request.headers = { "Content-Type": "application/json" };
            request.body = JSON.stringify({
              url: targetUrl,
              method: originalMethod,
              headers: originalHeaders,
              body: originalBody
            });
            return request;
          },
          presets: [SwaggerUIBundle.presets.apis],
          layout: "BaseLayout"
        });
      });

      async function monitorBridge() {
        const status = document.getElementById("bridge-status");
        const help = document.getElementById("bridge-help");
        while (true) {
          try {
            const response = await fetch("/__cap/health", { cache: "no-store" });
            const health = await response.json();
            if (health.bridge === "extension" && health.extensionConnected && health.extensionCurrent !== false) {
              status.textContent = "Extension connected";
              status.className = "connected";
              help.textContent = "";
            } else if (health.bridge === "extension" && health.extensionConnected && health.extensionVersion && health.extensionVersion !== health.expectedExtensionVersion) {
              status.textContent = "Extension reload needed";
              status.className = "";
              help.textContent = extensionHelp;
            } else if (health.bridge === "extension" && health.extensionConnected) {
              status.textContent = "Extension job channel reconnecting";
              status.className = "";
              help.textContent = "Wait a few seconds, or reload the extension if this does not clear.";
            } else if (health.bridge === "extension") {
              status.textContent = "Extension not connected";
              status.className = "";
              help.textContent = extensionHelp;
            } else {
              status.textContent = "CDP bridge";
              status.className = health.ok ? "connected" : "";
              help.textContent = "";
            }
          } catch {
            status.textContent = "Proxy offline";
            status.className = "";
            help.textContent = "Restart cli2anything --output swagger.";
          }
          await new Promise((resolve) => setTimeout(resolve, 2000));
        }
      }
    </script>
  </body>
</html>
`;
}

function createBrowserSessionSwaggerSpec(openapi) {
  const spec = structuredClone(openapi);
  spec.info = {
    ...spec.info,
    title: `${spec.info.title} (Browser Session)`,
    description: `${spec.info.description}\n\nThis Swagger UI is configured for cli2anything++ browser-session mode. Try-it-out requests are sent to a local proxy, which executes same-origin fetch calls inside the user's logged-in browser through the cli2anything++ browser bridge. No Cookie/API key needs to be pasted into Swagger UI.`
  };
  delete spec.security;
  if (spec.components) delete spec.components.securitySchemes;
  for (const pathItem of Object.values(spec.paths || {})) {
    for (const operation of Object.values(pathItem || {})) {
      if (operation && typeof operation === "object") delete operation.security;
    }
  }
  return spec;
}

function createSwaggerServer({ extensionDir, targetHost }) {
  return `#!/usr/bin/env node
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { mkdir, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { BrowserPageSession } from "../sdk/browser-cdp.mjs";

const DIR = dirname(fileURLToPath(import.meta.url));
const PACKAGE_DIR = resolve(DIR, "..");
const SOURCE_PACKAGE_DIR = ${JSON.stringify(resolve(dirname(fileURLToPath(import.meta.url)), ".."))};
const SOURCE_REQUIRE = createRequire(resolve(SOURCE_PACKAGE_DIR, "package.json"));
const PORT = Number(getArg(process.argv.slice(2), "--port") || "47831");
const CDP = getArg(process.argv.slice(2), "--cdp") || "http://127.0.0.1:9222";
const TARGET_URL_INCLUDES = getArg(process.argv.slice(2), "--target-url-includes") || "zenmux.ai";
const TARGET_URL = getArg(process.argv.slice(2), "--url") || "https://zenmux.ai/platform/logs";
const BROWSER_BRIDGE = getArg(process.argv.slice(2), "--browser-bridge") || "extension";
const BROWSER_PROFILE = getArg(process.argv.slice(2), "--browser-profile") || "existing";
const EXTENSION_DIR = ${JSON.stringify(extensionDir)};
const TARGET_LABEL = ${JSON.stringify(targetHost)};
const EXPECTED_EXTENSION_VERSION = ${JSON.stringify(EXTENSION_BRIDGE_VERSION)};
const RESTART_EXISTING = process.argv.includes("--restart-existing-browser");
const AUTO_LAUNCH = !process.argv.includes("--no-launch-browser");

let sessionPromise;
const extensionJobs = [];
const extensionPolls = [];
const extensionWaiters = new Map();
let extensionLastSeen = null;
let extensionLastPollSeen = null;
let extensionVersion = null;

const server = createServer(async (req, res) => {
  try {
    if (req.method === "OPTIONS" && req.url.startsWith("/__cap/extension/")) {
      return send(res, 204, "text/plain", "", corsHeaders());
    }

    if (req.method === "GET" && (req.url === "/" || req.url === "/index.html")) {
      const html = await readFile(resolve(DIR, "index.html"), "utf8");
      return send(res, 200, "text/html; charset=utf-8", html);
    }

    if (req.method === "GET" && (req.url === "/drilldown" || req.url === "/drilldown.html")) {
      const html = await readFile(resolve(DIR, "drilldown.html"), "utf8");
      return send(res, 200, "text/html; charset=utf-8", html);
    }

    if (req.method === "GET" && req.url === "/api-graph.json") {
      const graph = await readFile(resolve(PACKAGE_DIR, "api-graph.json"), "utf8");
      return send(res, 200, "application/json; charset=utf-8", graph);
    }

    if (req.method === "GET" && req.url === "/openapi.json") {
      const openapi = await readFile(resolve(PACKAGE_DIR, "openapi.json"), "utf8");
      return send(res, 200, "application/json; charset=utf-8", openapi);
    }

    if (req.method === "GET" && req.url === "/__cap/health") {
      return sendJson(res, 200, {
        ok: true,
        bridge: BROWSER_BRIDGE,
        cdpEndpoint: CDP,
        targetUrlIncludes: TARGET_URL_INCLUDES,
        extensionConnected: Boolean(extensionLastSeen && Date.now() - extensionLastSeen < 45_000),
        extensionPolling: Boolean(extensionLastPollSeen && Date.now() - extensionLastPollSeen < 45_000),
        extensionLastSeen,
        extensionLastPollSeen,
        expectedExtensionVersion: EXPECTED_EXTENSION_VERSION,
        extensionVersion,
        extensionCurrent: Boolean(extensionLastSeen && Date.now() - extensionLastSeen < 45_000 && extensionLastPollSeen && Date.now() - extensionLastPollSeen < 45_000 && extensionVersion === EXPECTED_EXTENSION_VERSION)
      });
    }

    if (req.method === "POST" && req.url === "/__cap/ai/plan") {
      const payload = JSON.parse(await readBody(req));
      const plan = await createAiPlan(payload);
      return sendJson(res, 200, plan);
    }

    if (req.method === "GET" && req.url.startsWith("/__cap/extension/hello")) {
      recordExtensionSeen(req);
      return sendJson(res, 200, { ok: true, bridge: "extension" }, corsHeaders());
    }

    if (req.method === "GET" && req.url.startsWith("/__cap/extension/poll")) {
      recordExtensionSeen(req);
      extensionLastPollSeen = Date.now();
      return waitForExtensionJob(req, res);
    }

    if (req.method === "POST" && req.url.startsWith("/__cap/extension/result")) {
      recordExtensionSeen(req);
      const result = JSON.parse(await readBody(req));
      const waiter = extensionWaiters.get(result.id);
      if (waiter) {
        clearTimeout(waiter.timeout);
        extensionWaiters.delete(result.id);
        waiter.resolve(result);
      }
      return sendJson(res, 200, { ok: true }, corsHeaders());
    }

    if (req.method === "POST" && req.url === "/__cap/proxy") {
      const payload = JSON.parse(await readBody(req));
      const result = BROWSER_BRIDGE === "cdp"
        ? await proxyViaCdp(payload)
        : await proxyViaExtension(payload);

      if (typeof result.body === "string") {
        return send(res, result.status, result.contentType || "text/plain; charset=utf-8", result.body);
      }
      return sendJson(res, result.status, result.body);
    }

    sendJson(res, 404, { message: "not found" });
  } catch (error) {
    sendJson(res, 502, {
      message: error?.message || String(error),
      hint: BROWSER_BRIDGE === "extension"
        ? \`Load the generated cli2anything++ extension in your existing Chrome, open/log in to \${TARGET_LABEL}, then retry Swagger.\`
        : \`Start Chrome with --remote-debugging-port=9222 and log in to \${TARGET_LABEL}, then refresh this Swagger page.\`
    });
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(\`cli2anything++ Swagger proxy listening on http://127.0.0.1:\${PORT}\`);
});

process.on("SIGTERM", async () => {
  try {
    const session = await sessionPromise;
    session?.close?.();
  } catch {}
  server.close(() => process.exit(0));
});

async function createAiPlan(payload) {
  const prompt = String(payload?.prompt || "").trim();
  if (!prompt) {
    return {
      type: "unsupported",
      title: "No prompt",
      reason: "Enter a natural-language request for the AI sidebar.",
      engine: "deterministic-fallback"
    };
  }
  const context = await loadAiContext();
  const fallback = fallbackAiPlan(prompt, context);
  try {
    const aiPlan = await planWithVercelAi(prompt, payload, context);
    return normalizeAiPlan(aiPlan, fallback, "vercel-ai-sdk");
  } catch (error) {
    return {
      ...fallback,
      engine: "deterministic-fallback",
      aiUnavailable: error?.message || String(error)
    };
  }
}

async function loadAiContext() {
  const [graphRaw, openapiRaw] = await Promise.all([
    readFile(resolve(PACKAGE_DIR, "api-graph.json"), "utf8"),
    readFile(resolve(PACKAGE_DIR, "openapi.json"), "utf8")
  ]);
  const graph = JSON.parse(graphRaw);
  const openapi = JSON.parse(openapiRaw);
  const endpoints = (graph.nodes || []).map((node) => ({
    id: node.id,
    method: node.method,
    path: node.path,
    label: node.label,
    group: node.group,
    role: node.role,
    operationId: node.operationId
  }));
  const edges = (graph.edges || []).filter((edge) => edge.relation !== "namespace").map((edge) => ({
    from: edge.from,
    to: edge.to,
    relation: edge.relation,
    sourceSelector: edge.sourceSelector,
    parameterMap: edge.parameterMap
  }));
  return {
    target: TARGET_LABEL,
    scope: graph.scope,
    endpoints,
    edges,
    openapiPaths: Object.keys(openapi.paths || {})
  };
}

async function planWithVercelAi(prompt, payload, context) {
  if (!process.env.OPENAI_API_KEY && !process.env.AI_GATEWAY_API_KEY) {
    throw new Error("Set OPENAI_API_KEY or AI_GATEWAY_API_KEY to enable the Vercel AI SDK planner.");
  }
  const [{ generateText, Output }, { openai }, { z }] = await Promise.all([
    importAiPackage("ai"),
    importAiPackage("@ai-sdk/openai"),
    importAiPackage("zod")
  ]);
  const schema = z.object({
    type: z.enum(["zenmux_recent_image_results", "unsupported"]),
    title: z.string().optional(),
    limit: z.number().int().min(1).max(10).optional(),
    scanLimit: z.number().int().min(1).max(500).optional(),
    filters: z.object({
      modelSlugs: z.array(z.string()).optional(),
      providerSlugs: z.array(z.string()).optional(),
      finishReasons: z.array(z.string()).optional()
    }).optional(),
    reason: z.string().optional(),
    steps: z.array(z.object({
      label: z.string(),
      method: z.string().optional(),
      path: z.string().optional()
    })).optional()
  });
  const endpointLines = context.endpoints.slice(0, 160).map((endpoint) =>
    endpoint.id + " " + endpoint.method + " " + endpoint.path + " group=" + (endpoint.group || "/") + " label=" + endpoint.label
  ).join("\\n");
  const edgeLines = context.edges.slice(0, 160).map((edge) =>
    edge.from + " -> " + edge.to + " relation=" + edge.relation + " selector=" + (edge.sourceSelector || "")
  ).join("\\n");
  const modelName = process.env.CLI2ANYTHING_AI_MODEL || "gpt-4.1-mini";
  const result = await generateText({
    model: openai(modelName),
    system: "You plan safe API calls for a local browser-session API explorer. Return only executable plans from the schema. Prefer read-only or safe log exploration. For ZenMux image-result requests, use zenmux_recent_image_results with a small limit, a broad scanLimit, and log filters when the user names models/providers.",
    prompt:
      "Target: " + context.target + "\\n" +
      "Scope: " + (context.scope || "unknown") + "\\n" +
      "Selected request id: " + (payload?.selectedRequestId || "") + "\\n" +
      "User request: " + prompt + "\\n\\n" +
      "Available endpoints:\\n" + endpointLines + "\\n\\n" +
      "Known endpoint links:\\n" + edgeLines,
    output: Output.object({ schema })
  });
  return result.output;
}

async function importAiPackage(name) {
  try {
    return await import(name);
  } catch (firstError) {
    try {
      return await import(pathToFileURL(SOURCE_REQUIRE.resolve(name)).href);
    } catch {
      throw firstError;
    }
  }
}

function normalizeAiPlan(plan, fallback, engine) {
  if (!plan || typeof plan !== "object") return { ...fallback, engine: "deterministic-fallback" };
  if (plan.type === "zenmux_recent_image_results") {
    return {
      type: "zenmux_recent_image_results",
      title: plan.title || fallback.title || "Recent image results",
      limit: clampNumber(plan.limit || fallback.limit || 2, 1, 10),
      scanLimit: clampNumber(plan.scanLimit || fallback.scanLimit || 160, 1, 500),
      filters: {
        modelSlugs: normalizeStringArray(plan.filters?.modelSlugs || fallback.filters?.modelSlugs),
        providerSlugs: normalizeStringArray(plan.filters?.providerSlugs || fallback.filters?.providerSlugs),
        finishReasons: normalizeStringArray(plan.filters?.finishReasons || fallback.filters?.finishReasons)
      },
      steps: Array.isArray(plan.steps) ? plan.steps : fallback.steps,
      engine
    };
  }
  return {
    type: "unsupported",
    title: plan.title || fallback.title || "Unsupported request",
    reason: plan.reason || fallback.reason || "The planner could not map this request to safe API calls.",
    engine
  };
}

function fallbackAiPlan(prompt, context) {
  const text = String(prompt || "").toLowerCase();
  const asksImage = /\\b(image|images|picture|pictures|render|png|jpg|jpeg|webp|gif|dall|flux|stable-diffusion|imagen)\\b/i.test(text) ||
    containsAny(prompt, ["\\u56fe\\u7247", "\\u56fe\\u50cf", "\\u51fa\\u56fe", "\\u6e32\\u67d3"]);
  const asksRecent = /\\b(recent|latest|last|newest)\\b/i.test(text) ||
    containsAny(prompt, ["\\u6700\\u8fd1", "\\u6700\\u65b0", "\\u8fd1"]);
  const hasZenmuxLogEndpoints = context.endpoints.some((endpoint) => endpoint.path === "/api/api_key/activity") &&
    context.endpoints.some((endpoint) => endpoint.path === "/api/v1/generation/response");
  if (TARGET_LABEL === "zenmux.ai" && asksImage && (asksRecent || text.includes("two") || text.includes("2")) && hasZenmuxLogEndpoints) {
    const limit = inferRequestedCount(prompt, 2);
    return {
      type: "zenmux_recent_image_results",
      title: "Recent image results",
      limit,
      scanLimit: Math.max(160, limit * 80),
      filters: {
        modelSlugs: [],
        providerSlugs: [],
        finishReasons: []
      },
      steps: [
        { label: "List recent logs", method: "POST", path: "/api/api_key/activity" },
        { label: "Fetch each response payload", method: "GET", path: "/api/v1/generation/response" },
        { label: "Render detected image URLs or inline images" }
      ],
      engine: "deterministic-fallback"
    };
  }
  return {
    type: "unsupported",
    title: "Unsupported request",
    reason: "The current MVP can execute ZenMux recent image-result requests. Try asking for the latest two image generation results.",
    engine: "deterministic-fallback"
  };
}

function containsAny(value, needles) {
  const text = String(value || "");
  return needles.some((needle) => text.includes(needle));
}

function inferRequestedCount(prompt, fallback) {
  const text = String(prompt || "").toLowerCase();
  const match = text.match(/\\b(\\d{1,2})\\b/);
  if (match) return clampNumber(Number(match[1]), 1, 10);
  const zhCounts = [
    ["\\u4e00", 1],
    ["\\u4e8c", 2],
    ["\\u4e24", 2],
    ["\\u4e09", 3],
    ["\\u56db", 4],
    ["\\u4e94", 5]
  ];
  for (const [needle, count] of zhCounts) {
    if (text.includes(needle)) return count;
  }
  if (text.includes("one")) return 1;
  if (text.includes("two")) return 2;
  if (text.includes("three")) return 3;
  return fallback;
}

function clampNumber(value, min, max) {
  const number = Number(value);
  if (!Number.isFinite(number)) return min;
  return Math.max(min, Math.min(max, Math.round(number)));
}

function normalizeStringArray(value) {
  return (Array.isArray(value) ? value : value ? [value] : [])
    .map((item) => String(item || "").trim())
    .filter(Boolean);
}

function getSession() {
  sessionPromise ||= (async () => {
    await ensureCdpBrowser({
      cdpEndpoint: CDP,
      url: TARGET_URL,
      userDataDir: resolve(PACKAGE_DIR, ".chrome-profile"),
      profileMode: BROWSER_PROFILE,
      restartExisting: RESTART_EXISTING,
      autoLaunch: AUTO_LAUNCH
    });
    return BrowserPageSession.connect({
      cdpEndpoint: CDP,
      url: TARGET_URL,
      targetUrlIncludes: TARGET_URL_INCLUDES
    });
  })();
  return sessionPromise;
}

async function proxyViaCdp(payload) {
  const session = await getSession();
  return session.fetchJson(payload.url, {
    method: payload.method || "GET",
    headers: sanitizeHeaders(payload.headers || {}),
    body: normalizeBody(payload.body)
  });
}

async function proxyViaExtension(payload) {
  const id = \`job_\${Date.now()}_\${Math.random().toString(36).slice(2)}\`;
  const job = {
    id,
    url: payload.url,
    method: payload.method || "GET",
    headers: sanitizeHeaders(payload.headers || {}),
    body: normalizeBody(payload.body),
    targetPageUrl: TARGET_URL
  };

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      extensionWaiters.delete(id);
      reject(new Error(\`No cli2anything++ browser extension responded. Load \${EXTENSION_DIR} as an unpacked Chrome extension, open \${TARGET_LABEL} in that same browser, then retry.\`));
    }, 60_000);
    extensionWaiters.set(id, { resolve, reject, timeout });
    dispatchExtensionJob(job);
  });
}

function dispatchExtensionJob(job) {
  const poll = extensionPolls.shift();
  if (poll) {
    clearTimeout(poll.timeout);
    return sendJson(poll.res, 200, { type: "job", job }, corsHeaders());
  }
  extensionJobs.push(job);
}

function recordExtensionSeen(req) {
  extensionLastSeen = Date.now();
  try {
    const url = new URL(req.url, "http://127.0.0.1");
    const version = url.searchParams.get("version");
    if (version) extensionVersion = version;
    else if (!extensionVersion) extensionVersion = null;
  } catch {
    if (!extensionVersion) extensionVersion = null;
  }
}

function waitForExtensionJob(req, res) {
  if (extensionJobs.length) {
    return sendJson(res, 200, { type: "job", job: extensionJobs.shift() }, corsHeaders());
  }
  const timeout = setTimeout(() => {
    const index = extensionPolls.findIndex((poll) => poll.res === res);
    if (index !== -1) extensionPolls.splice(index, 1);
    sendJson(res, 200, { type: "idle" }, corsHeaders());
  }, 8_000);
  extensionPolls.push({ res, timeout });
  const cleanup = () => {
    clearTimeout(timeout);
    const index = extensionPolls.findIndex((poll) => poll.res === res);
    if (index !== -1) extensionPolls.splice(index, 1);
  };
  req.on("aborted", cleanup);
  res.on("close", () => {
    if (!res.writableEnded) cleanup();
  });
}

async function ensureCdpBrowser({ cdpEndpoint, url, userDataDir, autoLaunch, profileMode = "existing", restartExisting = false }) {
  if (await canFetch(cdpEndpoint + "/json/version")) return;
  if (!autoLaunch) {
    throw new Error(\`Chrome DevTools Protocol is not available at \${cdpEndpoint}\`);
  }

  if (!["existing", "isolated"].includes(profileMode)) {
    throw new Error("--browser-profile must be one of: existing, isolated");
  }

  if (profileMode === "existing" && restartExisting) {
    await quitChromeIfSupported();
  }

  if (profileMode === "isolated") {
    await mkdir(userDataDir, { recursive: true });
  }

  const { port } = parseLocalCdpEndpoint(cdpEndpoint);
  const chrome = chromeExecutable();
  const profileArgs = profileMode === "isolated" ? [\`--user-data-dir=\${userDataDir}\`] : [];
  const child = spawn(chrome.command, [
    ...chrome.prefixArgs,
    \`--remote-debugging-port=\${port}\`,
    ...profileArgs,
    "--no-first-run",
    "--no-default-browser-check",
    url
  ], { stdio: "ignore", detached: true });
  child.unref();
  try {
    await waitForHttp(cdpEndpoint + "/json/version", 15_000);
  } catch (error) {
    if (profileMode === "existing") {
      throw new Error(
        \`Could not attach to the existing Chrome profile through \${cdpEndpoint}. \` +
        "Chrome usually cannot enable remote debugging after it is already running. " +
        "Quit Chrome and rerun, or rerun with --restart-existing-browser to let cli2anything++ restart Chrome, " +
        "or use --browser-profile isolated for a separate profile. " +
        \`Original error: \${error.message}\`
      );
    }
    throw error;
  }
}

function chromeExecutable() {
  if (process.platform === "darwin") {
    return {
      command: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      prefixArgs: []
    };
  }
  if (process.platform === "win32") {
    return { command: "cmd", prefixArgs: ["/c", "start", "", "chrome"] };
  }
  return { command: "google-chrome", prefixArgs: [] };
}

function parseLocalCdpEndpoint(cdpEndpoint) {
  const parsed = new URL(cdpEndpoint);
  if (!["127.0.0.1", "localhost"].includes(parsed.hostname)) {
    throw new Error(\`Refusing to auto-launch Chrome for non-local CDP endpoint: \${cdpEndpoint}\`);
  }
  return { port: Number(parsed.port || "9222") };
}

async function quitChromeIfSupported() {
  if (process.platform !== "darwin") return;
  try {
    await new Promise((resolve, reject) => {
      const child = spawn("osascript", ["-e", 'tell application "Google Chrome" to quit'], { stdio: "ignore" });
      child.on("error", reject);
      child.on("exit", (code) => code === 0 ? resolve() : reject(new Error(\`osascript exited with \${code}\`)));
    });
    await new Promise((resolve) => setTimeout(resolve, 2000));
  } catch {
    // Chrome may not be running; launch will still proceed.
  }
}

async function canFetch(url) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForHttp(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
      lastError = new Error(\`HTTP \${response.status}\`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error(\`Timed out waiting for Chrome DevTools Protocol at \${url}: \${lastError?.message || "unknown error"}\`);
}

function sanitizeHeaders(headers) {
  const blocked = new Set([
    "authorization",
    "cookie",
    "set-cookie",
    "x-xsrf-token",
    "x-csrf-token",
    "csrf-token",
    "host",
    "origin",
    "referer",
    "user-agent",
    "content-length"
  ]);
  const clean = {};
  for (const [key, value] of Object.entries(headers || {})) {
    if (!blocked.has(key.toLowerCase())) clean[key] = value;
  }
  return clean;
}

function normalizeBody(body) {
  if (body === undefined || body === null || body === "") return undefined;
  if (typeof body !== "string") return body;
  try {
    return JSON.parse(body);
  } catch {
    return body;
  }
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.setEncoding("utf8");
    req.on("data", (chunk) => { body += chunk; });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function sendJson(res, status, value, extraHeaders = {}) {
  send(res, status, "application/json; charset=utf-8", JSON.stringify(value ?? null), extraHeaders);
}

function send(res, status, contentType, body, extraHeaders = {}) {
  res.writeHead(status, {
    "content-type": contentType,
    "cache-control": "no-store",
    ...extraHeaders
  });
  res.end(body);
}

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type"
  };
}

function getArg(args, name) {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}
`;
}

async function writeCliPackage(outDir, manifest) {
  const binName = `cli-${slugify(manifest.target)}`;
  const packageJson = {
    name: binName,
    version: "0.1.0",
    private: true,
    type: "module",
    description: `Generated CLI for ${manifest.target} ${manifest.filterKeyword} APIs.`,
    bin: {
      [binName]: `./bin/${binName}.mjs`
    },
    engines: {
      node: ">=20"
    }
  };

  await writeJson(`${outDir}/package.json`, packageJson);
  const binPath = `${outDir}/bin/${binName}.mjs`;
  await writeText(binPath, createGeneratedCliBin({ binName, manifest }));
  await chmod(resolve(binPath), 0o755);
}

async function writeSwaggerExtension(outDir) {
  await rm(`${outDir}/content-script.js`, { force: true });
  await writeJson(`${outDir}/manifest.json`, {
    manifest_version: 3,
    name: "cli2anything++ Browser Bridge",
    version: EXTENSION_BRIDGE_VERSION,
    description: "Universal local bridge for cli2anything++ Swagger to reuse existing browser sessions.",
    permissions: [
      "alarms",
      "scripting",
      "tabs"
    ],
    host_permissions: [
      "<all_urls>"
    ],
    background: {
      service_worker: "background.js",
      type: "module"
    },
    content_scripts: [
      {
        matches: [
          "http://127.0.0.1/*",
          "http://localhost/*"
        ],
        js: [
          "content.js"
        ],
        run_at: "document_start"
      }
    ],
    action: {
      default_title: "cli2anything++ Browser Bridge"
    }
  });

  await writeText(`${outDir}/background.js`, `const PORT_START = 47831;
const PORT_COUNT = 100;
const BRIDGE_VERSION = ${JSON.stringify(EXTENSION_BRIDGE_VERSION)};
const ALARM_NAME = "cli2anything:scan";
const SERVER_POLL_TTL_MS = 15_000;
let polling = false;
const serverPolls = new Map();

chrome.runtime.onInstalled.addListener(() => {
  ensureAlarm();
  startPolling();
});
chrome.runtime.onStartup.addListener(() => {
  ensureAlarm();
  startPolling();
});
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message && message.type === "cli2anything:wake") {
    ensureAlarm();
    startPolling();
    sendResponse({ ok: true });
  }
});
chrome.action.onClicked.addListener(() => startPolling());
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) startPolling();
});
chrome.tabs.onUpdated.addListener((_tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url && /^https?:\\/\\//.test(tab.url)) {
    startPolling();
  }
});

ensureAlarm();
startPolling();

function ensureAlarm() {
  chrome.alarms.create(ALARM_NAME, {
    delayInMinutes: 0.02,
    periodInMinutes: 0.5
  });
}

function startPolling() {
  if (polling) return;
  polling = true;
  pollLoop().finally(() => {
    polling = false;
    setTimeout(startPolling, 1000);
  });
}

async function pollLoop() {
  while (true) {
    try {
      const servers = await findServers();
      for (const server of servers) ensureServerPoll(server);
      await delay(1500);
    } catch {
      await delay(1500);
    }
  }
}

function ensureServerPoll(server) {
  const existing = serverPolls.get(server);
  if (existing && Date.now() - existing.startedAt < SERVER_POLL_TTL_MS) return;
  const promise = pollServerLoop(server).finally(() => {
    if (serverPolls.get(server)?.promise === promise) serverPolls.delete(server);
  });
  serverPolls.set(server, { promise, startedAt: Date.now() });
}

async function pollServerLoop(server) {
  while (true) {
    try {
      markServerPollActive(server);
      const response = await fetchWithTimeout(\`\${server}/__cap/extension/poll?version=\${encodeURIComponent(BRIDGE_VERSION)}\`, { cache: "no-store" }, 12_000);
      markServerPollActive(server);
      const payload = await response.json();
      if (payload.type === "job") {
        const result = await executeJobInTargetTab(payload.job);
        markServerPollActive(server);
        await fetchWithTimeout(\`\${server}/__cap/extension/result?version=\${encodeURIComponent(BRIDGE_VERSION)}\`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(result)
        }, 5_000);
      }
    } catch {
      await delay(1500);
      if (!await ping(server)) return;
    }
  }
}

function markServerPollActive(server) {
  const current = serverPolls.get(server);
  if (current) current.startedAt = Date.now();
}

async function findServers() {
  const checks = [];
  for (let port = PORT_START; port < PORT_START + PORT_COUNT; port += 1) {
    const candidate = \`http://127.0.0.1:\${port}\`;
    checks.push(ping(candidate).then((ok) => ok ? candidate : null));
  }
  return (await Promise.all(checks)).filter(Boolean);
}

async function ping(candidate) {
  try {
    const response = await fetchWithTimeout(\`\${candidate}/__cap/extension/hello?version=\${encodeURIComponent(BRIDGE_VERSION)}\`, { cache: "no-store" }, 1_500);
    const body = await response.json();
    return Boolean(response.ok && body && body.bridge === "extension");
  } catch {
    return false;
  }
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 30_000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function executeJobInTargetTab(job) {
  try {
    const tab = await getTargetTab(job.url, job.targetPageUrl);
    await waitForTabReady(tab.id);
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      world: "MAIN",
      func: browserFetchJob,
      args: [job]
    });
    return { id: job.id, ...(result && result.result ? result.result : result) };
  } catch (error) {
    return {
      id: job.id,
      ok: false,
      status: 598,
      contentType: "application/json",
      body: { message: error && error.message ? error.message : String(error) }
    };
  }
}

async function getTargetTab(requestUrl, targetPageUrl) {
  const target = new URL(requestUrl);
  const pattern = \`\${target.protocol}//\${target.host}/*\`;
  const tabs = await chrome.tabs.query({ url: pattern });
  if (tabs.length) return tabs.find((tab) => tab.active) || tabs[0];
  return chrome.tabs.create({ url: targetPageUrl || target.origin, active: true });
}

async function waitForTabReady(tabId) {
  const tab = await chrome.tabs.get(tabId);
  if (tab.status === "complete") return;
  await new Promise((resolve) => {
    const listener = (updatedTabId, changeInfo) => {
      if (updatedTabId === tabId && changeInfo.status === "complete") {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
    setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, 15000);
  });
}

async function browserFetchJob(job) {
  try {
    const headers = { ...(job.headers || {}) };
    const hasHeader = (name) => Object.keys(headers).some((key) => key.toLowerCase() === name.toLowerCase());
    const readCookie = (name) => {
      const prefix = \`\${name}=\`;
      const item = document.cookie.split(/;\\s*/).find((part) => part.startsWith(prefix));
      return item ? decodeURIComponent(item.slice(prefix.length)) : "";
    };
    const requestUrl = new URL(job.url, location.href);
    const sameSite = requestUrl.hostname === location.hostname || (
      requestUrl.hostname.endsWith(\`.\${location.hostname}\`) ||
      location.hostname.endsWith(\`.\${requestUrl.hostname}\`) ||
      requestUrl.hostname.split(".").slice(-2).join(".") === location.hostname.split(".").slice(-2).join(".")
    );
    const ctoken = sameSite ? (readCookie("ctoken") || readCookie("_CHIPS-ctoken")) : "";
    if (ctoken && !requestUrl.searchParams.has("ctoken")) requestUrl.searchParams.set("ctoken", ctoken);
    const xsrf = readCookie("XSRF-TOKEN");
    if (xsrf && !hasHeader("X-XSRF-TOKEN")) headers["X-XSRF-TOKEN"] = xsrf;
    const requestBody = job.body === undefined || job.body === null || job.body === ""
      ? undefined
      : typeof job.body === "string"
        ? job.body
        : JSON.stringify(job.body);
    const response = await fetch(requestUrl.toString(), {
      method: job.method || "GET",
      headers,
      body: requestBody,
      credentials: "include"
    });
    const contentType = response.headers.get("content-type") || "";
    const text = await response.text();
    let body = text;
    if (contentType.includes("json")) {
      try {
        body = JSON.parse(text);
      } catch {
        body = null;
      }
    }
    return {
      ok: response.ok,
      status: response.status,
      contentType,
      body
    };
  } catch (error) {
    return {
      ok: false,
      status: 599,
      contentType: "application/json",
      body: { message: error && error.message ? error.message : String(error) }
    };
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}\n`);

  await writeText(`${outDir}/content.js`, `wakeBridge();
setInterval(wakeBridge, 2000);
window.addEventListener("focus", wakeBridge);
document.addEventListener("visibilitychange", wakeBridge);

function wakeBridge() {
  try {
    chrome.runtime.sendMessage({ type: "cli2anything:wake" }, () => {
      void chrome.runtime.lastError;
    });
  } catch {}
}
`);

  await writeText(`${outDir}/README.md`, `# cli2anything++ Browser Bridge

This single extension lets every cli2anything++ Swagger UI reuse your current logged-in browser sessions without opening a separate Chrome profile and without copying cookies.

Install once in your existing Chrome:

1. Open \`chrome://extensions\`.
2. Enable Developer mode.
3. Click "Load unpacked".
4. Select this folder.
5. Retry Swagger "Try it out". If no matching site tab exists, the extension opens one.

The extension has broad host permissions so it can serve all targets generated by cli2anything++. It only receives jobs from local cli2anything++ proxy servers on \`127.0.0.1\`.
`);
}

function createGeneratedCliBin({ binName, manifest }) {
  return `#!/usr/bin/env node
import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { BrowserPageSession, ExtensionBridgeSession, ZenMuxBrowserClient, ZenMuxClient } from "../sdk/index.mjs";

const PACKAGE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const LOGS_URL = "https://zenmux.ai/platform/logs";

async function main() {
  const [command, ...args] = process.argv.slice(2);
  try {
    if (command === "logs:list") return await withClient(args, async (client) => {
      const days = Number(getArg(args, "--days") || "7");
      const now = Date.now();
      const startTime = now - days * 24 * 60 * 60 * 1000;
      const pageNo = Number(getArg(args, "--page") || "1");
      const pageSize = Number(getArg(args, "--page-size") || "20");
      return print(await client.listLogs({ startTime, stopTime: now, pageNo, pageSize }));
    });

    if (command === "logs:detail") return await withClient(args, async (client) => {
      const requestId = args.find((arg) => !arg.startsWith("--"));
      if (!requestId) throw new Error("logs:detail requires <requestId>");
      return print(await client.getLogDetail(requestId, { includePayloads: !args.includes("--no-payloads") }));
    });

    if (command === "filters:api-keys") return await withClient(args, async (client) => {
      return print(args.includes("--all") ? await client.listAllApiKeys() : await client.listApiKeys());
    });

    if (command === "filters:finish-reasons") return await withClient(args, async (client) => {
      return print(await client.getFinishReasons());
    });

    if (command === "open") return await openPath(PACKAGE_DIR);
    usage();
    process.exit(command ? 1 : 0);
  } catch (error) {
    console.error(error?.stack || error?.message || String(error));
    process.exit(1);
  }
}

async function withClient(args, fn) {
  if (args.includes("--direct")) return fn(new ZenMuxClient());

  const browserBridge = getArg(args, "--browser-bridge") || process.env.CLI2ANYTHING_BROWSER_BRIDGE || "extension";
  const session = browserBridge === "cdp"
    ? await BrowserPageSession.connect({
      cdpEndpoint: getArg(args, "--cdp") || process.env.API_DRAG_CDP_ENDPOINT || "http://127.0.0.1:9222",
      url: getArg(args, "--url") || LOGS_URL,
      targetUrlIncludes: getArg(args, "--target-url-includes") || "zenmux.ai",
      apiVersion: getArg(args, "--api-version") || process.env.ZENMUX_API_VERSION
    })
    : await ExtensionBridgeSession.start({
      targetOrigin: "https://${manifest.target}",
      targetPageUrl: getArg(args, "--url") || LOGS_URL,
      apiVersion: getArg(args, "--api-version") || process.env.ZENMUX_API_VERSION,
      portStart: Number(getArg(args, "--port") || "47831")
    });

  try {
    return await fn(new ZenMuxBrowserClient(session));
  } finally {
    session.close();
  }
}

function usage() {
  console.log(\`${binName}

Generated from cli2anything++ for ${manifest.target} (${manifest.scope} scope${manifest.requestedFilterKeyword ? `, filter ${manifest.requestedFilterKeyword}` : ""}).

Commands:
  logs:list [--days 7]
  logs:detail <requestId>
  filters:api-keys [--all]
  filters:finish-reasons
  open

Default mode uses the cli2anything++ universal Chrome extension and your existing browser session.
Use --browser-bridge cdp for the older CDP transport, or --direct to call with explicit environment credentials.
\`);
}

function print(value) {
  console.log(JSON.stringify(value, null, 2));
}

function getArg(args, name) {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

async function openPath(path) {
  const command = process.platform === "darwin" ? "open" : process.platform === "win32" ? "cmd" : "xdg-open";
  const args = process.platform === "win32" ? ["/c", "start", "", path] : [path];
  const child = spawn(command, args, { stdio: "ignore", detached: true });
  child.unref();
}

main();
`;
}

async function openPath(path) {
  const target = /^[a-z][a-z0-9+.-]*:/i.test(path) ? path : resolve(path);
  const command = process.platform === "darwin" ? "open" : process.platform === "win32" ? "cmd" : "xdg-open";
  const args = process.platform === "win32" ? ["/c", "start", "", target] : [target];
  const child = spawn(command, args, { stdio: "ignore", detached: true });
  child.unref();
}

async function runCommand(command, args, options = {}) {
  await new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      stdio: options.stdio || "inherit"
    });
    child.on("error", rejectPromise);
    child.on("exit", (code) => {
      if (code === 0) resolvePromise();
      else rejectPromise(new Error(`${command} ${args.join(" ")} exited with ${code}`));
    });
  });
}

async function ensureCdpBrowser({ cdpEndpoint, url, userDataDir, autoLaunch, profileMode = "existing", restartExisting = false }) {
  if (await canFetch(`${normalizeEndpoint(cdpEndpoint)}/json/version`, 1000)) return false;
  if (!autoLaunch) {
    throw new Error(`Chrome DevTools Protocol is not available at ${cdpEndpoint}`);
  }

  if (!["existing", "isolated"].includes(profileMode)) {
    throw new Error("--browser-profile must be one of: existing, isolated");
  }

  if (profileMode === "existing" && restartExisting) {
    await quitChromeIfSupported();
  }

  if (profileMode === "isolated") {
    await mkdir(userDataDir, { recursive: true });
  }

  const { port } = parseLocalCdpEndpoint(cdpEndpoint);
  const chrome = chromeExecutable();
  const profileArgs = profileMode === "isolated" ? [`--user-data-dir=${userDataDir}`] : [];
  const child = spawn(chrome.command, [
    ...chrome.prefixArgs,
    `--remote-debugging-port=${port}`,
    ...profileArgs,
    "--no-first-run",
    "--no-default-browser-check",
    url
  ], {
    stdio: "ignore",
    detached: true
  });
  child.unref();
  try {
    await waitForHttp(`${normalizeEndpoint(cdpEndpoint)}/json/version`, 15_000);
  } catch (error) {
    if (profileMode === "existing") {
      throw new Error(
        `Could not attach to the existing Chrome profile through ${cdpEndpoint}. ` +
        "Chrome usually cannot enable remote debugging after it is already running. " +
        "Quit Chrome and rerun, or rerun with --restart-existing-browser to let cli2anything++ restart Chrome, " +
        "or use --browser-profile isolated for a separate profile. " +
        `Original error: ${error.message}`
      );
    }
    throw error;
  }
  return true;
}

function chromeExecutable() {
  if (process.platform === "darwin") {
    return {
      command: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      prefixArgs: []
    };
  }
  if (process.platform === "win32") {
    return { command: "cmd", prefixArgs: ["/c", "start", "", "chrome"] };
  }
  return { command: "google-chrome", prefixArgs: [] };
}

function parseLocalCdpEndpoint(cdpEndpoint) {
  const parsed = new URL(cdpEndpoint);
  if (!["127.0.0.1", "localhost"].includes(parsed.hostname)) {
    throw new Error(`Refusing to auto-launch Chrome for non-local CDP endpoint: ${cdpEndpoint}`);
  }
  return { port: Number(parsed.port || "9222") };
}

async function quitChromeIfSupported() {
  if (process.platform !== "darwin") return;
  try {
    await runCommand("osascript", ["-e", 'tell application "Google Chrome" to quit'], { stdio: "ignore" });
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 2000));
  } catch {
    // The browser may not be running; launch will still proceed.
  }
}

async function canFetch(url, timeoutMs = 1000) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
    return response.ok;
  } catch {
    return false;
  }
}

async function startSwaggerServer({ serverPath, port, cdpEndpoint, targetUrlIncludes, url, browserBridge, browserProfile, restartExisting }) {
  const child = spawn(process.execPath, [
    resolve(serverPath),
    "--port",
    String(port),
    "--cdp",
    cdpEndpoint,
    "--target-url-includes",
    targetUrlIncludes,
    "--url",
    url,
    "--browser-bridge",
    browserBridge,
    "--browser-profile",
    browserProfile,
    ...(restartExisting ? ["--restart-existing-browser"] : [])
  ], {
    stdio: "ignore",
    detached: true
  });
  child.unref();
  await waitForHttp(`http://127.0.0.1:${port}/__cap/health`);
}

async function findOpenPort(startPort) {
  for (let port = startPort; port < startPort + 100; port += 1) {
    if (await isPortOpen(port)) return port;
  }
  throw new Error(`No open port found from ${startPort} to ${startPort + 99}`);
}

function isPortOpen(port) {
  return new Promise((resolvePromise) => {
    const server = createNetServer();
    server.once("error", () => resolvePromise(false));
    server.once("listening", () => {
      server.close(() => resolvePromise(true));
    });
    server.listen(port, "127.0.0.1");
  });
}

async function waitForHttp(url, timeoutMs = 5_000) {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  throw new Error(`Timed out waiting for ${url}: ${lastError?.message || "unknown error"}`);
}

function normalizeEndpoint(endpoint) {
  return String(endpoint).replace(/\/+$/, "");
}

function normalizeOptionalKeyword(value) {
  const keyword = String(value || "").trim();
  return keyword || null;
}

function isLogKeyword(value) {
  return new Set(["log", "logs", "activity"]).has(String(value || "").toLowerCase());
}

function parseDepth(value) {
  const depth = Number(value);
  if (!Number.isInteger(depth) || depth < 0) {
    throw new Error("--depth must be a non-negative integer; use --depth 0 for no limit");
  }
  return depth;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function normalizePath(path) {
  return path
    .replace(/\$\{[^}]+\}/g, "{value}")
    .replace(/^\/?/, "/")
    .replace(/\/\{value\}/g, "/{id}");
}

function isTarget(value) {
  if (!value || value.startsWith("-")) return false;
  if (value.includes("://")) return true;
  return /^[a-z0-9.-]+\.[a-z]{2,}$/i.test(value);
}

function normalizeTargetHost(value) {
  const input = String(value || "").trim();
  const url = input.includes("://") ? new URL(input) : new URL(`https://${input}`);
  return url.hostname.replace(/^www\./, "");
}

function slugify(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function normalizeDiscoveredEndpoints(chunks) {
  const endpoints = new Set(chunks.flatMap((chunk) => chunk.endpoints));
  return [...endpoints].sort();
}

function getArg(args, name) {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

function defaultExtensionDir() {
  return resolve(homedir(), ".cli2anything-plus-plus/browser-extension");
}

async function fetchText(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`failed to fetch ${url}: HTTP ${response.status}`);
  return response.text();
}

async function writeJson(path, value) {
  const out = resolve(path);
  await mkdir(dirname(out), { recursive: true });
  await writeFile(out, `${JSON.stringify(value, null, 2)}\n`);
}

async function writeText(path, value) {
  const out = resolve(path);
  await mkdir(dirname(out), { recursive: true });
  await writeFile(out, value);
}

main();
