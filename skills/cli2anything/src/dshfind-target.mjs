import { DSHFIND_CATEGORIES_QUERY, DSHFIND_DATASET_QUERY } from "./dshfind-openapi.mjs";

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
    endpoint: "GET /graphql?query={value}",
    role: "primary:categories",
    capability: "plugins.categories",
    reason: "Return all available plugin categories and their current counts from the public pluginFacets query."
  },
  {
    endpoint: "POST /graphql",
    role: "primary:graphql-query",
    capability: "graphql.query",
    reason: "Execute field-selectable public queries for dataset metadata, facets, cursor pages, and rich plugin details."
  },
  {
    endpoint: "GET /graphql/schema",
    role: "dependency:graphql-schema",
    capability: "graphql.schema",
    reason: "Download the published SDL used instead of GraphQL introspection."
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
    { endpoint: "GET /healthz", url: `${API_BASE}/healthz` },
    { endpoint: "GET /v1/suggest?q={value}", url: `${API_BASE}/v1/suggest?q=memory` },
    { endpoint: "GET /graphql?query={value}", url: `${API_BASE}/graphql?query=${encodeURIComponent(DSHFIND_CATEGORIES_QUERY)}` },
    {
      endpoint: "POST /graphql",
      url: `${API_BASE}/graphql`,
      options: {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ query: DSHFIND_DATASET_QUERY, operationName: "DshFindDataset" })
      }
    },
    { endpoint: "GET /graphql/schema", url: `${API_BASE}/graphql/schema`, responseType: "text" },
    { endpoint: "GET /v1/plugins", url: `${API_BASE}/v1/plugins?page=1&per_page=2` },
    { endpoint: "GET /v1/plugins/{owner}/{repo}?snapshot_days={value}", url: `${API_BASE}/v1/plugins/deepseek-ai/deepseek-harness?snapshot_days=7` },
    { endpoint: "GET /market/manifest.json", url: `${API_BASE}/market/manifest.json` },
    { endpoint: "GET /market/v1/plugins", url: `${API_BASE}/market/v1/plugins?limit=2` }
  ];
  const observations = [];
  for (const probe of probes) {
    const { endpoint, url } = probe;
    const response = await fetchImpl(url, probe.options || { headers: { Accept: probe.responseType === "text" ? "application/graphql" : "application/json" } });
    const body = probe.responseType === "text" ? await response.text() : await response.json().catch(() => null);
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
        apifox: "apifox/openapi.json",
        graphqlSchema: "apifox/graphql.schema.graphql",
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
      node("listPluginCategories", "Plugin categories", "GET", "/graphql", "filter-source", 40, 220),
      node("executeGraphQLQuery", "GraphQL query", "POST", "/graphql", "field-selectable", 330, 280),
      node("getGraphQLSchema", "GraphQL schema", "GET", "/graphql/schema", "schema", 620, 280),
      node("suggestPlugins", "Suggest plugins", "GET", "/v1/suggest", "search", 40, 350),
      node("getPlugin", "Plugin detail", "GET", "/v1/plugins/{owner}/{repo}", "detail", 330, 40),
      node("getCatalog", "Bulk catalog", "GET", "/v1/catalog", "bulk", 330, 160),
      node("getMarketManifest", "Market manifest", "GET", "/market/manifest.json", "manifest", 40, 480),
      node("listMarketPlugins", "Market page", "GET", "/market/v1/plugins", "catalog-page", 330, 480),
      node("getHealth", "API health", "GET", "/healthz", "health", 620, 220)
    ],
    edges: [
      {
        id: "getGraphQLSchema-to-executeGraphQLQuery",
        from: "getGraphQLSchema",
        to: "executeGraphQLQuery",
        relation: "schema-contract",
        sourceSelector: "$",
        parameterMap: {},
        confidence: 1,
        safe: true,
        reason: "The published SDL defines the fields and arguments accepted by the read-only GraphQL endpoint."
      },
      {
        id: "listPluginCategories-to-listPlugins",
        from: "listPluginCategories",
        to: "listPlugins",
        relation: "filter-discovery",
        sourceSelector: "$.data.pluginFacets.categories[*].value",
        parameterMap: { category: "$selection" },
        confidence: 1,
        safe: true,
        reason: "pluginFacets categories are the supported category values for the REST list filter."
      },
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
      autoRunMethods: ["GET", "POST"],
      queryPostAllowList: ["executeGraphQLQuery"],
      mutationBlockWords: ["create", "update", "delete", "remove", "save", "submit", "vote", "comment"]
    }
  };
}

function node(id, label, method, path, role, x, y) {
  return { id, label, operationId: id, method, path, role, safeAutoRun: true, ui: { x, y } };
}

function trimSample(body) {
  if (typeof body === "string") return body.slice(0, 1000);
  if (!body || typeof body !== "object") return body;
  if (Array.isArray(body)) return body.slice(0, 2);
  const copy = { ...body };
  if (Array.isArray(copy.data)) copy.data = copy.data.slice(0, 2);
  if (Array.isArray(copy.items)) copy.items = copy.items.slice(0, 2);
  if (Array.isArray(copy.snapshots)) copy.snapshots = copy.snapshots.slice(0, 2);
  return copy;
}
