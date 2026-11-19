import test from "node:test";
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { PlaneClient } from "../src/plane-client.mjs";
import { createPlaneOpenapi, generatePlaneBundle } from "../src/plane-target.mjs";

const run = promisify(execFile);
const ROOT = resolve(fileURLToPath(new URL("../", import.meta.url)));
const DISCOVERY = join(ROOT, "artifacts/plane-discovered.json");
const SCHEMA = join(ROOT, "artifacts/plane-schema.raw.json");

const evidence = {
  target: "localhost",
  scope: "plane-rest-api-v1",
  authorized: true,
  authorization: "user-owned self-hosted instance",
  observedAt: "2026-09-08T18:00:00Z",
  instance: { product: "Plane", release: "v1.4.2", publicBaseUrl: "http://localhost", containerServerUrl: "http://api:8000", apiPrefix: "/api/v1" },
  sources: [{ kind: "vendor-generated-schema", how: "manage.py spectacular" }],
  auth: { scheme: "ApiKeyAuthentication", in: "header", name: "X-API-Key", howToObtain: "Settings → API tokens" },
  operations: [{ method: "GET", path: "/api/v1/users/me/", operationId: "get_current_user", tags: ["Users"] }],
  probes: [{ tag: "Users", operationId: "get_current_user", path: "/api/v1/users/me/", probedPath: "/api/v1/users/me/", statusNoAuth: "401", statusInvalidKey: "403" }],
  limitations: ["未执行写操作"],
};

const rawSchema = {
  openapi: "3.0.3",
  info: { title: "The Plane REST API", version: "0.0.1" },
  servers: [{ url: "http://localhost:8000", description: "Local" }],
  paths: {
    "/api/v1/users/me/": { get: { operationId: "get_current_user", tags: ["Users"], summary: "Get current user", responses: { 200: { description: "ok" } } } },
    "/api/v1/workspaces/{slug}/projects/": { post: { operationId: "create_project", tags: ["Projects"], summary: "Create project", responses: { 201: { description: "created" } } } },
  },
  components: { schemas: { User: { type: "object" } }, securitySchemes: { ApiKeyAuthentication: { type: "apiKey", in: "header", name: "X-API-Key" } } },
};

test("Plane adapter rejects unauthorized or incomplete discovery evidence", () => {
  assert.throws(() => createPlaneOpenapi({ ...evidence, authorized: false }, rawSchema), /authorized plane-rest-api-v1 discovery/);
  assert.throws(() => createPlaneOpenapi({ ...evidence, scope: "other" }, rawSchema), /authorized plane-rest-api-v1 discovery/);
  assert.throws(() => createPlaneOpenapi({ ...evidence, probes: [] }, rawSchema), /Incomplete Plane discovery/);
  assert.throws(() => createPlaneOpenapi({ ...evidence, auth: {} }, rawSchema), /Incomplete Plane discovery/);
  assert.throws(() => createPlaneOpenapi(evidence, { paths: {} }), /vendor-generated schema/);
});

test("Plane adapter corrects servers and grades every operation by evidence", () => {
  const spec = createPlaneOpenapi(evidence, rawSchema);
  assert.equal(spec.servers[0].url, "http://localhost", "对外地址必须排在容器内地址之前");
  assert.equal(spec.servers[1].url, "http://api:8000");
  assert.equal(spec.paths["/api/v1/users/me/"].get["x-observation"], "live-probe-401-403");
  assert.equal(spec.paths["/api/v1/users/me/"].get["x-probe"].statusInvalidKey, "403");
  assert.equal(spec.paths["/api/v1/workspaces/{slug}/projects/"].post["x-observation"], "vendor-generated-schema");
  assert.match(spec.paths["/api/v1/workspaces/{slug}/projects/"].post["x-write-operation"], /未在线执行/);
  assert.equal(spec["x-discovery"].sources.length, 1);
  // 路径与字段来自 vendor schema，adapter 不得增删接口。
  assert.deepEqual(Object.keys(spec.paths), Object.keys(rawSchema.paths));
});

