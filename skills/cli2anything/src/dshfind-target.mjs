const API_BASE = "https://api.dshfind.com";
const PAGE_URL = "https://dshfind.com/zh/plugins";

const ENDPOINTS = [
  {
    endpoint: "GET /v1/plugins",
    role: "primary:list",
    capability: "plugins.list",
    reason: "Search, filter, sort, and paginate the public plugin directory."
  },
  {
    endpoint: "GET /v1/suggest?q={value}",
    role: "primary:search-suggestions",
    capability: "plugins.suggest",
    reason: "Return up to ten lightweight plugin search suggestions."
  },
  {
    endpoint: "GET /v1/plugins/{owner}/{repo}?snapshot_days={value}",
    role: "dependency:detail",
    capability: "plugins.detail",
    reason: "Fetch one plugin with localized editorial content, snapshots, and growth."
  },
  {
    endpoint: "GET /v1/catalog?data_version={value}",
    role: "dependency:bulk-catalog",
    capability: "plugins.catalog",
    reason: "Download the complete public catalog, optionally pinned to a data version."
  },
  {
    endpoint: "GET /market/manifest.json",
    role: "primary:market-manifest",
    capability: "market.manifest",
    reason: "Read the standard DSH catalog-source manifest."
  },
  {
    endpoint: "GET /market/v1/plugins",
    role: "dependency:market-page",
    capability: "market.plugins",
    reason: "Page through the standard DSH catalog-provider contract using an opaque cursor."
  },
  {
    endpoint: "GET /healthz",
    role: "dependency:health",
    capability: "service.health",
    reason: "Read the public API health and loaded-catalog status."
  }
];

export async function discoverDshFindData({ fetchImpl = globalThis.fetch } = {}) {
  if (!fetchImpl) throw new TypeError("A fetch implementation is required");
  const probes = [
    ["GET /healthz", `${API_BASE}/healthz`],
    ["GET /v1/suggest?q={value}", `${API_BASE}/v1/suggest?q=memory`],
    ["GET /v1/plugins", `${API_BASE}/v1/plugins?page=1&per_page=2`],
    ["GET /v1/plugins/{owner}/{repo}?snapshot_days={value}", `${API_BASE}/v1/plugins/deepseek-ai/deepseek-harness?snapshot_days=7`],
    ["GET /market/manifest.json", `${API_BASE}/market/manifest.json`],
    ["GET /market/v1/plugins", `${API_BASE}/market/v1/plugins?limit=2`]
  ];
  const observations = [];
  for (const [endpoint, url] of probes) {
    const response = await fetchImpl(url, { headers: { Accept: "application/json" } });
    const body = await response.json().catch(() => null);
    if (!response.ok) throw new Error(`dshfind discovery probe failed for ${url}: HTTP ${response.status}`);
    observations.push({
      endpoint,
      url,
      status: response.status,
      contentType: response.headers.get("content-type"),
      sample: trimSample(body)
    });
  }
  return {
    target: "dshfind.com",
    apiBase: API_BASE,
    discoveredAt: new Date().toISOString(),
    authority: "Public unauthenticated endpoints only",
    sourcePage: PAGE_URL,
    normalizedEndpoints: ENDPOINTS.map((item) => item.endpoint),
    observations
  };
}

export function createDshFindPackage({ discovery, filterKeyword = "plugins" } = {}) {
  const generatedAt = new Date().toISOString();
  const primaryEndpoints = ENDPOINTS.filter((item) => !item.role.startsWith("dependency:"));
  const dependencyEndpoints = ENDPOINTS.filter((item) => item.role.startsWith("dependency:"));
  return {
    manifest: {
      name: "dshfind.com:plugins",
      target: "dshfind.com",
      apiBase: API_BASE,
      adapter: "dshfind",
      scope: "plugins",
      filterKeyword,
      requestedFilterKeyword: filterKeyword,
      depth: 0,
      generatedAt,
      strategy: "public page evidence + public source contract + live unauthenticated probes",
      outputs: {
        openapi: "openapi.json",
        apiGraph: "api-graph.json",
        discovery: "discovery.filtered.json",
        sdk: "sdk/index.mjs"
      },
      transportModes: ["direct-http: public read-only JSON endpoints; no credentials required"],
      primaryRoutes: ["/zh/plugins"],
      primaryEndpoints,
      dependencyEndpoints,
      capabilities: ENDPOINTS.map(({ capability, endpoint, role, reason }) => ({
        capability,
        endpoint,
        role,
        observed: discovery?.normalizedEndpoints?.includes(endpoint) ?? false,
        reason
      }))
    },
    filteredDiscovery: {
      ...discovery,
      scope: "plugins",
      filterKeyword,
      generatedAt,
      selectedEndpoints: ENDPOINTS
    }
  };
}

