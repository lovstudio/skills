import test from "node:test";
import assert from "node:assert/strict";
import { ZenMuxApiError } from "../src/zenmux-client.mjs";
import { ZenMuxBrowserClient } from "../src/zenmux-browser-client.mjs";

function mockPageSession(handler) {
  const calls = [];
  return {
    calls,
    async fetchJson(path, options = {}) {
      calls.push({ path, options });
      return handler(path, options);
    }
  };
}

test("browser client posts listLogs through the page session transport", async () => {
  const session = mockPageSession(() => ({ ok: true, status: 200, url: "https://zenmux.ai/api/api_key/activity", body: { data: [] } }));
  const client = new ZenMuxBrowserClient(session);

  await client.listLogs({ pageNo: 2, pageSize: 3, requestId: "req_1" });

  assert.equal(session.calls[0].path, "/api/api_key/activity");
  assert.equal(session.calls[0].options.method, "POST");
  assert.deepEqual(session.calls[0].options.body, {
    apiKeys: [],
    pageNo: 2,
    pageSize: 3,
    requestId: "req_1",
    modelSlugs: [],
    providerSlugs: [],
    finishReasons: []
  });
});

test("browser client combines log detail calls without direct cookie material", async () => {
  const session = mockPageSession((path) => ({ ok: true, status: 200, url: `https://zenmux.ai${path}`, body: { path } }));
  const client = new ZenMuxBrowserClient(session);

  const detail = await client.getLogDetail("req_1");

  assert.equal(detail.requestId, "req_1");
  assert.equal(session.calls.length, 4);
  assert.ok(session.calls.some((call) => call.path === "/api/api_key/activity/req_1?id=req_1"));
  assert.ok(session.calls.some((call) => call.path === "/api/v1/management/generation?id=req_1"));
  assert.ok(session.calls.some((call) => call.path === "/api/v1/generation/request?id=req_1&type=userRequest"));
  assert.ok(session.calls.some((call) => call.path === "/api/v1/generation/response?id=req_1&type=userResponse"));
});

test("browser client wraps dependency endpoints", async () => {
  const session = mockPageSession((path) => ({ ok: true, status: 200, url: `https://zenmux.ai${path}`, body: { path } }));
  const client = new ZenMuxBrowserClient(session);

  await client.listApiKeys();
  await client.listAllApiKeys();
  await client.getFinishReasons();

  assert.deepEqual(session.calls.map((call) => call.path), [
    "/api/api_key/list",
    "/api/api_key/list_all",
    "/api/api_key/finish_reasons"
  ]);
});

test("browser client wraps non-2xx responses as ZenMuxApiError", async () => {
  const session = mockPageSession(() => ({ ok: false, status: 403, url: "https://zenmux.ai/api/api_key/activity", body: { message: "forbidden" } }));
  const client = new ZenMuxBrowserClient(session);

  await assert.rejects(
    () => client.listLogs(),
    (error) => {
      assert.ok(error instanceof ZenMuxApiError);
      assert.equal(error.status, 403);
      assert.deepEqual(error.body, { message: "forbidden" });
      return true;
    }
  );
});
