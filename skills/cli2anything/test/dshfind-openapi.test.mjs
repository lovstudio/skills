import test from "node:test";
import assert from "node:assert/strict";
import { createDshFindOpenapi } from "../src/dshfind-openapi.mjs";
import { createDshFindApiGraph } from "../src/dshfind-target.mjs";

test("dshfind OpenAPI covers the read-only plugin and market workflows", () => {
  const spec = createDshFindOpenapi();
  const graph = createDshFindApiGraph();

  assert.equal(spec.openapi, "3.1.0");
  assert.equal(spec.servers[0].url, "https://api.dshfind.com");
  assert.deepEqual(spec.security, []);
  assert.equal(spec.paths["/v1/plugins"].get.operationId, "listPlugins");
  assert.equal(spec.paths["/graphql"].get.operationId, "listPluginCategories");
  assert.equal(spec.paths["/graphql"].post.operationId, "executeGraphQLQuery");
  assert.equal(spec.paths["/graphql/schema"].get.operationId, "getGraphQLSchema");
  assert.deepEqual(spec.paths["/graphql"].get.tags, ["Categories"]);
  assert.deepEqual(spec.paths["/graphql"].post.tags, ["GraphQL"]);
  assert.equal(Object.keys(spec.paths["/graphql"].post.requestBody.content["application/json"].examples).length, 4);
  assert.equal(spec.paths["/v1/plugins/{owner}/{repo}"].get.operationId, "getPlugin");
  assert.equal(spec.paths["/v1/catalog"].get.operationId, "getCatalog");
  assert.equal(spec.paths["/market/manifest.json"].get.operationId, "getMarketManifest");
  assert.equal(spec.paths["/market/v1/plugins"].get.operationId, "listMarketPlugins");
  assert.equal(spec.paths["/healthz"].get.operationId, "getHealth");
  assert.equal(spec.paths["/v1/plugins"].post, undefined);
  assert.ok(spec.paths["/v1/plugins"].get.parameters.some((item) => item.name === "data_version"));
  assert.equal(graph.defaultWorkflowId, "dshfind-plugin-discovery");
  assert.ok(graph.edges.some((edge) => edge.id === "listPlugins-to-getPlugin"));
  assert.ok(graph.edges.some((edge) => edge.id === "listPluginCategories-to-listPlugins"));
  assert.ok(graph.edges.some((edge) => edge.id === "getGraphQLSchema-to-executeGraphQLQuery"));
  assert.ok(graph.edges.some((edge) => edge.id === "listMarketPlugins-to-listMarketPlugins"));
  assert.deepEqual(graph.safety.autoRunMethods, ["GET", "POST"]);
  assert.deepEqual(graph.safety.queryPostAllowList, ["executeGraphQLQuery"]);
});
