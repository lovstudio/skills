import test from "node:test";
import assert from "node:assert/strict";
import { redactHeaders, shapeMaybeJson } from "../src/json-shape.mjs";

test("redactHeaders removes credential-bearing headers", () => {
  assert.deepEqual(redactHeaders({
    Authorization: "Bearer secret",
    Cookie: "session=secret",
    "X-XSRF-TOKEN": "secret",
    Accept: "application/json"
  }), {
    Authorization: "[redacted]",
    Cookie: "[redacted]",
    "X-XSRF-TOKEN": "[redacted]",
    Accept: "application/json"
  });
});

test("shapeMaybeJson records structure rather than payload contents", () => {
  const shape = shapeMaybeJson(JSON.stringify({
    text: "hello",
    image: { inlineData: "data:image/png;base64,AAAA" },
    items: [{ id: 1 }]
  }), "application/json");

  assert.equal(shape.type, "object");
  assert.equal(shape.properties.text.type, "string");
  assert.equal(shape.properties.image.properties.inlineData.format, "data-url");
  assert.equal(shape.properties.items.items.properties.id.type, "integer");
});
