const SENSITIVE_HEADER_RE = /^(authorization|cookie|set-cookie|x-xsrf-token|x-csrf-token|csrf-token|x-api-key|api-key)$/i;

export function redactHeaders(headers = {}) {
  const redacted = {};
  for (const [key, value] of Object.entries(headers || {})) {
    redacted[key] = SENSITIVE_HEADER_RE.test(key) ? "[redacted]" : value;
  }
  return redacted;
}

export function shapeMaybeJson(value, contentType = "") {
  if (value === undefined || value === null || value === "") return undefined;
  if (typeof value !== "string") return jsonShape(value);

  const trimmed = value.trim();
  if (contentType.includes("json") || trimmed.startsWith("{") || trimmed.startsWith("[")) {
    try {
      return jsonShape(JSON.parse(trimmed));
    } catch {
      return { type: "string", length: value.length, parseError: "invalid-json" };
    }
  }

  if (contentType.includes("x-www-form-urlencoded")) {
    const params = new URLSearchParams(value);
    return {
      type: "object",
      formEncoded: true,
      properties: Object.fromEntries([...params.keys()].map((key) => [key, { type: "string" }]))
    };
  }

  return { type: "string", length: value.length };
}

export function jsonShape(value, depth = 0, seen = new WeakSet()) {
  if (value === null) return { type: "null" };
  if (typeof value === "string") return shapeString(value);
  if (typeof value === "number") return { type: Number.isInteger(value) ? "integer" : "number" };
  if (typeof value === "boolean") return { type: "boolean" };
  if (Array.isArray(value)) return shapeArray(value, depth, seen);
  if (typeof value === "object") return shapeObject(value, depth, seen);
  return { type: typeof value };
}

function shapeString(value) {
  const shape = { type: "string" };
  if (value.startsWith("data:")) shape.format = "data-url";
  if (/^[A-Za-z0-9+/=_-]{200,}$/.test(value)) shape.contentEncoding = "base64-like";
  if (value.length > 0) shape.length = value.length;
  return shape;
}

function shapeArray(value, depth, seen) {
  if (depth >= 6) return { type: "array", truncated: true };
  const samples = value.slice(0, 8).map((item) => jsonShape(item, depth + 1, seen));
  return {
    type: "array",
    length: value.length,
    items: mergeShapes(samples)
  };
}

function shapeObject(value, depth, seen) {
  if (seen.has(value)) return { type: "object", circular: true };
  if (depth >= 6) return { type: "object", truncated: true };
  seen.add(value);

  const entries = Object.entries(value);
  const visibleEntries = entries.slice(0, 80);
  const properties = {};
  for (const [key, child] of visibleEntries) {
    properties[key] = jsonShape(child, depth + 1, seen);
  }

  seen.delete(value);
  return {
    type: "object",
    properties,
    additionalProperties: entries.length > visibleEntries.length
  };
}

function mergeShapes(shapes) {
  const present = shapes.filter(Boolean);
  if (present.length === 0) return true;
  const typeSet = new Set(present.map((shape) => shape.type));
  if (typeSet.size > 1) return { oneOf: [...typeSet].map((type) => ({ type })) };
  if (typeSet.has("object")) {
    const properties = {};
    for (const shape of present) {
      for (const [key, child] of Object.entries(shape.properties || {})) {
        properties[key] = properties[key] ? mergeShapes([properties[key], child]) : child;
      }
    }
    return { type: "object", properties, additionalProperties: true };
  }
  if (typeSet.has("array")) {
    return { type: "array", items: mergeShapes(present.map((shape) => shape.items)) };
  }
  return present[0];
}
