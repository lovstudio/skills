export function createZenmuxDrilldownLinks() {
  return [
    {
      id: "listLogs-to-getLogActivity",
      from: "listLogs",
      to: "getLogActivity",
      relation: "fanout-detail",
      sourceSelector: "$.data[*].requestId",
      itemSelector: "$.data[*]",
      parameterMap: {
        requestId: "$item.requestId",
        id: "$item.requestId"
      },
      confidence: 0.99,
      safe: true,
      reason: "Log list rows expose requestId, and the dashboard detail route uses the same id in path and query."
    },
    {
      id: "listLogs-to-getLegacyGeneration",
      from: "listLogs",
      to: "getLegacyGeneration",
      relation: "fanout-metadata",
      sourceSelector: "$.data[*].requestId",
      itemSelector: "$.data[*]",
      parameterMap: {
        id: "$item.requestId"
      },
      confidence: 0.96,
      safe: true,
      reason: "The browser-session dashboard endpoint accepts id=<requestId> for generation metadata."
    },
    {
      id: "listLogs-to-getGenerationRequestPayload",
      from: "listLogs",
      to: "getGenerationRequestPayload",
      relation: "fanout-payload",
      sourceSelector: "$.data[*].requestId",
      itemSelector: "$.data[*]",
      parameterMap: {
        id: "$item.requestId",
        type: "userRequest"
      },
      confidence: 0.97,
      safe: true,
      reason: "The logs detail route loads user request payloads with id=<requestId>&type=userRequest."
    },
    {
      id: "listLogs-to-getGenerationResponsePayload",
      from: "listLogs",
      to: "getGenerationResponsePayload",
      relation: "fanout-payload",
      sourceSelector: "$.data[*].requestId",
      itemSelector: "$.data[*]",
      parameterMap: {
        id: "$item.requestId",
        type: "userResponse"
      },
      confidence: 0.98,
      safe: true,
      reason: "The logs detail route loads user response payloads with id=<requestId>&type=userResponse."
    },
    {
      id: "listApiKeys-to-listLogs",
      from: "listApiKeys",
      to: "listLogs",
      relation: "filter-dependency",
      sourceSelector: "$.data[*].id",
      parameterMap: {
        apiKeys: "$selection[]"
      },
      confidence: 0.9,
      safe: true,
      reason: "API key list values populate the log list apiKeys filter."
    },
    {
      id: "getFinishReasons-to-listLogs",
      from: "getFinishReasons",
      to: "listLogs",
      relation: "filter-dependency",
      sourceSelector: "$.data[*]",
      parameterMap: {
        finishReasons: "$selection[]"
      },
      confidence: 0.88,
      safe: true,
      reason: "Finish reason values populate the log list finishReasons filter."
    }
  ];
}

