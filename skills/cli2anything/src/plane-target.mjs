// Plane 自托管实例的 target adapter。
// 证据来源是 Plane 自身内置的 drf-spectacular 导出（vendor-generated schema），
// 再用 live 探测交叉验证端点存在与认证行为。不臆造任何未出现在 schema 中的接口。
import { chmod, mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const TARGET = "localhost";
const SCOPE = "plane-rest-api-v1";
const ADAPTER = "plane";
const VERSION = "0.1.0";
const CLI_NAME = "lov-plane-cli";
const METHODS = ["get", "post", "patch", "put", "delete"];

export function createPlaneOpenapi(discovery, rawSchema) {
  if (discovery?.scope !== SCOPE || discovery?.authorized !== true) {
    throw new Error("Plane adapter requires authorized plane-rest-api-v1 discovery evidence");
  }
  if (!discovery.sources?.length || !discovery.auth?.name || !discovery.operations?.length || !discovery.probes?.length) {
    throw new Error("Incomplete Plane discovery: sources, auth scheme, operations and live probes are required");
  }
  if (!rawSchema?.paths || !rawSchema?.components?.schemas) {
    throw new Error("Plane adapter requires the vendor-generated schema exported from the running instance");
  }

  const baseUrl = discovery.instance?.publicBaseUrl || `http://${TARGET}`;
  const probeByOperation = new Map(discovery.probes.map(p => [p.operationId, p]));
  const spec = structuredClone(rawSchema);

  // servers 修正：vendor schema 写的是容器内地址，对外要经 proxy 暴露的地址。
  spec.servers = [
    { url: baseUrl, description: "自托管实例（经 proxy 暴露的对外地址）" },
    { url: discovery.instance?.containerServerUrl || "http://api:8000", description: "容器内 API 直连地址，仅在 compose 网络内可用" },
  ];
  spec.info = {
    ...spec.info,
    title: spec.info?.title || "Plane REST API",
    description: [
      spec.info?.description || "",
      "",
      `本文件由 ${discovery.instance?.product || "Plane"} ${discovery.instance?.release || ""} 自托管实例内置的 drf-spectacular 导出，未经人工改写路径或字段；`,
      "仅修正 servers（容器内地址 → 对外地址）并补充证据标注。",
      `认证为 ${discovery.auth.scheme}，请求头 ${discovery.auth.name}；凭据不包含在本文件内。`,
    ].join("\n"),
  };

  // 逐操作标注证据等级：探测过的标 live-probe，其余标 vendor schema。
  for (const [path, item] of Object.entries(spec.paths)) {
    for (const [method, op] of Object.entries(item)) {
      if (!METHODS.includes(method)) continue;
      const probe = probeByOperation.get(op.operationId);
      op["x-observation"] = probe ? "live-probe-401-403" : "vendor-generated-schema";
      if (probe) {
        op["x-probe"] = { path: probe.probedPath, statusNoAuth: probe.statusNoAuth, statusInvalidKey: probe.statusInvalidKey };
      }
      if (method !== "get") op["x-write-operation"] = "未在线执行；仅来自 schema 定义。";
    }
  }

  spec["x-discovery"] = {
    observedAt: discovery.observedAt,
    authorization: discovery.authorization,
    sources: discovery.sources,
    limitations: discovery.limitations,
  };
  return spec;
}

export async function generatePlaneBundle(args) {
  const get = key => {
    const index = args.indexOf(key);
    return index < 0 ? undefined : args[index + 1];
  };
  const outputMode = get("--output") || "bundle";
  if (!["bundle", "cli"].includes(outputMode)) {
    throw new Error("Plane adapter supports --output bundle or --output cli; Swagger is not implemented for this target");
  }
  if (!get("--discovery")) throw new Error("Plane adapter requires --discovery with the exported instance evidence");

  const discovery = JSON.parse(await readFile(resolve(get("--discovery")), "utf8"));
  const schemaPath = get("--schema") || resolve(new URL("../artifacts/plane-schema.raw.json", import.meta.url).pathname);
  const rawSchema = JSON.parse(await readFile(schemaPath, "utf8"));
  const spec = createPlaneOpenapi(discovery, rawSchema);
  const out = resolve(get("--out") || (outputMode === "cli" ? `generated/${CLI_NAME}` : "generated/plane-rest-api-v1"));

  const operations = Object.entries(spec.paths).flatMap(([path, item]) =>
    Object.entries(item)
      .filter(([method]) => METHODS.includes(method))
      .map(([method, op]) => ({
        operationId: op.operationId,
        includedEndpoint: `${method.toUpperCase()} ${path}`,
        tag: (op.tags || ["Other"])[0],
        observation: op["x-observation"],
      })));

  const manifest = {
    name: `${TARGET}:${SCOPE}`,
    target: TARGET,
    scope: SCOPE,
    adapter: ADAPTER,
    version: VERSION,
    cliName: CLI_NAME,
    instance: discovery.instance,
    auth: { scheme: discovery.auth.scheme, header: discovery.auth.name, howToObtain: discovery.auth.howToObtain },
    operationCount: operations.length,
    primaryEndpoints: operations.filter(o => o.observation === "live-probe-401-403"),
    dependencyEndpoints: operations.filter(o => o.observation !== "live-probe-401-403"),
    outputs: { openapi: "openapi.json", apiGraph: "api-graph.json", sdk: "sdk/index.mjs", ...(outputMode === "cli" ? { cli: `bin/${CLI_NAME}.mjs` } : {}) },
    secretsIncluded: false,
  };

  const graph = createPlaneApiGraph(operations);
  const readme = createPlaneReadme({ manifest, discovery, operations, outputMode });

  for (const dir of [out, `${out}/sdk`, ...(outputMode === "cli" ? [`${out}/bin`] : [])]) {
    await mkdir(dir, { recursive: true });
  }
  await writeFile(`${out}/manifest.json`, JSON.stringify(manifest, null, 2) + "\n");
  await writeFile(`${out}/openapi.json`, JSON.stringify(spec, null, 2) + "\n");
  await writeFile(`${out}/api-graph.json`, JSON.stringify(graph, null, 2) + "\n");
  await writeFile(`${out}/discovery.filtered.json`, JSON.stringify(discovery, null, 2) + "\n");
  await writeFile(`${out}/README.md`, readme);
  await writeFile(`${out}/sdk/index.mjs`, await readFile(new URL("./plane-client.mjs", import.meta.url), "utf8"));

  if (outputMode === "cli") {
    await writeFile(`${out}/bin/${CLI_NAME}.mjs`, await readFile(new URL("./plane-cli-runtime.mjs", import.meta.url), "utf8"));
    await chmod(`${out}/bin/${CLI_NAME}.mjs`, 0o755);
    await writeFile(`${out}/package.json`, JSON.stringify({
      name: CLI_NAME,
      version: VERSION,
      description: `Plane REST API v1 命令行（${operations.length} 个操作，schema 驱动）`,
      type: "module",
      bin: { [CLI_NAME]: `./bin/${CLI_NAME}.mjs` },
      exports: { ".": "./sdk/index.mjs" },
      files: ["bin", "sdk", "openapi.json", "manifest.json", "api-graph.json", "README.md"],
      engines: { node: ">=20" },
      private: true,
    }, null, 2) + "\n");
  }

  console.log(`generated ${out}`);
  console.log(`operations: ${operations.length} (live-probed: ${manifest.primaryEndpoints.length}, schema-only: ${manifest.dependencyEndpoints.length})`);
  console.log("no credentials exported");
  if (outputMode === "cli") console.log(`cli ${CLI_NAME}`);
  return { out, manifest, spec };
}

// Plane 的资源是严格层级的：workspace slug → project id → 各子资源 id。
// 边描述的是"下一步调用需要的 id 从哪个响应字段来"，全部来自 schema 中的路径参数结构。
function createPlaneApiGraph(operations) {
  const has = id => operations.some(o => o.operationId === id);
  const edges = [
    { from: "get_current_user", to: "list_projects", sourceSelector: "$.workspace slug 由用户自行提供或从 Plane UI 读取", description: "确认凭据有效后进入工作区" },
    { from: "list_projects", to: "list_work_items", sourceSelector: "$.results[].id → {project_id}", description: "项目 id driving 后续所有项目级资源" },
    { from: "list_projects", to: "list_states", sourceSelector: "$.results[].id → {project_id}", description: "创建工作项前取状态字典" },
    { from: "list_projects", to: "list_labels", sourceSelector: "$.results[].id → {project_id}", description: "创建工作项前取标签字典" },
    { from: "list_states", to: "create_work_item", sourceSelector: "$.results[].id → body.state", description: "状态 id 作为写入字段" },
    { from: "list_labels", to: "create_work_item", sourceSelector: "$.results[].id → body.labels[]", description: "标签 id 作为写入字段" },
    { from: "list_work_items", to: "list_work_item_comments", sourceSelector: "$.results[].id → {issue_id}", description: "工作项 id 进入评论/附件/链接/活动" },
    { from: "list_work_items", to: "list_work_item_links", sourceSelector: "$.results[].id → {issue_id}" },
    { from: "list_work_items", to: "list_work_item_activities", sourceSelector: "$.results[].id → {issue_id}" },
    { from: "list_projects", to: "list_cycles", sourceSelector: "$.results[].id → {project_id}" },
    { from: "list_projects", to: "list_modules", sourceSelector: "$.results[].id → {project_id}" },
  ].filter(edge => has(edge.from) && has(edge.to));
  return { target: TARGET, scope: SCOPE, rootOperationId: "get_current_user", nodes: operations, edges };
}

function createPlaneReadme({ manifest, discovery, operations, outputMode }) {
  const byTag = operations.reduce((acc, op) => {
    acc[op.tag] = (acc[op.tag] || 0) + 1;
    return acc;
  }, {});
  const tagLines = Object.entries(byTag).sort((a, b) => b[1] - a[1]).map(([tag, count]) => `| ${tag} | ${count} |`).join("\n");
  const install = outputMode === "cli"
    ? `## 安装\n\n\`\`\`bash\ncd ${manifest.cliName ? "<生成目录>" : "."}\nnpm link          # 或 npm install -g .\n\`\`\`\n\n未安装时也可直接运行 \`node bin/${manifest.cliName}.mjs\`。\n\n`
    : "";

  return `# ${manifest.instance?.product || "Plane"} REST API v1

由 ${manifest.instance?.product || "Plane"} ${manifest.instance?.release || ""} 自托管实例导出，共 ${operations.length} 个操作、${Object.keys(byTag).length} 个资源分组。

实例地址 ${manifest.instance?.publicBaseUrl}，API 前缀 ${manifest.instance?.apiPrefix}。

## 证据来源

${discovery.sources.map(s => `- **${s.kind}** — ${s.how}${s.result ? `；结果：${s.result}` : ""}${s.note ? `\n  ${s.note}` : ""}`).join("\n")}

OpenAPI 文档本身由实例内置的 drf-spectacular 生成，未人工改写路径或字段，只修正了 servers 并补充 \`x-observation\` 证据标注。${manifest.primaryEndpoints.length} 个操作经过 live 探测（无认证 401、无效 key 403），其余 ${manifest.dependencyEndpoints.length} 个仅有 schema 定义，未在线执行。

## 认证

请求头 \`${manifest.auth.header}\`。获取方式：${manifest.auth.howToObtain}。

凭据不写入本目录任何文件。运行时通过环境变量提供：

\`\`\`bash
export PLANE_BASE_URL=${manifest.instance?.publicBaseUrl}
export PLANE_API_KEY=<你的 api key>
\`\`\`

${install}## 资源分组

| 分组 | 操作数 |
| --- | --- |
${tagLines}

## 用法

\`\`\`bash
${manifest.cliName || "lov-plane-cli"} help                                    # 按分组列出全部命令
${manifest.cliName || "lov-plane-cli"} list-projects -w <workspace-slug>
${manifest.cliName || "lov-plane-cli"} list-work-items -w <slug> -p <project-id>
${manifest.cliName || "lov-plane-cli"} create-work-item -w <slug> -p <project-id> --data '{"name":"新任务"}'
${manifest.cliName || "lov-plane-cli"} list-projects --help                    # 查看单个命令的参数
${manifest.cliName || "lov-plane-cli"} list-projects -w <slug> --dry-run       # 只打印请求，不发出
\`\`\`

命令表在启动时由随包的 \`openapi.json\` 构建，operationId 转为 kebab-case 即命令名，因此 ${operations.length} 个操作全部可直接调用，无需为每个端点写代码。路径参数可按顺序作为位置参数传入，也可用同名选项；\`-w\`/\`-p\`/\`--id\` 是 \`slug\`/\`project_id\`/\`pk\` 的别名。请求体用 \`--data '<json>'\` 或 \`--data @file.json\`。

## 调用顺序

\`api-graph.json\` 记录资源层级：workspace slug → project id → 工作项/周期/模块/状态/标签 id。创建工作项前先用 \`list-states\` 和 \`list-labels\` 取字典 id。

## 限制

${discovery.limitations.map(l => `- ${l}`).join("\n")}

## SDK

\`sdk/index.mjs\` 导出 \`PlaneClient\`，包含常用入口和通用 \`request(method, path, {query, body})\`。凭据经构造参数或 \`PLANE_API_KEY\` 在内存中传入，不落盘。
`;
}
