import test from "node:test";
import assert from "node:assert/strict";
import { ZenMuxClient, ZenMuxApiError } from "../src/zenmux-client.mjs";

function mockFetch(handler) {
  const calls = [];
  const fetchImpl = async (url, init = {}) => {
    calls.push({ url, init });
    const result = await handler(url, init);
    return {
      ok: result.status >= 200 && result.status < 300,
      status: result.status,
      headers: {
        get(name) {
          return name.toLowerCase() === "content-type" ? "application/json" : "";
        }
      },
      async json() {
        return result.body;
      },
      async text() {
        return JSON.stringify(result.body);
      }
    };
  };
  return { fetchImpl, calls };
}

test("listLogs posts the observed ZenMux dashboard list shape", async () => {
  const { fetchImpl, calls } = mockFetch(() => ({ status: 200, body: { data: [] } }));
  const client = new ZenMuxClient({ apiKey: "test-key", fetchImpl, baseUrl: "https://example.test" });

  await client.listLogs({
    startTime: 1,
    stopTime: 2,
    pageNo: 3,
    pageSize: 4,
    requestId: "req_1",
    modelSlugs: ["openai/gpt-4o"],
    providerSlugs: ["openai"],
    finishReasons: ["stop"]
  });

  assert.equal(calls[0].url, "https://example.test/api/api_key/activity");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(calls[0].init.headers.Authorization, "Bearer test-key");
  assert.equal(calls[0].init.headers["x-api-version"], "2026-04-20");
  assert.deepEqual(JSON.parse(calls[0].init.body), {
    apiKeys: [],
    startTime: 1,
    stopTime: 2,
    pageNo: 3,
    pageSize: 4,
    requestId: "req_1",
    modelSlugs: ["openai/gpt-4o"],
    providerSlugs: ["openai"],
    finishReasons: ["stop"]
  });
});

test("dashboard requests can include console cookie and configurable csrf header", async () => {
  const { fetchImpl, calls } = mockFetch(() => ({ status: 200, body: { data: [] } }));
  const client = new ZenMuxClient({
    fetchImpl,
    baseUrl: "https://example.test",
    cookie: "session=abc",
    csrfToken: "csrf-123",
    csrfHeaderName: "x-custom-csrf"
  });

  await client.listLogs({ pageSize: 1 });

  assert.equal(calls[0].init.headers.Cookie, "session=abc");
  assert.equal(calls[0].init.headers["x-custom-csrf"], "csrf-123");
});

test("dependency helpers wrap API key and finish reason endpoints", async () => {
  const { fetchImpl, calls } = mockFetch(() => ({ status: 200, body: { data: [] } }));
  const client = new ZenMuxClient({ apiKey: "test-key", fetchImpl, baseUrl: "https://example.test" });

  await client.listApiKeys();
  await client.listAllApiKeys();
  await client.getFinishReasons();

  assert.deepEqual(calls.map((call) => call.url), [
    "https://example.test/api/api_key/list",
    "https://example.test/api/api_key/list_all",
    "https://example.test/api/api_key/finish_reasons"
  ]);
  assert.ok(calls.every((call) => call.init.method === "GET"));
});

test("getLogDetail combines activity, metadata, request, and response payload calls", async () => {
  const { fetchImpl, calls } = mockFetch((url) => {
    if (url.includes("/activity/req_1")) return { status: 200, body: { requestId: "req_1" } };
    if (url.includes("/management/generation")) return { status: 200, body: { generationId: "req_1" } };
    if (url.includes("/generation/request")) return { status: 200, body: { body: { messages: [] } } };
    if (url.includes("/generation/response")) return { status: 200, body: { body: { content: "ok" } } };
    return { status: 404, body: { error: "not found" } };
  });
  const client = new ZenMuxClient({ apiKey: "test-key", fetchImpl, baseUrl: "https://example.test" });

  const detail = await client.getLogDetail("req_1");

  assert.equal(detail.requestId, "req_1");
  assert.equal(calls.length, 4);
  assert.ok(calls.some((call) => call.url === "https://example.test/api/api_key/activity/req_1?id=req_1"));
  assert.ok(calls.some((call) => call.url === "https://example.test/api/v1/management/generation?id=req_1"));
  assert.ok(calls.some((call) => call.url === "https://example.test/api/v1/generation/request?id=req_1&type=userRequest"));
  assert.ok(calls.some((call) => call.url === "https://example.test/api/v1/generation/response?id=req_1&type=userResponse"));
});

test("getLogDetail falls back to the legacy generation endpoint", async () => {
  const { fetchImpl, calls } = mockFetch((url) => {
    if (url.includes("/activity/req_1")) return { status: 200, body: { requestId: "req_1" } };
    if (url.includes("/management/generation")) return { status: 404, body: { error: "not found" } };
    if (url.includes("/api/v1/generation?id=req_1")) return { status: 200, body: { generationId: "legacy" } };
    if (url.includes("/generation/request")) return { status: 200, body: { body: {} } };
    if (url.includes("/generation/response")) return { status: 200, body: { body: {} } };
    return { status: 404, body: { error: "not found" } };
  });
  const client = new ZenMuxClient({ apiKey: "test-key", fetchImpl, baseUrl: "https://example.test" });

  const detail = await client.getLogDetail("req_1");

  assert.deepEqual(detail.generation, { generationId: "legacy" });
  assert.ok(calls.some((call) => call.url === "https://example.test/api/v1/generation?id=req_1"));
});

test("non-2xx responses throw ZenMuxApiError with response body", async () => {
  const { fetchImpl } = mockFetch(() => ({ status: 401, body: { error: "unauthorized" } }));
  const client = new ZenMuxClient({ fetchImpl, baseUrl: "https://example.test" });

  await assert.rejects(
    () => client.getGeneration("req_1"),
    (error) => {
      assert.ok(error instanceof ZenMuxApiError);
      assert.equal(error.status, 401);
      assert.deepEqual(error.body, { error: "unauthorized" });
      return true;
    }
  );
});