export function createZenmuxApiGraph({ target = "zenmux.ai", filterKeyword = "log", manifest } = {}) {
  if (manifest?.scope === "all") {
    return createEndpointInventoryGraph({ target, filterKeyword, manifest });
  }

  return {
    version: "0.1.0",
    target,
    filterKeyword,
    generatedAt: new Date().toISOString(),
    rootOperationId: "listLogs",
    defaultWorkflowId: "zenmux-log-drilldown",
    nodes: [
      {
        id: "listLogs",
        label: "List logs",
        operationId: "listLogs",
        method: "POST",
        path: "/api/api_key/activity",
        role: "root-list",
        safeAutoRun: true,
        ui: { x: 48, y: 112 }
      },
      {
        id: "getLogActivity",
        label: "Activity detail",
        operationId: "getLogActivity",
        method: "GET",
        path: "/api/api_key/activity/{requestId}",
        role: "detail",
        safeAutoRun: true,
        ui: { x: 318, y: 40 }
      },
      {
        id: "getLegacyGeneration",
        label: "Generation metadata",
        operationId: "getLegacyGeneration",
        method: "GET",
        path: "/api/v1/generation",
        role: "detail",
        safeAutoRun: true,
        ui: { x: 318, y: 152 }
      },
      {
        id: "getGenerationRequestPayload",
        label: "Request payload",
        operationId: "getGenerationRequestPayload",
        method: "GET",
        path: "/api/v1/generation/request",
        role: "payload",
        safeAutoRun: true,
        ui: { x: 602, y: 40 }
      },
      {
        id: "getGenerationResponsePayload",
        label: "Response payload",
        operationId: "getGenerationResponsePayload",
        method: "GET",
        path: "/api/v1/generation/response",
        role: "payload",
        safeAutoRun: true,
        ui: { x: 602, y: 152 }
      },
      {
        id: "listApiKeys",
        label: "API key filters",
        operationId: "listApiKeys",
        method: "GET",
        path: "/api/api_key/list",
        role: "filter",
        safeAutoRun: true,
        ui: { x: 48, y: 232 }
      },
      {
        id: "getFinishReasons",
        label: "Finish reason filters",
        operationId: "getFinishReasons",
        method: "GET",
        path: "/api/api_key/finish_reasons",
        role: "filter",
        safeAutoRun: true,
        ui: { x: 318, y: 232 }
      }
    ],
    edges: createZenmuxDrilldownLinks(),
    workflows: [
      {
        id: "zenmux-log-drilldown",
        label: "Logs list to request/response payloads",
        rootOperationId: "listLogs",
        itemSelector: "$.data[*]",
        identitySelector: "$.requestId",
        defaultPageSize: 20,
        defaultMaxDrillItems: 20,
        defaultConcurrency: 3,
        fanoutEdges: [
          "listLogs-to-getLogActivity",
          "listLogs-to-getLegacyGeneration",
          "listLogs-to-getGenerationRequestPayload",
          "listLogs-to-getGenerationResponsePayload"
        ]
      }
    ],
    safety: {
      defaultAutoRunPolicy: "read-only",
      autoRunMethods: ["GET"],
      queryPostAllowList: ["listLogs"],
      mutationBlockWords: ["create", "update", "delete", "remove", "save", "submit", "cancel"]
    }
  };
}

function createEndpointInventoryGraph({ target, filterKeyword, manifest }) {
  const endpoints = [
    ...(manifest.primaryEndpoints || []),
    ...(manifest.dependencyEndpoints || [])
  ];
  const nodes = endpoints.map((item, index) => {
    const parsed = parseEndpoint(item.includedEndpoint || item.endpoint);
    const group = endpointGroup(parsed.path);
    return {
      id: operationId(parsed.method, parsed.path, index),
      label: labelForEndpoint(parsed.method, parsed.path),
      operationId: operationId(parsed.method, parsed.path, index),
      method: parsed.method,
      path: parsed.path,
      role: roleForEndpoint(parsed.method, parsed.path),
      group,
      safeAutoRun: parsed.method === "GET",
      reason: item.reason,
      ui: gridPosition(index, endpoints.length)
    };
  });

  return {
    version: "0.1.0",
    target,
    filterKeyword,
    scope: "all",
    generatedAt: new Date().toISOString(),
    rootOperationId: nodes[0]?.operationId || "discoveredEndpoints",
    defaultWorkflowId: "zenmux-all-endpoint-inventory",
    nodes,
    edges: inferInventoryEdges(nodes),
    workflows: [
      {
        id: "zenmux-all-endpoint-inventory",
        label: "All discovered endpoint inventory",
        rootOperationId: nodes[0]?.operationId || "discoveredEndpoints",
        defaultPageSize: 50,
        defaultMaxDrillItems: 0,
        defaultConcurrency: 3,
        fanoutEdges: []
      }
    ],
    safety: {
      defaultAutoRunPolicy: "manual",
      autoRunMethods: ["GET"],
      queryPostAllowList: [],
      mutationBlockWords: ["create", "update", "delete", "remove", "save", "submit", "cancel"]
    }
  };
}

function parseEndpoint(endpoint) {
  const match = String(endpoint || "").trim().match(/^([A-Z]+)\s+(.+)$/);
  const method = match?.[1] || "GET";
  const target = match?.[2] || String(endpoint || "/");
  return {
    method,
    path: target.split("?")[0] || "/"
  };
}

