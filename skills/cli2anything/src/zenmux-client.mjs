const DEFAULT_BASE_URL = "https://zenmux.ai";

const DEFAULT_REQUEST_TYPE = "userRequest";
const DEFAULT_RESPONSE_TYPE = "userResponse";
const DEFAULT_API_VERSION = "2026-04-20";

function env(name) {
  return globalThis.process?.env?.[name];
}

function cleanBaseUrl(baseUrl) {
  return String(baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
}

function appendQuery(path, query = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item !== undefined && item !== null && item !== "") params.append(key, String(item));
      }
    } else {
      params.set(key, String(value));
    }
  }
  const suffix = params.toString();
  return suffix ? `${path}?${suffix}` : path;
}

function required(value, name) {
  if (value === undefined || value === null || value === "") {
    throw new TypeError(`${name} is required`);
  }
  return value;
}

function hasHeader(headers, name) {
  const lowerName = name.toLowerCase();
  return Object.keys(headers).some((key) => key.toLowerCase() === lowerName);
}

function setHeaderIfMissing(headers, name, value) {
  if (value && !hasHeader(headers, name)) headers[name] = value;
}

export class ZenMuxApiError extends Error {
  constructor(message, { status, url, body }) {
    super(message);
    this.name = "ZenMuxApiError";
    this.status = status;
    this.url = url;
    this.body = body;
  }
}

export class ZenMuxClient {
  constructor(options = {}) {
    this.baseUrl = cleanBaseUrl(options.baseUrl);
    this.apiKey = options.apiKey || env("ZENMUX_API_KEY");
    this.authorization = options.authorization || env("ZENMUX_AUTHORIZATION");
    this.cookie = options.cookie || env("ZENMUX_COOKIE");
    this.csrfToken = options.csrfToken || env("ZENMUX_CSRF_TOKEN") || env("ZENMUX_XSRF_TOKEN");
    this.csrfHeaderName = options.csrfHeaderName || env("ZENMUX_CSRF_HEADER") || "X-XSRF-TOKEN";
    this.apiVersion = options.apiVersion ?? env("ZENMUX_API_VERSION") ?? DEFAULT_API_VERSION;
    this.fetchImpl = options.fetchImpl || globalThis.fetch;
    this.defaultHeaders = options.headers || {};
    if (!this.fetchImpl) throw new TypeError("A fetch implementation is required");
  }

  async request(path, options = {}) {
    const url = `${this.baseUrl}/${String(path).replace(/^\/+/, "")}`;
    const headers = {
      Accept: "application/json",
      ...this.defaultHeaders,
      ...(options.headers || {})
    };

    setHeaderIfMissing(headers, "Authorization", this.authorization || (this.apiKey ? `Bearer ${this.apiKey}` : undefined));
    setHeaderIfMissing(headers, "Cookie", this.cookie);
    setHeaderIfMissing(headers, this.csrfHeaderName, this.csrfToken);
    setHeaderIfMissing(headers, "x-api-version", this.apiVersion);

    let body = options.body;
    if (body !== undefined && body !== null && typeof body !== "string" && !(body instanceof ArrayBuffer)) {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
      body = JSON.stringify(body);
    }

    const response = await this.fetchImpl(url, {
      method: options.method || "GET",
      headers,
      body,
      signal: options.signal
    });

    const contentType = response.headers?.get?.("content-type") || "";
    const responseBody = contentType.includes("application/json")
      ? await response.json().catch(() => null)
      : await response.text().catch(() => "");

    if (!response.ok) {
      throw new ZenMuxApiError(`ZenMux request failed with HTTP ${response.status}`, {
        status: response.status,
        url,
        body: responseBody
      });
    }

    return responseBody;
  }

  listLogs(params = {}, options = {}) {
    const body = {
      apiKeys: params.apiKeys ?? [],
      startTime: params.startTime,
      stopTime: params.stopTime,
      pageNo: params.pageNo ?? params.page ?? 1,
      pageSize: params.pageSize ?? 20,
      requestId: params.requestId,
      modelSlugs: params.modelSlugs ?? [],
      providerSlugs: params.providerSlugs ?? [],
      finishReasons: params.finishReasons ?? []
    };

    return this.request("/api/api_key/activity", {
      method: "POST",
      body,
      signal: options.signal,
      headers: options.headers
    });
  }

  getLogActivity(requestId, options = {}) {
    const id = encodeURIComponent(required(requestId, "requestId"));
    const query = { id: requestId, ...(options.query || {}) };
    return this.request(appendQuery(`/api/api_key/activity/${id}`, query), {
      method: "GET",
      signal: options.signal,
      headers: options.headers
    });
  }

  listApiKeys(options = {}) {
    return this.request("/api/api_key/list", {
      method: "GET",
      signal: options.signal,
      headers: options.headers
    });
  }

  listAllApiKeys(options = {}) {
    return this.request("/api/api_key/list_all", {
      method: "GET",
      signal: options.signal,
      headers: options.headers
    });
  }

  getFinishReasons(options = {}) {
    return this.request("/api/api_key/finish_reasons", {
      method: "GET",
      signal: options.signal,
      headers: options.headers
    });
  }

  getGeneration(requestId, options = {}) {
    const id = required(requestId, "requestId");
    if (options.legacy) return this.getLegacyGeneration(id, options);
    return this.request(appendQuery("/api/v1/management/generation", { id }), {
      method: "GET",
      signal: options.signal,
      headers: options.headers
    });
  }

  getLegacyGeneration(requestId, options = {}) {
    const id = required(requestId, "requestId");
    return this.request(appendQuery("/api/v1/generation", { id }), {
      method: "GET",
      signal: options.signal,
      headers: options.headers
    });
  }

  getGenerationRequest(requestId, options = {}) {
    const id = required(requestId, "requestId");
    return this.request(
      appendQuery("/api/v1/generation/request", {
        id,
        type: options.type || DEFAULT_REQUEST_TYPE
      }),
      { method: "GET", signal: options.signal, headers: options.headers }
    );
  }

  getGenerationResponse(requestId, options = {}) {
    const id = required(requestId, "requestId");
    return this.request(
      appendQuery("/api/v1/generation/response", {
        id,
        type: options.type || DEFAULT_RESPONSE_TYPE
      }),
      { method: "GET", signal: options.signal, headers: options.headers }
    );
  }

  async getLogDetail(requestId, options = {}) {
    const includePayloads = options.includePayloads ?? true;
    const [activity, generation, requestPayload, responsePayload] = await Promise.all([
      this.getLogActivity(requestId, options),
      this.getGeneration(requestId, options).catch(async (error) => {
        try {
          return await this.getLegacyGeneration(requestId, options);
        } catch (legacyError) {
          return {
            _error: serializeError(error),
            _legacyError: serializeError(legacyError)
          };
        }
      }),
      includePayloads
        ? this.getGenerationRequest(requestId, { ...options, type: options.requestType }).catch((error) => ({ _error: serializeError(error) }))
        : Promise.resolve(undefined),
      includePayloads
        ? this.getGenerationResponse(requestId, { ...options, type: options.responseType }).catch((error) => ({ _error: serializeError(error) }))
        : Promise.resolve(undefined)
    ]);

    return {
      requestId,
      activity,
      generation,
      requestPayload,
      responsePayload
    };
  }
}

function serializeError(error) {
  return {
    name: error?.name || "Error",
    message: error?.message || String(error),
    status: error?.status,
    body: error?.body
  };
}

export default ZenMuxClient;
