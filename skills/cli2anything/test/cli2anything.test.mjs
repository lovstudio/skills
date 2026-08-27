import test from "node:test";
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { readFile, rm } from "node:fs/promises";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

test("cli2anything++ generates a log-filtered ZenMux SDK bundle with dependencies", async () => {
  const out = "tmp/cli2anything-zenmux-log";
  await rm(out, { recursive: true, force: true });

  await execFileAsync(process.execPath, [
    "./bin/cli2anything.mjs",
    "zenmux.ai",
    "--filter-keyword",
    "log",
    "--discovery",
    "./artifacts/zenmux-discovered.json",
    "--out",
    out
  ]);

  const manifest = JSON.parse(await readFile(`${out}/manifest.json`, "utf8"));
  const openapi = JSON.parse(await readFile(`${out}/openapi.json`, "utf8"));
  const apiGraph = JSON.parse(await readFile(`${out}/api-graph.json`, "utf8"));
  const sdkIndex = await readFile(`${out}/sdk/index.mjs`, "utf8");

  assert.equal(manifest.name, "zenmux.ai:log");
  assert.deepEqual(manifest.primaryEndpoints.map((item) => item.includedEndpoint), [
    "POST /api/api_key/activity",
    "GET /api/api_key/activity/{id}"
  ]);
  assert.ok(manifest.dependencyEndpoints.some((item) => item.includedEndpoint === "GET /api/api_key/finish_reasons"));
  assert.ok(manifest.transportModes.some((mode) => mode.includes("browser-session")));
  assert.equal(manifest.outputs.apiGraph, "api-graph.json");
  assert.equal(apiGraph.rootOperationId, "listLogs");
  assert.ok(apiGraph.edges.some((edge) => edge.to === "getGenerationResponsePayload" && edge.sourceSelector === "$.data[*].requestId"));
  assert.ok(openapi.paths["/api/api_key/finish_reasons"].get);
  assert.match(sdkIndex, /ZenMuxBrowserClient/);

  await rm(out, { recursive: true, force: true });
});

