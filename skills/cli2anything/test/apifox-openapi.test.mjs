import test from "node:test";
import assert from "node:assert/strict";
import { createApifoxOpenapi, createApifoxReadme } from "../src/apifox-openapi.mjs";
import { createDshFindOpenapi } from "../src/dshfind-openapi.mjs";

test("Apifox OpenAPI imports a ready-to-run environment and safe examples", () => {
  const spec = createApifoxOpenapi(createDshFindOpenapi());
  const operations = Object.values(spec.paths).flatMap((pathItem) => Object.entries(pathItem))
    .filter(([method]) => ["get", "post"].includes(method))
    .map(([, operation]) => operation);

  assert.equal(spec.openapi, "3.1.0");
  assert.match(spec.info.title, /v0\.5\.0/);
  assert.deepEqual(spec.security, []);
  assert.deepEqual(spec.servers, [{
    url: "https://api.dshfind.com",
    description: "生产环境（公开只读，无需鉴权）"
  }]);
  assert.equal(operations.length, 10);
  assert.ok(operations.every((operation) => operation.operationId && operation.security.length === 0));

  const listParameters = Object.fromEntries(
    spec.paths["/v1/plugins"].get.parameters.map((parameter) => [parameter.name, parameter])
  );
  assert.equal(listParameters.q.example, "memory");
  assert.equal(listParameters.page.example, 1);
  assert.equal(listParameters.per_page.example, 5);
  assert.equal(listParameters.sort.example, "stars");
  assert.equal(listParameters.order.example, "desc");
  assert.equal(listParameters.category.example, undefined);
  assert.equal(listParameters.owner.example, undefined);
  assert.equal(listParameters.tag.example, undefined);
  assert.equal(listParameters.data_version.example, undefined);
  assert.equal(listParameters.data_version.schema.default, undefined);

  const categoryQuery = spec.paths["/graphql"].get.parameters.find((parameter) => parameter.name === "query");
  assert.deepEqual(spec.paths["/graphql"].get.tags, ["Categories"]);
  assert.match(categoryQuery.example, /pluginFacets \{ categories \{ value count \}/);
  assert.equal(categoryQuery.required, true);

  const graphqlExamples = spec.paths["/graphql"].post.requestBody.content["application/json"].examples;
  assert.deepEqual(Object.keys(graphqlExamples), ["dataset", "facets", "plugins", "plugin"]);
  assert.match(graphqlExamples.facets.value.query, /languages \{ value count \}/);
  assert.equal(graphqlExamples.plugins.value.variables.filter.category, "memory");
  assert.equal(graphqlExamples.plugins.value.variables.after, null);
  assert.equal(spec.paths["/graphql/schema"].get.security.length, 0);

  const detailParameters = Object.fromEntries(
    spec.paths["/v1/plugins/{owner}/{repo}"].get.parameters.map((parameter) => [parameter.name, parameter])
  );
  assert.equal(detailParameters.owner.example, "deepseek-ai");
  assert.equal(detailParameters.repo.example, "deepseek-harness");
  assert.equal(detailParameters.snapshot_days.example, 7);

  const marketParameters = Object.fromEntries(
    spec.paths["/market/v1/plugins"].get.parameters.map((parameter) => [parameter.name, parameter])
  );
  assert.equal(marketParameters.limit.example, 5);
  assert.equal(marketParameters.cursor.example, undefined);
  assert.equal(spec.components.securitySchemes, undefined);

  const readme = createApifoxReadme();
  assert.match(readme, /导入 Servers 为环境/);
  assert.match(readme, /自动生成接口用例/);
  assert.match(readme, /pluginFacets\.categories/);
  assert.match(readme, /Categories \(1\)/);
  assert.match(readme, /GraphQL \(2\)/);
  assert.match(readme, /dataset.*facets.*plugins.*plugin/s);
  assert.match(readme, /https:\/\/dshfind\.lovstudio\.ai\/openapi\.json/);
  assert.match(readme, /定时导入（绑定数据源）/);
  assert.match(readme, /直接点击“发送”/);
});