function endpointGroup(path) {
  const parts = String(path || "").split("/").filter(Boolean);
  if (parts[0] === "api" && parts[1]) return `/api/${parts[1]}`;
  return parts[0] ? `/${parts[0]}` : "/";
}

function roleForEndpoint(method, path) {
  const lower = `${method} ${path}`.toLowerCase();
  if (method === "GET") return "detail";
  if (/(delete|disable|remove|cancel)/.test(lower)) return "mutation-danger";
  if (/(create|update|enable|regenerate|save|submit)/.test(lower)) return "mutation";
  return "root-list";
}

function labelForEndpoint(method, path) {
  const parts = String(path || "").split("/").filter(Boolean);
  const last = parts.at(-1) || path || "endpoint";
  const cleaned = last.replace(/[{}]/g, "").replace(/[_-]+/g, " ");
  const label = cleaned.replace(/\b\w/g, (char) => char.toUpperCase());
  return label && label !== "Id" ? label : `${method} ${endpointGroup(path)}`;
}

function operationId(method, path, index) {
  const suffix = String(path || "")
    .replace(/[{}]/g, "")
    .split("/")
    .filter(Boolean)
    .map((part) => part.replace(/[^a-zA-Z0-9]+/g, " "))
    .join(" ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace(/\s+/g, "");
  return `${method.toLowerCase()}${suffix || "Root"}${index}`;
}

function gridPosition(index, count) {
  const columns = Math.max(4, Math.ceil(Math.sqrt(count * 1.6)));
  const row = Math.floor(index / columns);
  const column = index % columns;
  const rows = Math.max(1, Math.ceil(count / columns));
  return {
    xRatio: (column + 0.5) / columns,
    yRatio: (row + 0.5) / rows
  };
}

function inferInventoryEdges(nodes) {
  const edges = [];
  const seen = new Set();
  const byMethodPath = new Map(nodes.map((node) => [endpointKey(node.method, node.path), node]));
  const byStem = new Map();

  const addEdge = (from, to, relation, details = {}) => {
    if (!from || !to || from.id === to.id) return;
    const id = details.id || `${from.id}-to-${to.id}-${relation}`;
    const key = `${from.id}->${to.id}:${relation}`;
    if (seen.has(key)) return;
    seen.add(key);
    edges.push({
      id,
      from: from.id,
      to: to.id,
      relation,
      sourceSelector: details.sourceSelector || "",
      itemSelector: details.itemSelector,
      parameterMap: details.parameterMap || {},
      confidence: details.confidence ?? 0.55,
      safe: Boolean(details.safe),
      reason: details.reason || `${from.method} ${from.path} appears related to ${to.method} ${to.path}.`
    });
  };

  for (const node of nodes) {
    const stem = endpointStem(node.path);
    if (!byStem.has(stem)) byStem.set(stem, []);
    byStem.get(stem).push(node);
  }

  addKnownInventoryEdges(byMethodPath, addEdge);

  for (const groupNodes of byStem.values()) {
    if (groupNodes.length < 2) continue;
    const listLike = groupNodes.filter(isListLikeEndpoint);
    const detailLike = groupNodes.filter((node) => isDetailLikeEndpoint(node) || node.path.includes("{"));
    const actions = groupNodes.filter((node) => isActionEndpoint(node));

    for (const source of listLike.slice(0, 4)) {
      for (const target of detailLike.slice(0, 5)) {
        addEdge(source, target, "detail-dependency", {
          confidence: 0.72,
          safe: source.safeAutoRun && target.safeAutoRun,
          sourceSelector: "$.data[*].id",
          parameterMap: { id: "$item.id" },
          reason: "A list/query endpoint and detail endpoint share the same resource stem."
        });
      }
      for (const target of actions.slice(0, 5)) {
        addEdge(source, target, "resource-action", {
          confidence: 0.54,
          safe: false,
          sourceSelector: "$.data[*].id",
          parameterMap: { id: "$selection.id" },
          reason: "A list/query endpoint and write action share the same resource stem."
        });
      }
    }
  }

  for (const node of nodes) {
    if (!isFilterSourceEndpoint(node)) continue;
    const sourceTokens = significantPathTokens(node.path);
    for (const target of nodes) {
      if (target.id === node.id || !isQueryTargetEndpoint(target)) continue;
      const targetTokens = significantPathTokens(target.path);
      const shared = sourceTokens.filter((token) => targetTokens.includes(token));
      if (!shared.length) continue;
      if (node.group !== target.group && shared.length < 2) continue;
      addEdge(node, target, "filter-dependency", {
        confidence: node.group === target.group ? 0.62 : 0.5,
        safe: node.safeAutoRun && target.safeAutoRun,
        sourceSelector: "$.data[*]",
        parameterMap: { filter: "$selection[]" },
        reason: "A list/filter endpoint can plausibly populate a query endpoint."
      });
    }
  }

  addSemanticEdges(nodes, addEdge);

  return edges
    .sort((left, right) =>
      Number(right.safe) - Number(left.safe) ||
      right.confidence - left.confidence ||
      relationRank(left.relation) - relationRank(right.relation)
    )
    .slice(0, 220);
}

function addKnownInventoryEdges(byMethodPath, addEdge) {
  const node = (method, path) => byMethodPath.get(endpointKey(method, path));
  const listLogs = node("POST", "/api/api_key/activity");
  addEdge(listLogs, node("GET", "/api/api_key/activity/{id}"), "fanout-detail", {
    id: "inventory-listLogs-to-getLogActivity",
    sourceSelector: "$.data[*].requestId",
    itemSelector: "$.data[*]",
    parameterMap: { requestId: "$item.requestId", id: "$item.requestId" },
    confidence: 0.99,
    safe: true,
    reason: "Log rows expose requestId, and the activity detail endpoint consumes that id."
  });
  addEdge(listLogs, node("GET", "/api/v1/generation"), "fanout-metadata", {
    id: "inventory-listLogs-to-getLegacyGeneration",
    sourceSelector: "$.data[*].requestId",
    itemSelector: "$.data[*]",
    parameterMap: { id: "$item.requestId" },
    confidence: 0.96,
    safe: true,
    reason: "Log rows expose requestId, and the generation metadata endpoint consumes that id."
  });
  addEdge(listLogs, node("GET", "/api/v1/generation/request"), "fanout-payload", {
    id: "inventory-listLogs-to-getGenerationRequestPayload",
    sourceSelector: "$.data[*].requestId",
    itemSelector: "$.data[*]",
    parameterMap: { id: "$item.requestId", type: "userRequest" },
    confidence: 0.97,
    safe: true,
    reason: "Log rows expose requestId, and the request payload endpoint consumes that id."
  });
  addEdge(listLogs, node("GET", "/api/v1/generation/response"), "fanout-payload", {
    id: "inventory-listLogs-to-getGenerationResponsePayload",
    sourceSelector: "$.data[*].requestId",
    itemSelector: "$.data[*]",
    parameterMap: { id: "$item.requestId", type: "userResponse" },
    confidence: 0.98,
    safe: true,
    reason: "Log rows expose requestId, and the response payload endpoint consumes that id."
  });
  addEdge(node("GET", "/api/api_key/list"), listLogs, "filter-dependency", {
    id: "inventory-listApiKeys-to-listLogs",
    sourceSelector: "$.data[*].id",
    parameterMap: { apiKeys: "$selection[]" },
    confidence: 0.9,
    safe: true,
    reason: "API key list values populate the log list apiKeys filter."
  });
  addEdge(node("GET", "/api/api_key/finish_reasons"), listLogs, "filter-dependency", {
    id: "inventory-getFinishReasons-to-listLogs",
    sourceSelector: "$.data[*]",
    parameterMap: { finishReasons: "$selection[]" },
    confidence: 0.88,
    safe: true,
    reason: "Finish reason values populate the log list finishReasons filter."
  });
}

function addSemanticEdges(nodes, addEdge) {
  const candidates = [];
  for (let leftIndex = 0; leftIndex < nodes.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < nodes.length; rightIndex += 1) {
      const left = nodes[leftIndex];
      const right = nodes[rightIndex];
      if (left.group === right.group) continue;
      const leftTokens = significantPathTokens(left.path);
      const rightTokens = significantPathTokens(right.path);
      const shared = leftTokens.filter((token) => rightTokens.includes(token));
      if (shared.length < 2) continue;
      const score = shared.length / Math.max(leftTokens.length, rightTokens.length, 1);
      if (score < 0.28) continue;
      candidates.push({ left, right, shared, score });
    }
  }

  candidates
    .sort((left, right) => right.score - left.score || right.shared.length - left.shared.length)
    .slice(0, 48)
    .forEach(({ left, right, shared, score }) => {
      const source = isListLikeEndpoint(left) || left.method === "GET" ? left : right;
      const target = source.id === left.id ? right : left;
      addEdge(source, target, "semantic-dependency", {
        confidence: Math.min(0.7, 0.42 + score),
        safe: source.safeAutoRun && target.safeAutoRun,
        sourceSelector: shared.join(","),
        parameterMap: {},
        reason: `Endpoints share semantic path tokens: ${shared.join(", ")}.`
      });
    });
}

