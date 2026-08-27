import test from "node:test";
import assert from "node:assert/strict";
import { createZenmuxOpenapi } from "../src/zenmux-openapi.mjs";

test("OpenAPI spec contains the log list/detail contract", () => {
  const spec = createZenmuxOpenapi();

  assert.equal(spec.openapi, "3.1.0");
  assert.ok(spec.paths["/api/api_key/activity"].post);
  assert.ok(spec.paths["/api/api_key/activity/{requestId}"].get);
  assert.ok(spec.paths["/api/api_key/list"].get);
  assert.ok(spec.paths["/api/api_key/list_all"].get);
  assert.ok(spec.paths["/api/api_key/finish_reasons"].get);
  assert.ok(spec.paths["/api/v1/management/generation"].get);
  assert.equal(spec.paths["/api/v1/generation"].get.summary, "Get dashboard generation metering and billing detail");
  assert.ok(spec.paths["/api/v1/generation/request"].get);
  assert.ok(spec.paths["/api/v1/generation/response"].get);
  assert.equal(spec.paths["/api/api_key/activity"].post.operationId, "listLogs");
  assert.equal(spec.paths["/api/api_key/finish_reasons"].get.operationId, "getFinishReasons");
  assert.ok(spec.paths["/api/api_key/activity"].post.security.some((entry) => entry.consoleCookie && entry.csrfToken));
  assert.equal(spec.paths["/api/v1/generation/response"].get.operationId, "getGenerationResponsePayload");
  assert.equal(spec.components.securitySchemes.csrfToken.name, "X-XSRF-TOKEN");
  assert.equal(spec.components.parameters.ApiVersionHeader.schema.default, "2026-04-20");
  assert.equal(spec.components.schemas.ListLogsRequest.properties.pageSize.minimum, 5);
  assert.deepEqual(
    spec.paths["/api/api_key/activity"].post.requestBody.content["application/json"].example.apiKeys,
    []
  );
  assert.equal(spec.paths["/api/api_key/activity"].post.requestBody.content["application/json"].example.pageNo, 1);
  assert.equal(spec.paths["/api/api_key/activity"].post.requestBody.content["application/json"].example.pageSize, 20);
  assert.ok(spec.paths["/api/api_key/activity"].post.requestBody.content["application/json"].example.startTime > 0);
  assert.ok(spec.paths["/api/api_key/activity"].post.requestBody.content["application/json"].example.stopTime > 0);
  assert.equal(spec.components.parameters.RequestIdQuery.schema.default, "paste-request-id-from-listLogs");
  assert.equal(spec.components.parameters.RequestIdPath.schema.default, "paste-request-id-from-listLogs");
  assert.equal(spec.paths["/api/v1/generation/request"].get.parameters[1].schema.default, "userRequest");
  assert.equal(spec.paths["/api/v1/generation/response"].get.parameters[1].schema.default, "userResponse");
  assert.equal(
    spec.paths["/api/api_key/activity"].post.responses["200"].links.firstGenerationResponsePayload.operationId,
    "getGenerationResponsePayload"
  );
  assert.equal(
    spec.paths["/api/api_key/activity"].post.responses["200"].links.firstGenerationResponsePayload.parameters["query.type"],
    "userResponse"
  );
  assert.ok(spec["x-cli-anything-links"].some((link) => link.to === "getGenerationResponsePayload" && link.sourceSelector === "$.data[*].requestId"));
});
