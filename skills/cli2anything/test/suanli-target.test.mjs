import test from "node:test";
import assert from "node:assert/strict";
import { execFile, spawnSync } from "node:child_process";
import { generateKeyPairSync, privateDecrypt, constants, verify } from "node:crypto";
import { mkdtemp, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { SuanliApiError, SuanliClient, buildSigningString, encryptBody } from "../src/suanli-client.mjs";
import { createSuanliOpenapi, deriveOperationId, isWriteOperation } from "../src/suanli-target.mjs";

const run = promisify(execFile);
const ROOT = resolve(fileURLToPath(new URL("../", import.meta.url)));
// 测试用的占位凭据；生成物与 dry-run 输出里都不得出现它。
const PLACEHOLDER_TOKEN = "placeholder-token-for-tests";
const KEYCHAIN_TOKEN = "keychain-placeholder-for-tests";
const header = (name, schema = { type: "string" }, extra = {}) => ({ name, in: "header", required: true, schema, ...extra });
const table = (encrypt = "否") => `| 当前版本 | 旧版本 | 是否需要加密 | 是否需要加签 |\n| --- | --- | --- | --- |\n| v1.0.0 | - | ${encrypt} | 是 |`;
const authHeaders = [header("token", { type: "string" }, { example: "" }), header("timestamp", { type: "number" }), header("version", { type: "number" }, { example: "1.0.0" })];
const doc = (apifoxId, folder, path, method, op) => ({
  apifoxId,
  title: op.summary,
  folder: `共绩算力 Open API/${folder}`,
  url: `https://s.apifox.cn/share/${apifoxId}.md`,
  sha256: "0".repeat(64),
  fragment: {
    openapi: "3.0.1",
    paths: { [path]: { [method]: { "x-apifox-folder": `共绩算力 Open API/${folder}`, security: [], ...op } } },
    components: {
      schemas: { IResponse: { type: "object", properties: { code: { type: "string" }, message: { type: "string", nullable: true } }, "x-apifox-orders": ["code", "message"] } },
      securitySchemes: { AdminAuth: { type: "jwt", scheme: "bearer" }, ApiKeyAuth: { type: "apikey", in: "header", name: "token" } },
    },
  },
});

const fragments = {
  schema: "suanli-apifox-fragments/v1",
  shareUrl: "https://s.apifox.cn/share",
  llmsTxt: { url: "https://s.apifox.cn/share/llms.txt", sha256: "1".repeat(64) },
  fetchedAt: "2026-11-19T00:00:00+00:00",
  redaction: { count: 0, rule: "test" },
  docs: [
    doc("api-1", "资源", "/api/deployment/resource/search", "get", {
      summary: "获取设备资源列表",
      description: `${table()}\n获取设备资源列表。`,
      parameters: [{ name: "device_type", in: "query", required: false, schema: { type: "string", enum: ["GpuDevice"] } }, ...authHeaders],
      responses: { 200: { description: "", content: { "application/json": { schema: { $ref: "#/components/schemas/IResponse" } } } } },
    }),
    doc("api-2", "弹性部署服务任务", "/api/deployment/task/create", "post", {
      summary: "任务创建接口",
      description: `${table()}\nresources.item.mark 需要从 [获取设备资源列表](https://s.apifox.cn/share/api-1.md) 获取`,
      parameters: authHeaders,
      requestBody: { content: { "application/json": { schema: { type: "object", properties: { task_name: { type: "string" }, points: { type: "number", nullable: true } } } } } },
      responses: { 200: { description: "" } },
    }),
    doc("api-3", "存储/对象存储", "/api/storage/encrypt/check", "post", {
      summary: "校验对象存储连接",
      description: table("是"),
      parameters: [...authHeaders, { name: "sign_str", in: "header", required: false, schema: { type: "string" } }],
      requestBody: { content: { "application/json": { schema: { type: "object" } } } },
      responses: { 200: { description: "" } },
    }),
    doc("api-4", "费用", "/api/storage/billing/get_billing_record", "get", {
      summary: "共享存储卷-计费查询接口",
      description: table(),
      parameters: [{ name: "storage_type", in: "query", required: true, schema: { type: "string", const: "ShareStorage" } }, ...authHeaders],
      responses: { 200: { description: "" } },
    }),
    doc("api-5", "费用", "/api/storage/billing/get_billing_record", "get", {
      summary: "对象存储加速-计费查询接口",
      description: table(),
      parameters: [{ name: "storage_type", in: "query", required: true, schema: { type: "string", const: "Juicefs" } }, ...authHeaders],
      responses: { 200: { description: "" } },
    }),
    doc("api-6", "裸金属/订单列表", "/api/output/v2/device_order/get_order_list_v2", "post", {
      summary: "订单列表",
      description: table(),
      requestBody: { content: { "application/json": { schema: { type: "object" } } } },
      responses: { 200: { description: "" } },
    }),
  ],
};

const discovery = {
  target: "suanli.cn",
  scope: "openapi-and-llm",
  authorized: true,
  authorization: "public official docs",
  observedAt: "2026-11-19T00:00:00Z",
  evidenceFiles: { apifoxFragments: "fragments.json" },
  sources: [{ kind: "vendor-apifox-openapi", url: "https://s.apifox.cn/share" }],
  auth: {
    openapi: { baseUrl: "https://openapi.suanli.cn", howToObtain: "控制台 API 密钥管理" },
    llm: { baseUrl: "https://api.suanli.cn/v1", howToObtain: "控制台模型页" },
  },
  llmOperations: [{ method: "get", path: "/v1/models", operationId: "llmListModels", summary: "模型列表", responses: { 200: { description: "ok" } }, evidence: [{ url: "https://docs.suanli.cn/llm/quickstart" }] }],
  workflowEdges: [{ from: "GET /v1/models", to: "GET /api/deployment/resource/search", basis: "docs", sourceSelector: "x" }],
  docConflicts: ["msg vs message"],
  limitations: ["未实测"],
};

test("suanli adapter rejects unauthorized discovery or missing vendor fragments", () => {
  assert.throws(() => createSuanliOpenapi({ ...discovery, authorized: false }, fragments), /authorized suanli\.cn/);
  assert.throws(() => createSuanliOpenapi({ ...discovery, auth: { openapi: {} } }, fragments), /Incomplete suanli discovery/);
  assert.throws(() => createSuanliOpenapi(discovery, { ...fragments, schema: "other" }), /vendor Apifox fragments/);
});

test("suanli adapter normalizes vendor fragments to OpenAPI 3.1 without inventing operations", () => {
  const { spec } = createSuanliOpenapi(discovery, fragments);
  assert.equal(spec.openapi, "3.1.0");
  const vendorKeys = new Set(fragments.docs.flatMap(d => Object.entries(d.fragment.paths).flatMap(([p, item]) => Object.keys(item).map(m => `${m} ${p}`))));
  const opKeys = Object.entries(spec.paths).flatMap(([p, item]) => Object.keys(item).filter(m => m !== "servers").map(m => `${m} ${p}`));
  assert.deepEqual(new Set(opKeys), new Set([...vendorKeys, "get /v1/models"]), "只能包含官方片段与文档里的接口");

  const search = spec.paths["/api/deployment/resource/search"].get;
  assert.equal(search.operationId, "deploymentResourceSearch");
  assert.equal(search["x-observation"], "documented-apifox-openapi");
  assert.equal(search["x-evidence"].basis, "文档");
  assert.equal(search["x-evidence"].live, false);
  assert.deepEqual(search.security, [{ ApiKeyAuth: [] }]);
  assert.equal(search.parameters.some(p => p.name === "token"), false, "token 头改由 securitySchemes 表达");
  const version = search.parameters.find(p => p.name === "version");
  assert.equal(version.schema.type, "string", "官方误写为 number 的 version 头统一为字符串");
  assert.equal(search.parameters.find(p => p.name === "sign_str").required, false);
  assert.equal(search["x-write-operation"], undefined);

  const create = spec.paths["/api/deployment/task/create"].post;
  assert.match(create["x-write-operation"], /未在线执行/);
  assert.deepEqual(create.requestBody.content["application/json"].schema.properties.points.type, ["number", "null"]);
  const contract = JSON.stringify({ ...spec, "x-discovery": undefined });
  assert.equal(contract.includes('"nullable"'), false);
  assert.equal(contract.includes('"x-apifox-orders"'), false, "Apifox 编辑器元数据不进入契约");

  const check = spec.paths["/api/storage/encrypt/check"].post;
  assert.equal(check["x-suanli-auth"].encryption, true);
  assert.equal(check["x-write-operation"], undefined, "校验连接是只读操作");

  const billing = spec.paths["/api/storage/billing/get_billing_record"].get;
  assert.equal(billing["x-evidence"].sources.length, 2, "同一 method + path 的多份接口页合并为一个操作");
  assert.deepEqual(billing.parameters.find(p => p.name === "storage_type").schema.enum, ["ShareStorage", "Juicefs"]);

  const order = spec.paths["/api/output/v2/device_order/get_order_list_v2"].post;
  assert.equal(order["x-suanli-auth"].authHeaders, "inferred-from-overview");
  assert.ok(order.parameters.find(p => p.name === "timestamp")["x-inferred-from"]);

  const models = spec.paths["/v1/models"];
  assert.equal(models.servers[0].url, "https://api.suanli.cn");
  assert.equal(models.get["x-observation"], "documented-docs-example");
  assert.deepEqual(Object.keys(spec.components.securitySchemes), ["ApiKeyAuth", "LlmBearer"]);
  assert.equal(spec.components.securitySchemes.ApiKeyAuth.type, "apiKey");
});

test("suanli operation helpers derive stable ids and classify writes", () => {
  assert.equal(deriveOperationId("/api/storage/nas/v1/pre-create"), "storageNasV1PreCreate");
  assert.equal(isWriteOperation("post", "/api/storage/s3/bucket/list"), false);
  assert.equal(isWriteOperation("post", "/api/output/v2/device-output/page_list_product_single_v2"), false);
  assert.equal(isWriteOperation("post", "/api/deployment/task/change_points"), true);
  assert.equal(isWriteOperation("post", "/api/storage/nas/v1/sftp/obtain"), true);
  assert.equal(isWriteOperation("get", "/api/deployment/task/search"), false);
});

test("SuanliClient signs path?query exactly as sent and encrypts before signing", async () => {
  const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048, publicKeyEncoding: { type: "spki", format: "pem" }, privateKeyEncoding: { type: "pkcs8", format: "pem" } });
  assert.equal(buildSigningString({ path: "/a", version: "1.0.0", timestamp: "1", token: "t" }), "/a\n1.0.0\n1\nt\n");
  const client = new SuanliClient({ token: PLACEHOLDER_TOKEN, privateKey, platformPublicKey: publicKey, now: () => 1770194570564, env: {} });

  const get = client.prepare("GET", "/api/deployment/task/search", { query: { page: 1, page_size: 5 } });
  assert.equal(get.url, "https://openapi.suanli.cn/api/deployment/task/search?page=1&page_size=5");
  assert.equal(get.init.body, undefined);
  const signed = buildSigningString({ path: "/api/deployment/task/search?page=1&page_size=5", version: "1.0.0", timestamp: "1770194570564", token: PLACEHOLDER_TOKEN, body: "" });
  assert.ok(verify("sha256", Buffer.from(signed), publicKey, Buffer.from(get.init.headers.sign_str, "base64")));

  const payload = { storage_name: "演示", dir: "d".repeat(400) };
  const post = client.prepare("POST", "/api/storage/encrypt/check", { body: payload, encryption: true });
  assert.equal(post.encrypted, true);
  const cipher = Buffer.from(post.init.body, "base64");
  assert.equal(cipher.length / 256, Math.ceil(Buffer.byteLength(JSON.stringify(payload)) / 244), "按 244 字节分段");
  const parts = [];
  for (let i = 0; i < cipher.length; i += 256) parts.push(privateDecrypt({ key: privateKey, padding: constants.RSA_PKCS1_PADDING }, cipher.subarray(i, i + 256)));
  assert.equal(Buffer.concat(parts).toString("utf8"), JSON.stringify(payload));
  const postSigned = buildSigningString({ path: "/api/storage/encrypt/check", version: "1.0.0", timestamp: "1770194570564", token: PLACEHOLDER_TOKEN, body: post.init.body });
  assert.ok(verify("sha256", Buffer.from(postSigned), publicKey, Buffer.from(post.init.headers.sign_str, "base64")), "签名基于加密后的 Base64");
  assert.equal(encryptBody(publicKey, "x").length > 0, true);

  assert.throws(() => new SuanliClient({ token: PLACEHOLDER_TOKEN, env: {} }).prepare("POST", "/api/storage/encrypt/check", { body: {}, encryption: true }), /RSA 模式/);
  const tokenOnly = new SuanliClient({ token: PLACEHOLDER_TOKEN, env: {} }).prepare("GET", "/api/x");
  assert.equal(tokenOnly.init.headers.sign_str, undefined);
  assert.equal(tokenOnly.mode, "token");
});