function endpointKey(method, path) {
  return `${String(method || "GET").toUpperCase()} ${String(path || "/").replace(/\{requestId\}/g, "{id}")}`;
}

function endpointStem(path) {
  const parts = String(path || "/").split("/").filter(Boolean);
  while (parts.length && /^(list|list_all|detail|create|update|delete|disable|enable|regenerate|save|submit|summary|total|query|download_zip|download_zip_active|download_zip_status|pdf_url|\{[^}]+\})$/i.test(parts.at(-1))) {
    parts.pop();
  }
  return "/" + parts.join("/");
}

function isListLikeEndpoint(node) {
  const lower = `${node.method} ${node.path}`.toLowerCase();
  return /(list|list_all|query|search|summary|leaderboard|timeseries|activity)$/.test(lower) || node.role === "root-list";
}

function isDetailLikeEndpoint(node) {
  const lower = String(node.path || "").toLowerCase();
  return /(\{[^}]+\}|detail|info|status|config|summary|pdf_url|generation\/(request|response)?$)/.test(lower) && node.method === "GET";
}

function isActionEndpoint(node) {
  return node.role === "mutation" || node.role === "mutation-danger" || /(create|update|delete|disable|enable|regenerate|save|submit|execute|refund)/i.test(node.path || "");
}