export function createDshFindApiGraph() {
  return {
    version: "0.1.0",
    target: "dshfind.com",
    filterKeyword: "plugins",
    generatedAt: new Date().toISOString(),
    rootOperationId: "listPlugins",
    defaultWorkflowId: "dshfind-plugin-discovery",
    nodes: [
      node("listPlugins", "List plugins", "GET", "/v1/plugins", "root-list", 40, 90),
      node("suggestPlugins", "Suggest plugins", "GET", "/v1/suggest", "search", 40, 220),
      node("getPlugin", "Plugin detail", "GET", "/v1/plugins/{owner}/{repo}", "detail", 330, 40),
      node("getCatalog", "Bulk catalog", "GET", "/v1/catalog", "bulk", 330, 160),
      node("getMarketManifest", "Market manifest", "GET", "/market/manifest.json", "manifest", 40, 350),
      node("listMarketPlugins", "Market page", "GET", "/market/v1/plugins", "catalog-page", 330, 350),
      node("getHealth", "API health", "GET", "/healthz", "health", 620, 220)
    ],
    edges: [
      {
        id: "listPlugins-to-getPlugin",
        from: "listPlugins",
        to: "getPlugin",
        relation: "fanout-detail",
        sourceSelector: "$.data[*].full_name",
        itemSelector: "$.data[*]",
        parameterMap: { owner: "$item.owner", repo: "$item.name" },
        confidence: 1,
        safe: true,
        reason: "Each list item exposes owner and name used by the detail path."
      },
      {
        id: "listPlugins-to-getCatalog",
        from: "listPlugins",
        to: "getCatalog",
        relation: "version-pin",
        sourceSelector: "$.data_version",
        parameterMap: { data_version: "$.data_version" },
        confidence: 1,
        safe: true,
        reason: "The list response data_version can pin the full catalog snapshot."
      },
      {
        id: "getMarketManifest-to-listMarketPlugins",
        from: "getMarketManifest",
        to: "listMarketPlugins",
        relation: "declared-transport",
        sourceSelector: "$.transport.endpoint",
        parameterMap: {},
        confidence: 1,
        safe: true,
        reason: "The manifest declares the market paging endpoint."
      },
      {
        id: "listMarketPlugins-to-listMarketPlugins",
        from: "listMarketPlugins",
        to: "listMarketPlugins",
        relation: "cursor-page",
        sourceSelector: "$.page.nextCursor",
        parameterMap: { cursor: "$.page.nextCursor" },
        confidence: 1,
        safe: true,
        reason: "The opaque nextCursor advances standard market pagination."
      }
    ],
    workflows: [
      {
        id: "dshfind-plugin-discovery",
        label: "Search plugin directory and inspect details",
        rootOperationId: "listPlugins",
        itemSelector: "$.data[*]",
        identitySelector: "$.full_name",
        defaultPageSize: 20,
        defaultMaxDrillItems: 20,
        defaultConcurrency: 3,
        fanoutEdges: ["listPlugins-to-getPlugin"]
      },
      {
        id: "dshfind-market-pagination",
        label: "Read standard market catalog pages",
        rootOperationId: "getMarketManifest",
        defaultPageSize: 50,
        defaultMaxDrillItems: 0,
        defaultConcurrency: 1,
        fanoutEdges: ["getMarketManifest-to-listMarketPlugins", "listMarketPlugins-to-listMarketPlugins"]
      }
    ],
    safety: {
      defaultAutoRunPolicy: "read-only",
      autoRunMethods: ["GET"],
      queryPostAllowList: [],
      mutationBlockWords: ["create", "update", "delete", "remove", "save", "submit", "vote", "comment"]
    }
  };
}

function node(id, label, method, path, role, x, y) {
  return { id, label, operationId: id, method, path, role, safeAutoRun: true, ui: { x, y } };
}

function trimSample(body) {
  if (!body || typeof body !== "object") return body;
  if (Array.isArray(body)) return body.slice(0, 2);
  const copy = { ...body };
  if (Array.isArray(copy.data)) copy.data = copy.data.slice(0, 2);
  if (Array.isArray(copy.items)) copy.items = copy.items.slice(0, 2);
  if (Array.isArray(copy.snapshots)) copy.snapshots = copy.snapshots.slice(0, 2);
  return copy;
}