test("SuanliClient surfaces gateway envelope errors instead of returning them as data", async () => {
  const replies = [
    { code: "A003", message: "token expired", data: null },
    { code: "0000", message: "success", data: { ok: true } },
  ];
  const client = new SuanliClient({ token: PLACEHOLDER_TOKEN, env: {}, fetch: async () => new Response(JSON.stringify(replies.shift()), { status: 200 }) });
  const error = await client.request("GET", "/api/deployment/resource/search").catch(e => e);
  assert.ok(error instanceof SuanliApiError);
  assert.equal(error.code, "A003");
  assert.deepEqual(await client.request("GET", "/api/deployment/resource/search"), { ok: true });
  await assert.rejects(() => new SuanliClient({ env: {} }).request("GET", "/api/x"), /需要 token/);
  await assert.rejects(() => new SuanliClient({ env: {} }).listModels(), /SUANLI_LLM_API_KEY/);
});

test("suanli wrapper dispatch produces bundle, Swagger and a schema-driven CLI without credentials", async () => {
  const dir = await mkdtemp(join(tmpdir(), "suanli-bundle-"));
  try {
    await writeFile(join(dir, "fragments.json"), JSON.stringify(fragments));
    await writeFile(join(dir, "discovery.json"), JSON.stringify(discovery));
    const out = join(dir, "bundle");
    await run(process.execPath, ["bin/cli2anything.mjs", "suanli.cn", "--output", "bundle,swagger,cli", "--no-link", "--no-open", "--discovery", join(dir, "discovery.json"), "--out", out], { cwd: ROOT });

    const manifest = JSON.parse(await readFile(join(out, "manifest.json"), "utf8"));
    assert.equal(manifest.target, "suanli.cn");
    assert.equal(manifest.operationCount, 6);
    assert.equal(manifest.liveVerified, 0);
    assert.equal(manifest.secretsIncluded, false);
    const graph = JSON.parse(await readFile(join(out, "api-graph.json"), "utf8"));
    assert.ok(graph.edges.some(e => e.from === "deploymentResourceSearch" && e.to === "deploymentTaskCreate" && e.basis === "apifox-description-link"));
    assert.ok(graph.edges.some(e => e.from === "llmListModels" && e.basis === "docs"));

    for (const file of ["sdk/index.mjs", "bin/lov-suanli-cli.mjs", "swagger/server.mjs"]) await run(process.execPath, ["--check", join(out, file)]);
    for (const file of ["swagger/index.html", "swagger/drilldown.html", "README.md", "openapi.json"]) assert.ok((await readFile(join(out, file), "utf8")).length > 0);
    assert.match(await readFile(join(out, "sdk/index.mjs"), "utf8"), /"deploymentTaskCreate": \{/, "SDK 内嵌完整操作表");

    // SUANLI_KEYCHAIN=0：不让本机钥匙串里的真实密钥进入测试。
    const env = { PATH: process.env.PATH, SUANLI_KEYCHAIN: "0" };
    const cli = join(out, "bin/lov-suanli-cli.mjs");
    const help = await run(process.execPath, [cli, "help"], { env });
    const commands = help.stdout.split("\n").filter(line => /^ {4}[a-z0-9-]+ +(GET|POST|PUT|PATCH|DELETE) /.test(line));
    assert.equal(commands.length, manifest.operationCount, "命令数与操作数一致");

    const dry = JSON.parse((await run(process.execPath, [cli, "deployment-resource-search", "--device-type", "GpuDevice", "--dry-run"], { env: { ...env, SUANLI_TOKEN: PLACEHOLDER_TOKEN } })).stdout);
    assert.equal(dry.url, "https://openapi.suanli.cn/api/deployment/resource/search?device_type=GpuDevice");
    assert.equal(dry.headers.token, "<已提供>");
    assert.equal(JSON.stringify(dry).includes(PLACEHOLDER_TOKEN), false, "dry-run 不得回显凭据");

    const refused = spawnSync(process.execPath, [cli, "deployment-task-create", "--data", '{"task_name":"x"}'], { env: { ...env, SUANLI_TOKEN: PLACEHOLDER_TOKEN }, encoding: "utf8" });
    assert.equal(refused.status, 3, "写操作没有 --confirm-write 必须拒绝");
    await assert.rejects(() => run(process.execPath, [cli, "deployment-resource-search", "--nope", "1", "--dry-run"], { env }), error => /未知参数/.test(error.stderr));

    if (process.platform === "darwin") {
      // 用假的 security 命令模拟钥匙串：只对 suanli-token 返回占位密钥。
      const fakeBin = join(dir, "fake-bin");
      await mkdir(fakeBin);
      await writeFile(join(fakeBin, "security"), `#!/bin/sh\n[ "$3" = "suanli-token" ] && echo ${KEYCHAIN_TOKEN} && exit 0\nexit 44\n`, { mode: 0o755 });
      const kcEnv = { PATH: `${fakeBin}:${process.env.PATH}` };
      const fromKeychain = JSON.parse((await run(process.execPath, [cli, "deployment-resource-search", "--dry-run"], { env: kcEnv })).stdout);
      assert.equal(fromKeychain.credentialSource, "keychain");
      assert.equal(fromKeychain.headers.token, "<已提供>");
      assert.equal(JSON.stringify(fromKeychain).includes(KEYCHAIN_TOKEN), false, "dry-run 不得回显钥匙串里的密钥");
      const envWins = JSON.parse((await run(process.execPath, [cli, "deployment-resource-search", "--dry-run"], { env: { ...kcEnv, SUANLI_TOKEN: PLACEHOLDER_TOKEN } })).stdout);
      assert.equal(envWins.credentialSource, "env", "环境变量优先于钥匙串");
      const disabled = JSON.parse((await run(process.execPath, [cli, "deployment-resource-search", "--dry-run"], { env: { ...kcEnv, SUANLI_KEYCHAIN: "0" } })).stdout);
      assert.equal(disabled.hasCredential, false);
      const llmMissing = JSON.parse((await run(process.execPath, [cli, "llm-list-models", "--dry-run"], { env: kcEnv })).stdout);
      assert.equal(llmMissing.hasCredential, false, "大模型 Key 用单独的钥匙串条目");
    }

    const files = await listFiles(out);
    for (const file of files) assert.equal((await readFile(file, "utf8")).includes(PLACEHOLDER_TOKEN), false, `${file} 不得包含凭据`);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

test("suanli discovery script redacts credential-looking examples from vendor pages", async t => {
  if (spawnSync("python3", ["-c", "import yaml"]).status !== 0) return t.skip("PyYAML not installed");
  const dir = await mkdtemp(join(tmpdir(), "suanli-discover-"));
  try {
    const share = "https://s.apifox.cn/share";
    const tokenLike = `${"ab12cd34"}-${"ab12"}-${"ab12"}-${"ab12"}-${"ab12cd34ef56"}-20260101000000`;
    await mkdir(join(dir, "pages"));
    await writeFile(join(dir, "pages/llms.txt"), `# x\n\n## API Docs\n- 共绩算力 Open API > 资源 [获取设备资源列表](${share}/api-1.md): x\n`);
    await writeFile(join(dir, "pages/api-1.md"), [
      "# 获取设备资源列表", "", "## OpenAPI Specification", "", "```yaml",
      "openapi: 3.0.1", "paths:", "  /api/deployment/resource/search:", "    get:", "      summary: 获取设备资源列表",
      "      description: see " + tokenLike, "      parameters:", "        - name: token", "          in: header", "          required: true",
      "          example: " + tokenLike, "          schema:", "            type: string", "      responses: {}", "```", "",
    ].join("\n"));
    const out = join(dir, "fragments.json");
    const result = spawnSync("python3", [join(ROOT, "scripts/suanli_discover.py"), "--offline-dir", join(dir, "pages"), "--share-id", "share", "--out", out], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr);
    const text = await readFile(out, "utf8");
    assert.equal(text.includes(tokenLike), false, "形如 API 密钥的值必须被清除");
    const evidence = JSON.parse(text);
    assert.equal(evidence.docs.length, 1);
    assert.ok(evidence.redaction.count >= 2);
    assert.equal(evidence.docs[0].fragment.paths["/api/deployment/resource/search"].get.parameters[0].example, "");
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});

async function listFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = await Promise.all(entries.map(entry => (entry.isDirectory() ? listFiles(join(dir, entry.name)) : [join(dir, entry.name)])));
  return files.flat();
}