function isFilterSourceEndpoint(node) {
  return node.method === "GET" && /(list|list_all|filters|finish_reasons|config|preferences|limits)$/i.test(node.path || "");
}

function isQueryTargetEndpoint(node) {
  return node.method === "POST" && /(activity|query|list|summary|total|detail)$/i.test(node.path || "");
}

function significantPathTokens(path) {
  const stopWords = new Set([
    "api", "v1", "common", "public",
    "list", "list_all", "query", "detail", "create", "update", "delete",
    "enable", "disable", "save", "submit", "get", "set", "by", "id"
  ]);
  const parts = String(path || "").split("/").filter(Boolean);
  const resourceParts = parts[0] === "api" && parts.length > 2 ? parts.slice(2) : parts;
  return [...new Set(resourceParts.join("/")
    .replace(/\{[^}]+\}/g, " id ")
    .split(/[^a-zA-Z0-9]+/)
    .map((token) => token.trim().toLowerCase())
    .filter((token) => token.length > 2 && !stopWords.has(token)))];
}

function relationRank(relation) {
  return {
    "fanout-payload": 0,
    "fanout-detail": 1,
    "fanout-metadata": 2,
    "detail-dependency": 3,
    "filter-dependency": 4,
    "resource-action": 5,
    "semantic-dependency": 6
  }[relation] ?? 9;
}
