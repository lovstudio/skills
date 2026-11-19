// 共绩算力（suanli.cn）的 target adapter。
// Open API 的证据是官方 Apifox 公开分享里逐接口导出的 OpenAPI 片段（vendor-published），
// 大模型云服务的证据是 docs.suanli.cn 的示例；不臆造任何未出现在证据中的接口。
import { chmod, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

export const SUANLI_HOSTS = new Set(["suanli.cn", "openapi.suanli.cn", "api.suanli.cn", "docs.suanli.cn", "console.suanli.cn"]);
const TARGET = "suanli.cn";
const SCOPE = "openapi-and-llm";
const ADAPTER = "suanli";
const VERSION = "0.1.0";
const CLI_NAME = "lov-suanli-cli";
const METHODS = ["get", "post", "put", "patch", "delete"];
const FOLDER_PREFIX = "共绩算力 Open API/";
const LLM_TAG = "大模型云服务";
// Apifox 编辑器的界面元数据，不属于接口语义。
const APIFOX_UI_KEYS = new Set(["x-apifox-orders", "x-apifox-refs", "x-apifox-ignore-properties", "x-apifox-overrides"]);
const AUTH_HEADERS = ["version", "timestamp", "sign_str"];
const OVERVIEW_AUTH = "https://docs.suanli.cn/api-key/overview";
const GATEWAY_NOTE = "未实测：网关先校验凭据再路由，无凭据探测无法确认单个接口。";
const LIVE_NOTE = "已用真实密钥只读实测通过；字段结构仍以官方文档为准。";
// 平台 API 密钥的形态（UUID 加 14 位时间戳），实测证据里出现即视为泄漏。
const TOKEN_LIKE = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-\d{14}/i;

export function createSuanliOpenapi(discovery, fragments, liveChecks = null) {
  if (discovery?.target !== TARGET || discovery?.scope !== SCOPE || discovery?.authorized !== true) {
    throw new Error("suanli adapter requires authorized suanli.cn openapi-and-llm discovery evidence");
  }
  if (!discovery.sources?.length || !discovery.auth?.openapi?.baseUrl || !discovery.auth?.llm?.baseUrl || !Array.isArray(discovery.llmOperations)) {
    throw new Error("Incomplete suanli discovery: sources, auth.openapi, auth.llm and llmOperations are required");
  }
  if (fragments?.schema !== "suanli-apifox-fragments/v1" || !fragments.docs?.length) {
    throw new Error("suanli adapter requires the vendor Apifox fragments collected by scripts/suanli_discover.py");
  }

  const notes = [];
  const schemas = {};
  const groups = new Map();
  for (const doc of fragments.docs) {
    for (const [name, schema] of Object.entries(doc.fragment?.components?.schemas || {})) {
      if (!schemas[name]) schemas[name] = schema;
      else if (JSON.stringify(schemas[name]) !== JSON.stringify(schema)) notes.push(`组件 ${name} 在 ${doc.apifoxId} 中定义不同，保留首次出现的版本。`);
    }
    for (const [path, item] of Object.entries(doc.fragment?.paths || {})) {
      for (const [method, op] of Object.entries(item)) {
        if (!METHODS.includes(method)) continue;
        const key = `${method.toUpperCase()} ${path}`;
        if (!groups.has(key)) groups.set(key, { method, path, variants: [] });
        groups.get(key).variants.push({ doc, op });
      }
    }
  }

  const paths = {};
  const usedIds = new Set();
  const apifoxToOperation = new Map();
  const tagNames = [];
  for (const { method, path, variants } of groups.values()) {
    const op = normalizeOperation({ method, path, variants, usedIds });
    for (const { doc } of variants) apifoxToOperation.set(doc.apifoxId, op.operationId);
    paths[path] ||= {};
    paths[path][method] = op;
    if (!tagNames.includes(op.tags[0])) tagNames.push(op.tags[0]);
  }

  const llmServer = new URL(discovery.auth.llm.baseUrl).origin;
  for (const llm of discovery.llmOperations) {
    const { method, path, evidence, ...rest } = llm;
    if (paths[path]?.[method]) throw new Error(`LLM operation ${method} ${path} collides with an Open API path`);
    usedIds.add(rest.operationId);
    paths[path] ||= { servers: [{ url: llmServer, description: "大模型云服务（文档 Base URL 为 /v1）" }] };
    paths[path][method] = {
      ...toOas31(rest),
      tags: [LLM_TAG],
      security: [{ LlmBearer: [] }],
      "x-observation": "documented-docs-example",
      "x-evidence": { basis: "文档", live: false, sources: evidence, note: GATEWAY_NOTE },
      ...(rest.operationId === "llmChatCompletions" ? { "x-billable": "按 Token 计费；生成物未调用。" } : {}),
    };
  }
  if (discovery.llmOperations.length) tagNames.push(LLM_TAG);
  const live = applyLiveChecks(paths, liveChecks);

  const spec = {
    openapi: "3.1.0",
    info: {
      title: "共绩算力 Open API 与大模型云服务",
      version: "1.0.0",
      description: [
        "由 cli2anything++ 从共绩算力公开官方文档生成：Open API 部分逐接口取自官方 Apifox 公开分享中导出的 OpenAPI 片段，未改写路径与字段；",
        live
          ? `大模型云服务部分取自 docs.suanli.cn 的示例。其中 ${live.count} 个只读接口已用真实密钥实测（x-observation 为 live-verified-*），其余未实测；写操作没有执行。`
          : "大模型云服务部分取自 docs.suanli.cn 的示例。所有接口都没有带凭据实测，写操作没有执行。",
        `Open API 鉴权：请求头 token、version、timestamp；RSA 模式另加 sign_str。详见 ${OVERVIEW_AUTH} 与 https://docs.suanli.cn/api-key/rsa 。`,
        "凭据不包含在本文件内。",
      ].join("\n"),
      "x-adapter-version": VERSION,
    },
    servers: [{ url: discovery.auth.openapi.baseUrl, description: "共绩算力 Open API 正式环境" }],
    tags: tagNames.map(name => ({ name })),
    paths,
    components: {
      schemas: toOas31(schemas),
      securitySchemes: {
        ApiKeyAuth: { type: "apiKey", in: "header", name: "token", description: `平台 API 密钥。还需 version、timestamp 头；RSA 模式还需 sign_str。获取：${discovery.auth.openapi.howToObtain}` },
        LlmBearer: { type: "http", scheme: "bearer", description: `大模型云服务 API Key。获取：${discovery.auth.llm.howToObtain}` },
      },
    },
  };

  const dangling = [...collectRefs(spec)].filter(ref => !ref.startsWith("#/components/schemas/") || !spec.components.schemas[ref.slice("#/components/schemas/".length)]);
  if (dangling.length) notes.push(`未解析的 $ref：${dangling.join(", ")}`);

  spec["x-discovery"] = {
    observedAt: discovery.observedAt,
    authorization: discovery.authorization,
    sources: discovery.sources,
    apifox: {
      shareUrl: fragments.shareUrl,
      llmsTxt: fragments.llmsTxt,
      fetchedAt: fragments.fetchedAt,
      pages: fragments.docs.length,
      uniqueOperations: groups.size,
      redaction: fragments.redaction,
    },
    normalization: [
      "OpenAPI 3.0.1 片段合并为一个 3.1.0 文档；nullable 改写为 type 联合 null。",
      "header 参数 token 改用 components.securitySchemes.ApiKeyAuth 表达；官方 securitySchemes 的 type 取值（jwt、bearer、apikey）不是合法 OpenAPI 值，已改写，未被任何接口引用的 AdminAuth、bearerAuth 已移除。",
      "version 头统一为字符串、默认 1.0.0；timestamp 头统一为 13 位毫秒整数；sign_str 头统一为可选（RSA 模式必填）。",
      "operationId 由 path 派生（官方片段未提供），tags 取 Apifox 目录。",
      "去掉 Apifox 编辑器元数据 x-apifox-orders、x-apifox-refs、x-apifox-ignore-properties、x-apifox-overrides。",
      ...notes,
    ],
    docConflicts: discovery.docConflicts || [],
    gatewayProbes: discovery.gatewayProbes || [],
    ...(live ? { liveChecks: live.summary } : {}),
    llmErrors: discovery.llmErrors,
    limitations: discovery.limitations || [],
  };
  return { spec, apifoxToOperation };
}

// 把真实密钥的只读实测结果合入对应操作；只接受成功的只读调用，避免把文档推断冒充实测。
function applyLiveChecks(paths, liveChecks) {
  if (!liveChecks) return null;
  if (liveChecks.schema !== "suanli-live-checks/v1" || liveChecks.target !== TARGET || liveChecks.readOnly !== true || !Array.isArray(liveChecks.checks) || !liveChecks.checks.length) {
    throw new Error("suanli live checks must be a read-only suanli-live-checks/v1 file for suanli.cn");
  }
  if (!["token", "rsa"].includes(liveChecks.mode) || !liveChecks.observedAt) throw new Error("suanli live checks need mode (token|rsa) and observedAt");
  if (TOKEN_LIKE.test(JSON.stringify(liveChecks))) throw new Error("suanli live checks contain a credential-looking value; remove it before generating");
  const observation = `live-verified-${liveChecks.mode}-mode`;
  const verified = [];
  for (const check of liveChecks.checks) {
    const [method, path] = String(check.endpoint || "").split(" ");
    const op = paths[path]?.[method?.toLowerCase()];
    if (!op) throw new Error(`live check ${check.endpoint} does not match any generated operation`);
    if (op["x-write-operation"]) throw new Error(`live check ${check.endpoint} is a write operation; only read-only checks are accepted`);
    const expected = op.tags[0] === LLM_TAG ? check.result?.httpOk === true : check.result?.httpOk === true && check.result?.code === "0000";
    if (!expected) throw new Error(`live check ${check.endpoint} did not succeed; record only successful calls`);
    op["x-observation"] = observation;
    op["x-evidence"] = {
      ...op["x-evidence"],
      basis: "实测",
      live: true,
      liveCheck: { observedAt: liveChecks.observedAt, mode: liveChecks.mode, request: check.request, result: check.result, ...(check.note ? { note: check.note } : {}) },
      note: LIVE_NOTE,
    };
    verified.push(check.endpoint);
  }
  return {
    count: verified.length,
    summary: { observedAt: liveChecks.observedAt, mode: liveChecks.mode, authorization: liveChecks.authorization, client: liveChecks.client, note: liveChecks.note, verified },
  };
}

function normalizeOperation({ method, path, variants, usedIds }) {
  const first = variants[0];
  const base = structuredClone(first.op);
  const meta = parseMetaTable(first.op.description);
  const folder = String(first.op["x-apifox-folder"] || first.doc.folder || "").replace(FOLDER_PREFIX, "") || "其他";

  let parameters = mergeParameters(variants.map(v => v.op.parameters || []));
  const declared = new Set(parameters.filter(p => p.in === "header").map(p => p.name));
  const authHeaders = AUTH_HEADERS.every(name => declared.has(name)) ? "declared" : declared.size ? "partially-declared" : "inferred-from-overview";
  parameters = parameters.filter(p => !(p.in === "header" && p.name === "token"));
  for (const name of AUTH_HEADERS) {
    if (!parameters.some(p => p.in === "header" && p.name === name)) {
      parameters.push({ name, in: "header", required: name !== "sign_str", "x-inferred-from": OVERVIEW_AUTH });
    }
  }
  parameters = parameters.map(normalizeAuthHeader);

  const summaries = [...new Set(variants.map(v => v.op.summary).filter(Boolean))];
  const description = variants.length === 1
    ? base.description
    : [
      `官方 Apifox 中同一个 ${method.toUpperCase()} ${path} 有 ${variants.length} 份接口页，按页列出说明；参数已合并，响应结构取第一份。`,
      ...variants.map(v => `#### ${v.op.summary}（${v.doc.apifoxId}）\n\n${v.op.description || ""}`),
    ].join("\n\n");

  const operationId = uniqueId(deriveOperationId(path), method, usedIds);
  const write = isWriteOperation(method, path);
  delete base.security;
  const op = toOas31({
    ...base,
    operationId,
    summary: summaries.join(" / "),
    description,
    tags: [folder],
    parameters,
    security: [{ ApiKeyAuth: [] }],
    "x-apifox-tags": base.tags,
    "x-observation": "documented-apifox-openapi",
    "x-evidence": {
      basis: "文档",
      live: false,
      sources: variants.map(v => ({ apifoxId: v.doc.apifoxId, title: v.doc.title, url: v.doc.url, sha256: v.doc.sha256 })),
      note: GATEWAY_NOTE,
    },
    "x-suanli-auth": {
      encryption: meta.encryption,
      signature: meta.signature,
      interfaceVersion: meta.version,
      authHeaders,
      note: meta.encryption ? "请求体需用平台公钥加密，只能用 RSA 模式调用；requestBody 描述的是加密前的明文 JSON。" : undefined,
    },
  });
  if (write) op["x-write-operation"] = "会改变账户资源或产生费用；未在线执行，仅来自官方 Apifox 定义。";
  return op;
}

function normalizeAuthHeader(param) {
  if (param.in !== "header") return param;
  if (param.name === "version") {
    return { ...param, required: true, description: "接口版本，字符串，通常为 1.0.0", schema: { type: "string", default: "1.0.0" }, example: "1.0.0" };
  }
  if (param.name === "timestamp") {
    return { ...param, required: true, description: "毫秒级 Unix 时间戳（13 位），每次请求重新生成", schema: { type: "integer" }, example: 1770194570564 };
  }
  if (param.name === "sign_str") {
    return { ...param, required: false, description: "RSA 签名模式必填：RSA-SHA256（PKCS#1 v1.5）签名的 Base64；Token 模式不传", schema: { type: "string" }, example: undefined };
  }
  return param;
}

function mergeParameters(lists) {
  const merged = new Map();
  const seen = new Map();
  for (const list of lists) {
    for (const param of list) {
      const key = `${param.in}:${param.name}`;
      seen.set(key, (seen.get(key) || 0) + 1);
      merged.set(key, merged.has(key) ? mergeParam(merged.get(key), param) : structuredClone(param));
    }
  }
  return [...merged.entries()].map(([key, param]) => ({ ...param, required: Boolean(param.required) && seen.get(key) === lists.length }));
}

function mergeParam(a, b) {
  const out = { ...a, required: Boolean(a.required) && Boolean(b.required) };
  const sa = a.schema || {};
  const sb = b.schema || {};
  const valuesA = enumValues(sa);
  const valuesB = enumValues(sb);
  const schema = { ...sa };
  if (valuesA && valuesB) {
    schema.enum = [...new Set([...valuesA, ...valuesB])];
    delete schema.const;
  } else if (valuesA || valuesB) {
    const examples = [...new Set([...(valuesA || []), ...(valuesB || []), ...(sa.examples || []), ...(sb.examples || [])])];
    delete schema.enum;
    delete schema.const;
    delete schema["x-apifox-enum"];
    if (examples.length) schema.examples = examples;
  }
  if (sa.type !== sb.type && [sa.type, sb.type].includes("number")) schema.type = "number";
  out.schema = schema;
  if (b.description && b.description !== a.description) out.description = [a.description, b.description].filter(Boolean).join("；");
  if ((a.example === undefined || a.example === "" || a.example === 0) && b.example !== undefined && b.example !== "") out.example = b.example;
  return out;
}

function enumValues(schema) {
  if (Array.isArray(schema.enum)) return schema.enum;
  if (schema.const !== undefined) return [schema.const];
  return null;
}

function parseMetaTable(description = "") {
  const row = String(description).match(/\|\s*(v[\d.]+|-)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|/);
  if (!row) return { version: null, encryption: false, signature: null };
  return { version: row[1], encryption: row[3] === "是", signature: row[4] === "是" };
}

// 只读查询多以 list/search/detail/check/get_* 结尾；其余 POST 会改变资源或产生费用。
export function isWriteOperation(method, path) {
  if (method.toLowerCase() === "get") return false;
  const last = path.split("/").filter(Boolean).pop() || "";
  return !(["list", "search", "detail", "check"].includes(last) || /^(get|list|page_list)_/.test(last));
}

export function deriveOperationId(path) {
  const parts = path.replace(/^\/api\//, "/").split(/[/_-]+/).filter(Boolean);
  return parts.map((part, index) => (index ? part[0].toUpperCase() + part.slice(1) : part)).join("");
}

function uniqueId(id, method, used) {
  let candidate = used.has(id) ? `${id}${method[0].toUpperCase()}${method.slice(1)}` : id;
  for (let n = 2; used.has(candidate); n += 1) candidate = `${id}${n}`;
  used.add(candidate);
  return candidate;
}

function toOas31(node) {
  if (Array.isArray(node)) return node.map(toOas31);
  if (!node || typeof node !== "object") return node;
  const out = {};
  for (const [key, value] of Object.entries(node)) {
    if (APIFOX_UI_KEYS.has(key) || value === undefined) continue;
    out[key] = toOas31(value);
  }
  if (out.nullable === true) {
    delete out.nullable;
    if (typeof out.type === "string") out.type = [out.type, "null"];
    else if (Array.isArray(out.type) && !out.type.includes("null")) out.type = [...out.type, "null"];
    if (Array.isArray(out.enum) && !out.enum.includes(null)) out.enum = [...out.enum, null];
  } else if (out.nullable === false) {
    delete out.nullable;
  }
  return out;
}

function collectRefs(node, refs = new Set()) {
  if (Array.isArray(node)) node.forEach(item => collectRefs(item, refs));
  else if (node && typeof node === "object") {
    for (const [key, value] of Object.entries(node)) {
      if (key === "$ref" && typeof value === "string") refs.add(value);
      else collectRefs(value, refs);
    }
  }
  return refs;
}

export function listOperations(spec) {
  return Object.entries(spec.paths).flatMap(([path, item]) =>
    Object.entries(item)
      .filter(([method]) => METHODS.includes(method))
      .map(([method, op]) => ({
        operationId: op.operationId,
        includedEndpoint: `${method.toUpperCase()} ${path}`,
        method: method.toUpperCase(),
        path,
        tag: op.tags[0],
        observation: op["x-observation"],
        base: op.tags[0] === LLM_TAG ? "llm" : "openapi",
        write: Boolean(op["x-write-operation"]),
        encryption: Boolean(op["x-suanli-auth"]?.encryption),
        authHeaders: op["x-suanli-auth"]?.authHeaders || "bearer",
      })));
}

export function createSuanliApiGraph({ spec, discovery, fragments, apifoxToOperation }) {
  const operations = listOperations(spec);
  const byEndpoint = new Map(operations.map(op => [op.includedEndpoint, op.operationId]));
  const edges = [];
  const add = edge => {
    if (!edge.from || !edge.to || edge.from === edge.to) return;
    if (edges.some(e => e.from === edge.from && e.to === edge.to)) return;
    edges.push(edge);
  };
  for (const edge of discovery.workflowEdges || []) {
    add({ from: byEndpoint.get(edge.from), to: byEndpoint.get(edge.to), sourceSelector: edge.sourceSelector, basis: edge.basis, doc: edge.doc });
  }
  // 官方说明里引用其他接口页（api-NNN）的，视为“先调被引用的接口取值”。
  const dangling = [];
  for (const doc of fragments.docs) {
    const consumer = apifoxToOperation.get(doc.apifoxId);
    for (const item of Object.values(doc.fragment?.paths || {})) {
      for (const op of Object.values(item)) {
        for (const ref of new Set(String(op?.description || "").match(/api-\d+/g) || [])) {
          const producer = apifoxToOperation.get(ref);
          if (!producer) dangling.push({ in: doc.apifoxId, ref });
          else add({ from: producer, to: consumer, sourceSelector: "官方说明引用该接口的返回值", basis: "apifox-description-link", doc: doc.url });
        }
      }
    }
  }
  return {
    target: TARGET,
    scope: SCOPE,
    rootOperationId: byEndpoint.get("GET /api/deployment/resource/search") || operations[0]?.operationId,
    nodes: operations,
    edges,
    danglingLinks: dangling,
  };
}

export async function generateSuanliBundle(args) {
  const get = key => {
    const index = args.indexOf(key);
    return index < 0 ? undefined : args[index + 1];
  };
  const modes = new Set(String(get("--output") || "bundle").split(",").map(s => s.trim()).filter(Boolean));
  for (const mode of modes) {
    if (!["bundle", "swagger", "cli"].includes(mode)) throw new Error(`suanli adapter supports --output bundle, swagger, cli (comma-separated); got ${mode}`);
  }
  if (get("--filter-keyword") && !["openapi", "api", "all"].includes(get("--filter-keyword"))) {
    throw new Error("suanli adapter covers the whole public Open API and LLM surface; --filter-keyword is not supported");
  }
  if (!get("--discovery")) throw new Error("suanli adapter requires --discovery with the curated suanli.cn evidence");

  const discoveryPath = resolve(get("--discovery"));
  const discovery = JSON.parse(await readFile(discoveryPath, "utf8"));
  const fragmentsPath = get("--schema") ? resolve(get("--schema")) : resolve(dirname(discoveryPath), discovery.evidenceFiles?.apifoxFragments || "suanli-apifox-fragments.json");
  const fragments = JSON.parse(await readFile(fragmentsPath, "utf8"));
  const livePath = get("--live-checks") ? resolve(get("--live-checks")) : discovery.evidenceFiles?.liveChecks ? resolve(dirname(discoveryPath), discovery.evidenceFiles.liveChecks) : null;
  const liveChecks = livePath ? JSON.parse(await readFile(livePath, "utf8")) : null;
  const { spec, apifoxToOperation } = createSuanliOpenapi(discovery, fragments, liveChecks);
  const graph = createSuanliApiGraph({ spec, discovery, fragments, apifoxToOperation });
  const operations = graph.nodes;
  const out = resolve(get("--out") || "generated/suanli-cn-openapi");

  const count = predicate => operations.filter(predicate).length;
  const byTag = operations.reduce((acc, op) => ({ ...acc, [op.tag]: (acc[op.tag] || 0) + 1 }), {});
  const manifest = {
    name: `${TARGET}:${SCOPE}`,
    target: TARGET,
    scope: SCOPE,
    adapter: ADAPTER,
    version: VERSION,
    cliName: modes.has("cli") ? CLI_NAME : undefined,
    operationCount: operations.length,
    readOperations: count(op => !op.write),
    writeOperations: count(op => op.write),
    encryptedOperations: count(op => op.encryption),
    byObservation: operations.reduce((acc, op) => ({ ...acc, [op.observation]: (acc[op.observation] || 0) + 1 }), {}),
    authHeadersInferred: operations.filter(op => op.authHeaders === "inferred-from-overview").map(op => op.includedEndpoint),
    byTag,
    liveVerified: count(op => op.observation.startsWith("live-verified")),
    liveVerifiedEndpoints: operations.filter(op => op.observation.startsWith("live-verified")).map(op => op.includedEndpoint),
    servers: { openapi: discovery.auth.openapi.baseUrl, llm: discovery.auth.llm.baseUrl },
    endpoints: operations.map(({ operationId, includedEndpoint, tag, observation, write, encryption }) => ({ operationId, includedEndpoint, tag, observation, write, encryption })),
    outputs: {
      openapi: "openapi.json",
      apiGraph: "api-graph.json",
      sdk: "sdk/index.mjs",
      ...(modes.has("swagger") ? { swagger: "swagger/index.html", drilldown: "swagger/drilldown.html", swaggerServer: "swagger/server.mjs" } : {}),
      ...(modes.has("cli") ? { cli: `bin/${CLI_NAME}.mjs` } : {}),
    },
    secretsIncluded: false,
  };

  const dirs = [out, `${out}/sdk`, ...(modes.has("swagger") ? [`${out}/swagger`] : []), ...(modes.has("cli") ? [`${out}/bin`] : [])];
  for (const dir of dirs) await mkdir(dir, { recursive: true });
  await writeFile(`${out}/manifest.json`, JSON.stringify(manifest, null, 2) + "\n");
  await writeFile(`${out}/openapi.json`, JSON.stringify(spec, null, 2) + "\n");
  await writeFile(`${out}/api-graph.json`, JSON.stringify(graph, null, 2) + "\n");
  await writeFile(`${out}/discovery.filtered.json`, JSON.stringify(discovery, null, 2) + "\n");
  await writeFile(`${out}/README.md`, createSuanliReadme({ manifest, spec, discovery, graph, modes }));

  const table = Object.fromEntries(operations.map(op => [op.operationId, { method: op.method, path: op.path, base: op.base, encryption: op.encryption, write: op.write }]));
  const sdk = (await readFile(new URL("./suanli-client.mjs", import.meta.url), "utf8")).replace("/*__SUANLI_OPERATIONS__*/ {}", JSON.stringify(table, null, 2));
  await writeFile(`${out}/sdk/index.mjs`, sdk);

  if (modes.has("swagger")) {
    await writeFile(`${out}/swagger/index.html`, createSwaggerIndex(manifest));
    await writeFile(`${out}/swagger/drilldown.html`, createDrilldown({ manifest, graph }));
    await writeFile(`${out}/swagger/server.mjs`, await readFile(new URL("./suanli-swagger-server.mjs", import.meta.url), "utf8"));
  }
  if (modes.has("cli")) {
    await writeFile(`${out}/bin/${CLI_NAME}.mjs`, await readFile(new URL("./suanli-cli-runtime.mjs", import.meta.url), "utf8"));
    await chmod(`${out}/bin/${CLI_NAME}.mjs`, 0o755);
    await writeFile(`${out}/package.json`, JSON.stringify({
      name: CLI_NAME,
      version: VERSION,
      description: `共绩算力 Open API 与大模型云服务命令行（${operations.length} 个操作，schema 驱动）`,
      type: "module",
      bin: { [CLI_NAME]: `./bin/${CLI_NAME}.mjs` },
      exports: { ".": "./sdk/index.mjs" },
      files: ["bin", "sdk", "swagger", "openapi.json", "manifest.json", "api-graph.json", "README.md"],
      engines: { node: ">=20" },
      private: true,
    }, null, 2) + "\n");
  }

  console.log(`generated ${out}`);
  console.log(`operations: ${operations.length} (read: ${manifest.readOperations}, write: ${manifest.writeOperations}, live-verified: ${manifest.liveVerified})`);
  console.log("no credentials exported");
  return { out, manifest, spec, graph };
}

function createSuanliReadme({ manifest, spec, discovery, graph, modes }) {
  const tagRows = Object.entries(manifest.byTag).map(([tag, n]) => `| ${tag} | ${n} | ${graph.nodes.filter(op => op.tag === tag && op.write).length} |`).join("\n");
  const cli = manifest.cliName || CLI_NAME;
  const cliSection = modes.has("cli") ? `## CLI

\`\`\`bash
node bin/${cli}.mjs help                                   # 按分组列出全部命令
node bin/${cli}.mjs deployment-resource-search --dry-run   # 只打印请求，不发出
node bin/${cli}.mjs deployment-task-search --page 1 --page-size 5
node bin/${cli}.mjs deployment-task-change-points --data '{"task_id":388,"points":1}' --confirm-write
node bin/${cli}.mjs llm-list-models
\`\`\`

命令表在启动时由随包的 \`openapi.json\` 构建，operationId 转 kebab-case 即命令名，${manifest.operationCount} 个操作都能直接调用。查询参数用同名选项（下划线可写成连字符），请求体用 \`--data '<json>'\` 或 \`--data @file.json\`。写操作必须加 \`--confirm-write\` 才会发出；\`--dry-run\` 打印请求时凭据只显示是否已提供。

` : "";
  const swaggerSection = modes.has("swagger") ? `## Swagger

\`\`\`bash
node swagger/server.mjs --port 4790      # 只监听 127.0.0.1
\`\`\`

打开 http://127.0.0.1:4790 。页面里的 Try it out 经本地代理发出，代理从环境变量读取凭据并现场生成 timestamp 与 sign_str，浏览器里不需要也不应填写 token。代理默认拒绝写操作，确需调试写接口时加 \`--allow-write\`。\`swagger/drilldown.html\` 按分组列出全部操作与调用顺序。

` : "";
  return `# 共绩算力 Open API 与大模型云服务

由 cli2anything++ suanli 适配器 ${VERSION} 生成，共 ${manifest.operationCount} 个操作：Open API ${manifest.operationCount - (manifest.byTag[LLM_TAG] || 0)} 个、大模型云服务 ${manifest.byTag[LLM_TAG] || 0} 个；只读 ${manifest.readOperations} 个，写操作 ${manifest.writeOperations} 个，要求请求体加密 ${manifest.encryptedOperations} 个。

## 证据等级

- \`documented-apifox-openapi\`：官方 Apifox 公开分享中逐接口导出的 OpenAPI 片段，路径与字段未改写。来源 ${spec["x-discovery"].apifox.shareUrl}，抓取于 ${spec["x-discovery"].apifox.fetchedAt}。
- \`documented-docs-example\`：docs.suanli.cn 文档中的调用示例。
${manifest.liveVerified ? `- \`${spec["x-discovery"].liveChecks.mode === "rsa" ? "live-verified-rsa-mode" : "live-verified-token-mode"}\`：在上面任一文档等级之上，又用真实密钥做了只读实测并返回成功，实测时间与请求、结果摘要写在该操作的 \`x-evidence.liveCheck\`。
` : ""}
${manifest.liveVerified
    ? `已实测 ${manifest.liveVerified} 个只读接口（${spec["x-discovery"].liveChecks.observedAt}，${spec["x-discovery"].liveChecks.mode} 模式）：${manifest.liveVerifiedEndpoints.join("、")}。其余接口仍只有文档证据，写操作都没有执行。`
    : "所有接口都没有带凭据实测（liveVerified = 0）。"}两个网关都先校验凭据再路由，无凭据探测只证明了鉴权头名称与错误格式，记录在 \`openapi.json\` 的 \`x-discovery.gatewayProbes\`。每个操作的 \`x-evidence.sources\` 给出接口页地址与 sha256。

## 推断与未验证

- 下列 ${manifest.authHeadersInferred.length} 个接口的官方片段没有声明 token、version、timestamp 头，按 ${OVERVIEW_AUTH} 的统一规则补上：${manifest.authHeadersInferred.join("、") || "无"}。
- operationId 由 path 派生；api-graph.json 中 basis 为 \`parameter-name\` 的边按参数名推断，\`docs\` 与 \`apifox-description-link\` 的边有文档依据。
${(discovery.limitations || []).map(item => `- ${item}`).join("\n")}

## 文档之间的冲突

${(discovery.docConflicts || []).map(item => `- ${item}`).join("\n")}

## 认证

凭据不写入本目录任何文件，运行时从环境变量读取：

\`\`\`bash
export SUANLI_TOKEN=<API 密钥>                           # Token 模式与 RSA 模式都需要
export SUANLI_PRIVATE_KEY_FILE=./private.key             # 可选：设置后自动按 RSA 模式签名
export SUANLI_PLATFORM_PUBLIC_KEY_FILE=./platform_pub.pem # 加密接口需要：平台返回的公钥
export SUANLI_LLM_API_KEY=<大模型云服务 API Key>
\`\`\`

在 macOS 上也可以只存一次钥匙串，之后 CLI 与 Swagger 代理在环境变量缺失时自动读取（\`SUANLI_KEYCHAIN=0\` 可关闭）：

\`\`\`bash
security add-generic-password -a "$USER" -s suanli-token -w     # Open API 密钥，提示输入两次，不回显
security add-generic-password -a "$USER" -s suanli-llm-key -w   # 大模型云服务 API Key
\`\`\`

获取 Open API 密钥：${discovery.auth.openapi.howToObtain}

获取大模型 API Key：${discovery.auth.llm.howToObtain}

## 资源分组

| 分组 | 操作数 | 其中写操作 |
| --- | --- | --- |
${tagRows}

${cliSection}${swaggerSection}## SDK

\`sdk/index.mjs\` 导出 \`SuanliClient\`：\`request(method, path, {query, body, encryption})\` 自动加 version、timestamp、token，提供私钥时生成 sign_str，需加密的接口用平台公钥按 244 字节分段加密后再签名；\`call(operationId, {query, body})\` 按生成的操作表调用任意接口；\`chatCompletions()\`、\`listModels()\` 调用大模型云服务。响应 code 不是 "0000" 时抛出 \`SuanliApiError\`。

## 调用顺序

\`api-graph.json\` 记录 ${graph.edges.length} 条调用边，起点是 \`${graph.rootOperationId}\`（资源列表，创建任务时的 resources[].mark 来自这里）。
`;
}

function createSwaggerIndex(manifest) {
  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>共绩算力 API</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css" />
    <style>
      body { margin: 0; background: #fff; }
      #banner { padding: 10px 16px; font: 14px/1.5 system-ui, sans-serif; background: #f4f4f5; border-bottom: 1px solid #ddd; }
      #banner a { margin-left: 12px; }
    </style>
  </head>
  <body>
    <div id="banner"><strong>cli2anything++</strong> ${manifest.target} / ${manifest.operationCount} 个操作。请求经本机代理签名后发出，凭据来自代理进程的环境变量，页面不需要填写 token。<a href="/drilldown">调用顺序</a></div>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({ url: "/openapi.json", dom_id: "#swagger-ui", deepLinking: true, docExpansion: "none", filter: true });
    </script>
  </body>
</html>
`;
}

function createDrilldown({ manifest, graph }) {
  const esc = value => String(value ?? "").replace(/[&<>"]/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]);
  const tags = [...new Set(graph.nodes.map(op => op.tag))];
  const sections = tags.map(tag => `<h2>${esc(tag)}</h2>
<table><thead><tr><th>方法</th><th>路径</th><th>operationId</th><th>证据</th><th>写操作</th><th>加密</th></tr></thead><tbody>
${graph.nodes.filter(op => op.tag === tag).map(op => `<tr><td>${op.method}</td><td><code>${esc(op.path)}</code></td><td><a href="/#/${encodeURIComponent(tag)}/${esc(op.operationId)}">${esc(op.operationId)}</a></td><td>${esc(op.observation)}</td><td>${op.write ? "是" : ""}</td><td>${op.encryption ? "是" : ""}</td></tr>`).join("\n")}
</tbody></table>`).join("\n");
  const edges = graph.edges.map(e => `<li><code>${esc(e.from)}</code> → <code>${esc(e.to)}</code>：${esc(e.sourceSelector)}（${esc(e.basis)}）</li>`).join("\n");
  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>共绩算力 API 调用顺序</title>
    <style>
      :root { --fg: #18181b; --muted: #71717a; --line: #e4e4e7; --bg: #fff; }
      @media (prefers-color-scheme: dark) { :root { --fg: #f4f4f5; --muted: #a1a1aa; --line: #3f3f46; --bg: #18181b; } }
      body { margin: 0 auto; max-width: 1100px; padding: 16px; font: 14px/1.6 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
      table { width: 100%; border-collapse: collapse; margin-bottom: 24px; display: block; overflow-x: auto; }
      th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--line); white-space: nowrap; }
      th { color: var(--muted); font-weight: 500; }
      code { font-size: 13px; }
      a { color: inherit; }
    </style>
  </head>
  <body>
    <h1>共绩算力 API：${manifest.operationCount} 个操作</h1>
    <p>只读 ${manifest.readOperations}，写操作 ${manifest.writeOperations}；已只读实测 ${manifest.liveVerified}，写操作均未执行。<a href="/">返回 Swagger</a></p>
    <h2>调用顺序（${graph.edges.length} 条）</h2>
    <ul>${edges}</ul>
    ${sections}
  </body>
</html>
`;
}