test("PlaneClient requires a key, preserves API errors, and never inlines credentials", async () => {
  await assert.rejects(() => new PlaneClient({ apiKey: undefined, baseUrl: "http://localhost" }).getCurrentUser(), /needs? apiKey|需要 apiKey/);
  const calls = [];
  const client = new PlaneClient({
    baseUrl: "http://localhost/",
    apiKey: "test-key",
    fetch: async (url, options) => {
      calls.push({ url: url.toString(), options });
      return new Response(JSON.stringify({ detail: "Given API token is not valid" }), { status: 403, statusText: "Forbidden" });
    },
  });
  const error = await client.listProjects("my ws", { per_page: 50 }).catch(e => e);
  assert.equal(error.status, 403);
  assert.deepEqual(error.body, { detail: "Given API token is not valid" });
  assert.equal(calls[0].url, "http://localhost/api/v1/workspaces/my%20ws/projects/?per_page=50", "slug 必须转义且不产生双斜杠");
  assert.equal(calls[0].options.headers["X-API-Key"], "test-key");
  const source = await readFile(new URL("../src/plane-client.mjs", import.meta.url), "utf8");
  assert.equal(/apiKey\s*=\s*"[A-Za-z0-9]{8,}"/.test(source), false, "SDK 源码不得内联凭据");
});

test("Plane wrapper dispatch produces a schema-driven CLI bundle without credentials", async () => {
  const dir = await mkdtemp(join(tmpdir(), "plane-bundle-"));
  try {
    const out = join(dir, "lov-plane-cli");
    const { manifest } = await generatePlaneBundle(["--output", "cli", "--discovery", DISCOVERY, "--schema", SCHEMA, "--out", out]);
    assert.equal(manifest.adapter, "plane");
    assert.equal(manifest.cliName, "lov-plane-cli");
    assert.equal(manifest.secretsIncluded, false);
    assert.equal(manifest.primaryEndpoints.length + manifest.dependencyEndpoints.length, manifest.operationCount);
    assert.ok(manifest.operationCount > 100, "应覆盖实例导出的全部操作");

    const spec = JSON.parse(await readFile(join(out, "openapi.json"), "utf8"));
    const graph = JSON.parse(await readFile(join(out, "api-graph.json"), "utf8"));
    assert.equal(spec.servers[0].url, "http://localhost");
    assert.ok(graph.edges.length > 0, "api-graph 必须记录资源层级");
    assert.equal(graph.rootOperationId, "get_current_user");

    // CLI 必须由 openapi.json 驱动，命令数与操作数一致。
    const help = await run("node", [join(out, "bin/lov-plane-cli.mjs"), "help"]);
    const commands = help.stdout.split("\n").filter(line => /^ {4}[a-z0-9-]+ +(GET|POST|PATCH|PUT|DELETE) /.test(line));
    assert.equal(commands.length, manifest.operationCount);

    // dry-run 解析别名与位置参数，且在无凭据时不发出请求。
    const dry = await run("node", [join(out, "bin/lov-plane-cli.mjs"), "list-work-items", "-w", "ws", "-p", "pid", "--per-page", "50", "--dry-run"], { env: { ...process.env, PLANE_API_KEY: "", PLANE_CLI_CONFIG: join(dir, "missing-config.json") } });
    const parsed = JSON.parse(dry.stdout);
    assert.equal(parsed.url, "http://localhost/api/v1/workspaces/ws/projects/pid/issues/?per_page=50");
    assert.equal(parsed.hasApiKey, false);

    // 未知参数必须报错，避免静默丢弃。
    await assert.rejects(
      () => run("node", [join(out, "bin/lov-plane-cli.mjs"), "list-projects", "-w", "ws", "--not-a-param", "x", "--dry-run"]),
      error => /未知参数/.test(error.stderr));

    const files = ["manifest.json", "openapi.json", "api-graph.json", "README.md", "package.json", "sdk/index.mjs", "bin/lov-plane-cli.mjs"];
    for (const file of files) {
      const text = await readFile(join(out, file), "utf8");
      assert.equal(/X-API-Key:\s*[A-Za-z0-9]{12,}/.test(text), false, `${file} 不得包含真实凭据`);
    }
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
});