test("cli2anything++ --output swagger writes a local Swagger UI page", async () => {
  const out = "tmp/cli2anything-swagger";
  const extensionOut = "tmp/cli2anything-extension";
  await rm(out, { recursive: true, force: true });
  await rm(extensionOut, { recursive: true, force: true });

  await execFileAsync(process.execPath, [
    "./bin/cli2anything.mjs",
    "zenmux.ai",
    "--filter-keyword",
    "log",
    "--output",
    "swagger",
    "--no-open",
    "--discovery",
    "./artifacts/zenmux-discovered.json",
    "--out",
    out,
    "--extension-dir",
    extensionOut
  ]);

  const html = await readFile(`${out}/swagger/index.html`, "utf8");
  const drilldown = await readFile(`${out}/swagger/drilldown.html`, "utf8");
  const apiGraph = JSON.parse(await readFile(`${out}/api-graph.json`, "utf8"));
  const server = await readFile(`${out}/swagger/server.mjs`, "utf8");
  const extensionManifest = JSON.parse(await readFile(`${extensionOut}/manifest.json`, "utf8"));
  const background = await readFile(`${extensionOut}/background.js`, "utf8");
  const content = await readFile(`${extensionOut}/content.js`, "utf8");
  assert.match(html, /SwaggerUIBundle/);
  assert.match(html, /href="\/drilldown"/);
  assert.match(html, /__cap\/proxy/);
  assert.match(html, /browser-session proxy enabled/);
  assert.match(html, /tmp\/cli2anything-extension/);
  assert.doesNotMatch(html, /generated\/zenmux-ai-log\/extension/);
  assert.doesNotMatch(html, /consoleCookie/);
  assert.match(drilldown, /Dependency Graph/);
  assert.match(drilldown, /body data-layout="tabs"/);
  assert.match(drilldown, /id="layout-tabs"/);
  assert.match(drilldown, /id="layout-columns"/);
  assert.match(drilldown, /body\[data-layout="columns"\] \.app/);
  assert.match(drilldown, /id="tab-graph"/);
  assert.match(drilldown, /id="tab-logs"/);
  assert.match(drilldown, /id="tab-detail"/);
  assert.match(drilldown, /id="logs-panel" role="tabpanel"/);
  assert.match(drilldown, /id="detail-panel" role="tabpanel"/);
  assert.match(drilldown, /id="close-logs"/);
  assert.match(drilldown, /Close logs panel/);
  assert.match(drilldown, /function setLayout/);
  assert.match(drilldown, /function renderDenseGraph/);
  assert.match(drilldown, /dense-graph/);
  assert.match(drilldown, /target-root/);
  assert.match(drilldown, /namespace-endpoint/);
  assert.match(drilldown, /id="graph-toolbar"/);
  assert.match(drilldown, /id="endpoint-inspector"/);
  assert.match(drilldown, /function renderEndpointInspector/);
  assert.match(drilldown, /data-run-endpoint/);
  assert.match(drilldown, /function runEndpointFromButton/);
  assert.match(drilldown, /endpointOperationSpecs/);
  assert.match(drilldown, /id="tab-ai"/);
  assert.match(drilldown, /id="ai-panel" role="tabpanel"/);
  assert.match(drilldown, /data-close-page="ai"/);
  assert.match(drilldown, /function runAiSidebar/);
  assert.match(drilldown, /function executeRecentImageResultsPlan/);
  assert.match(drilldown, /function resolveRenderableImages/);
  assert.match(drilldown, /function discoverImageLogFilters/);
  assert.match(drilldown, /function scanLogAttemptForImages/);
  assert.match(drilldown, /\/api\/frontend\/model\/provider\/price\/list/);
  assert.match(drilldown, /data-ai-steps/);
  assert.match(drilldown, /slice\(-1000\)/);
  assert.match(drilldown, /function openPage/);
  assert.match(drilldown, /Run listLogs/);
  assert.match(drilldown, /getGenerationResponsePayload/);
  assert.match(drilldown, /\/__cap\/proxy/);
  assert.equal(apiGraph.defaultWorkflowId, "zenmux-log-drilldown");
  assert.ok(apiGraph.edges.some((edge) => edge.id === "listLogs-to-getGenerationResponsePayload"));
  assert.match(server, /BrowserPageSession/);
  assert.match(server, /proxyViaExtension/);
  assert.match(server, /drilldown\.html/);
  assert.match(server, /api-graph\.json/);
  assert.match(server, /__cap\/ai\/plan/);
  assert.match(server, /@ai-sdk\/openai/);
  assert.match(server, /fallbackAiPlan/);
  assert.match(server, /tmp\/cli2anything-extension/);
  assert.match(server, /expectedExtensionVersion/);
  assert.match(server, /extensionCurrent/);
  assert.match(server, /extensionPolling/);
  assert.ok(server.includes('req.url.startsWith("/__cap/extension/result")'));
  assert.match(server, /req\.on\("aborted", cleanup\)/);
  assert.doesNotMatch(server, /req\.on\("close"/);
  assert.doesNotMatch(server, /generated\/zenmux-ai-log\/extension/);
  assert.equal(extensionManifest.name, "cli2anything++ Browser Bridge");
  assert.equal(extensionManifest.version, "0.1.9");
  assert.ok(extensionManifest.permissions.includes("alarms"));
  assert.deepEqual(extensionManifest.host_permissions, ["<all_urls>"]);
  assert.equal(extensionManifest.background.service_worker, "background.js");
  assert.deepEqual(extensionManifest.content_scripts[0].matches, ["http://127.0.0.1/*", "http://localhost/*"]);
  assert.deepEqual(extensionManifest.content_scripts[0].js, ["content.js"]);
  assert.ok(background.includes("__cap/extension/poll"));
  assert.ok(background.includes("BRIDGE_VERSION"));
  assert.ok(background.includes("chrome.alarms.create"));
  assert.ok(background.includes("findServers"));
  assert.ok(background.includes("Promise.all(checks)"));
  assert.ok(background.includes("serverPolls"));
  assert.ok(background.includes("SERVER_POLL_TTL_MS"));
  assert.ok(background.includes("markServerPollActive"));
  assert.ok(background.includes("fetchWithTimeout"));
  assert.ok(background.includes("chrome.scripting.executeScript"));
  assert.ok(background.includes("getTargetTab"));
  assert.ok(background.includes("cli2anything:wake"));
  assert.ok(background.includes("const requestBody ="));
  assert.ok(background.includes('readCookie("XSRF-TOKEN")'));
  assert.ok(background.includes('headers["X-XSRF-TOKEN"] = xsrf'));
  assert.ok(background.includes('readCookie("ctoken")'));
  assert.ok(background.includes('requestUrl.searchParams.set("ctoken", ctoken)'));
  assert.doesNotMatch(background, /body: serializeBody\(job\.body\)/);
  assert.doesNotMatch(background, /function serializeBody/);
  assert.ok(content.includes("setInterval(wakeBridge, 2000)"));
  await execFileAsync(process.execPath, ["--check", `${extensionOut}/background.js`]);
  await execFileAsync(process.execPath, ["--check", `${extensionOut}/content.js`]);
  await execFileAsync(process.execPath, ["--check", `${out}/swagger/server.mjs`]);

  await rm(out, { recursive: true, force: true });
  await rm(extensionOut, { recursive: true, force: true });
});

test("cli2anything++ supports an unfiltered all-site Swagger bundle", async () => {
  const out = "tmp/cli2anything-zenmux-all";
  const extensionOut = "tmp/cli2anything-extension-all";
  await rm(out, { recursive: true, force: true });
  await rm(extensionOut, { recursive: true, force: true });

  await execFileAsync(process.execPath, [
    "./bin/cli2anything.mjs",
    "zenmux.ai",
    "--output",
    "swagger",
    "--no-open",
    "--depth",
    "0",
    "--discovery",
    "./artifacts/zenmux-discovered.json",
    "--out",
    out,
    "--extension-dir",
    extensionOut
  ]);

  const manifest = JSON.parse(await readFile(`${out}/manifest.json`, "utf8"));
  const openapi = JSON.parse(await readFile(`${out}/openapi.json`, "utf8"));
  const apiGraph = JSON.parse(await readFile(`${out}/api-graph.json`, "utf8"));
  const drilldown = await readFile(`${out}/swagger/drilldown.html`, "utf8");
  const filteredDiscovery = JSON.parse(await readFile(`${out}/discovery.filtered.json`, "utf8"));
  const readme = await readFile(`${out}/README.md`, "utf8");

  assert.equal(manifest.name, "zenmux.ai:all");
  assert.equal(manifest.scope, "all");
  assert.equal(manifest.filterKeyword, "all");
  assert.equal(manifest.requestedFilterKeyword, null);
  assert.equal(manifest.depth, 0);
  assert.ok(manifest.primaryEndpoints.length > 8);
  assert.ok(manifest.primaryEndpoints.some((item) => item.includedEndpoint === "POST /api/dashboard/cost/query/cost"));
  assert.ok(manifest.primaryEndpoints.some((item) => item.includedEndpoint === "POST /api/api_key/create"));
  assert.equal(filteredDiscovery.scope, "all");
  assert.ok(openapi.paths["/api/dashboard/cost/query/cost"].post);
  assert.ok(openapi.paths["/api/api_key/create"].post);
  assert.ok(openapi.components.schemas.AnyJson);
  assert.equal(apiGraph.scope, "all");
  assert.equal(apiGraph.nodes.length, manifest.primaryEndpoints.length);
  assert.ok(apiGraph.nodes.length > 20);
  assert.ok(apiGraph.nodes.some((node) => node.path === "/api/dashboard/cost/query/cost"));
  assert.equal(apiGraph.defaultWorkflowId, "zenmux-all-endpoint-inventory");
  assert.match(drilldown, /Endpoint Map/);
  assert.match(drilldown, /Endpoint Inventory/);
  assert.match(drilldown, /target-root/);
  assert.match(readme, /Filter keyword: \(none\)/);
  assert.match(readme, /Discovery depth: unlimited/);

  await rm(out, { recursive: true, force: true });
  await rm(extensionOut, { recursive: true, force: true });
});

test("cli2anything++ --output cli writes a linkable local CLI package", async () => {
  const out = "tmp/cli-zenmux-ai";
  await rm(out, { recursive: true, force: true });

  await execFileAsync(process.execPath, [
    "./bin/cli2anything.mjs",
    "zenmux.ai",
    "--filter-keyword",
    "log",
    "--output",
    "cli",
    "--no-open",
    "--no-link",
    "--discovery",
    "./artifacts/zenmux-discovered.json",
    "--out",
    out
  ]);

  const packageJson = JSON.parse(await readFile(`${out}/package.json`, "utf8"));
  const bin = await readFile(`${out}/bin/cli-zenmux-ai.mjs`, "utf8");
  const browserSdk = await readFile(`${out}/sdk/browser-cdp.mjs`, "utf8");

  assert.equal(packageJson.name, "cli-zenmux-ai");
  assert.equal(packageJson.bin["cli-zenmux-ai"], "./bin/cli-zenmux-ai.mjs");
  assert.match(bin, /logs:list/);
  assert.match(bin, /ZenMuxBrowserClient/);
  assert.match(bin, /ExtensionBridgeSession/);
  assert.match(bin, /--browser-bridge cdp/);
  assert.ok(browserSdk.includes('readCookie("ctoken")'));
  assert.ok(browserSdk.includes('requestUrl.searchParams.set("ctoken", ctoken)'));
  assert.match(await readFile(`${out}/sdk/index.mjs`, "utf8"), /ExtensionBridgeSession/);
  assert.match(await readFile(`${out}/sdk/extension-bridge.mjs`, "utf8"), /__cap\/extension\/poll/);

  await rm(out, { recursive: true, force: true });
});
