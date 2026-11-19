import test from "node:test";
import assert from "node:assert/strict";
import { DshFindApiError, DshFindClient } from "../src/dshfind-client.mjs";

test("DshFindClient maps REST and GraphQL workflows to public endpoints", async () => {
  const seen = [];
  const client = new DshFindClient({
    fetchImpl: async (url, options) => {
      seen.push({ url, options });
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json" } });
    }
  });

  await client.listPlugins({ q: "memory", perPage: 10, minScore: 70, isPlugin: true, dataVersion: "sha256:test" });
  await client.listCategories();
  await client.getDataset();
  await client.listFacets();
  await client.listGraphqlPlugins({ first: 5, category: "memory", hasInstall: true, sort: "STARS" });
  await client.getGraphqlPlugin("deepseek-ai/deepseek-harness", { locale: "zh", snapshotDays: 7 });
  await client.getGraphqlSchema();
  await client.getPlugin("deepseek-ai", "deepseek-harness", { snapshotDays: 7 });
  await client.listMarketPlugins({ category: "memory", limit: 20, cursor: "opaque" });

  assert.equal(seen[0].options.method, "GET");
  assert.match(seen[0].url, /\/v1\/plugins\?/);
  assert.match(seen[0].url, /q=memory/);
  assert.match(seen[0].url, /per_page=10/);
  assert.match(seen[0].url, /min_score=70/);
  assert.match(seen[0].url, /is_plugin=true/);
  assert.match(seen[0].url, /data_version=sha256%3Atest/);
  const categoriesUrl = new URL(seen[1].url);
  assert.equal(categoriesUrl.pathname, "/graphql");
  assert.match(categoriesUrl.searchParams.get("query"), /pluginFacets \{ categories \{ value count \}/);
  assert.equal(seen[2].url, "https://api.dshfind.com/graphql");
  assert.equal(seen[2].options.method, "POST");
  assert.equal(JSON.parse(seen[2].options.body).operationName, "DshFindDataset");
  assert.match(JSON.parse(seen[3].options.body).query, /languages \{ value count \}/);
  const graphqlList = JSON.parse(seen[4].options.body);
  assert.deepEqual(graphqlList.variables, {
    first: 5,
    after: null,
    filter: { category: "memory", hasInstall: true },
    sort: "STARS",
    order: "DESC"
  });
  const graphqlDetail = JSON.parse(seen[5].options.body);
  assert.deepEqual(graphqlDetail.variables, { fullName: "deepseek-ai/deepseek-harness", locale: "zh", days: 7 });
  assert.equal(seen[6].url, "https://api.dshfind.com/graphql/schema");
  assert.equal(seen[6].options.headers.Accept, "application/graphql");
  assert.equal(seen[7].url, "https://api.dshfind.com/v1/plugins/deepseek-ai/deepseek-harness?snapshot_days=7");
  assert.match(seen[8].url, /\/market\/v1\/plugins\?/);
  assert.match(seen[8].url, /cursor=opaque/);
});

test("DshFindClient preserves public API error status and body", async () => {
  const client = new DshFindClient({
    fetchImpl: async () => new Response(JSON.stringify({ error: "not_found" }), {
      status: 404,
      headers: { "content-type": "application/json" }
    })
  });

  await assert.rejects(
    () => client.getPlugin("missing", "repo"),
    (error) => error instanceof DshFindApiError && error.status === 404 && error.body.error === "not_found"
  );
});
