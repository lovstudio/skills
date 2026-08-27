import { ZenMuxApiError } from "./zenmux-client.mjs";

const DEFAULT_REQUEST_TYPE = "userRequest";
const DEFAULT_RESPONSE_TYPE = "userResponse";

function appendQuery(path, query = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
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

function cleanObject(value) {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined));
}

export class ZenMuxBrowserClient {
  constructor(pageSession, options = {}) {
    if (!pageSession?.fetchJson) throw new TypeError("A BrowserPageSession-compatible transport is required");
    this.pageSession = pageSession;
    this.apiVersion = options.apiVersion;
    this.defaultHeaders = options.headers || {};
  }

  async request(path, options = {}) {
    const result = await this.pageSession.fetchJson(path, {
      method: options.method || "GET",
      headers: { ...this.defaultHeaders, ...(options.headers || {}) },
      body: options.body,
      apiVersion: options.apiVersion ?? this.apiVersion
    });

    if (!result.ok) {
      throw new ZenMuxApiError(`ZenMux browser-session request failed with HTTP ${result.status}`, {
        status: result.status,
        url: result.url,
        body: result.body
      });
    }

    return result.body;
  }

  listLogs(params = {}, options = {}) {
    const body = cleanObject({
      apiKeys: params.apiKeys ?? [],
      startTime: params.startTime,
      stopTime: params.stopTime,
      pageNo: params.pageNo ?? params.page ?? 1,
      pageSize: params.pageSize ?? 20,
      requestId: params.requestId,
      modelSlugs: params.modelSlugs ?? [],
      providerSlugs: params.providerSlugs ?? [],
      finishReasons: params.finishReasons ?? []
    });

    return this.request("/api/api_key/activity", {
      method: "POST",
      body,
      headers: options.headers
    });
  }

  getLogActivity(requestId, options = {}) {
    const id = encodeURIComponent(required(requestId, "requestId"));
    const query = { id: requestId, ...(options.query || {}) };
    return this.request(appendQuery(`/api/api_key/activity/${id}`, query), {
      method: "GET",
      headers: options.headers
    });
  }

  listApiKeys(options = {}) {
    return this.request("/api/api_key/list", {
      method: "GET",
      headers: options.headers
    });
  }

  listAllApiKeys(options = {}) {
    return this.request("/api/api_key/list_all", {
      method: "GET",
      headers: options.headers
    });
  }

  getFinishReasons(options = {}) {
    return this.request("/api/api_key/finish_reasons", {
      method: "GET",
      headers: options.headers
    });
  }

  getGeneration(requestId, options = {}) {
    const id = required(requestId, "requestId");
    if (options.legacy) return this.getLegacyGeneration(id, options);
    return this.request(appendQuery("/api/v1/management/generation", { id }), {
      method: "GET",
      headers: options.headers
    });
  }

  getLegacyGeneration(requestId, options = {}) {
    const id = required(requestId, "requestId");
    return this.request(appendQuery("/api/v1/generation", { id }), {
      method: "GET",
      headers: options.headers
    });
  }

  getGenerationRequest(requestId, options = {}) {
    const id = required(requestId, "requestId");
    return this.request(appendQuery("/api/v1/generation/request", {
      id,
      type: options.type || DEFAULT_REQUEST_TYPE
    }), {
      method: "GET",
      headers: options.headers
    });
  }

  getGenerationResponse(requestId, options = {}) {
    const id = required(requestId, "requestId");
    return this.request(appendQuery("/api/v1/generation/response", {
      id,
      type: options.type || DEFAULT_RESPONSE_TYPE
    }), {
      method: "GET",
      headers: options.headers
    });
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

export default ZenMuxBrowserClient;
