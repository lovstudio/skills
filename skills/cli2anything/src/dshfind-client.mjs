const DEFAULT_BASE_URL = "https://api.dshfind.com";

function cleanBaseUrl(baseUrl) {
  return String(baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
}

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

export class DshFindApiError extends Error {
  constructor(message, { status, url, body }) {
    super(message);
    this.name = "DshFindApiError";
    this.status = status;
    this.url = url;
    this.body = body;
  }
}

export class DshFindClient {
  constructor(options = {}) {
    this.baseUrl = cleanBaseUrl(options.baseUrl);
    this.fetchImpl = options.fetchImpl || globalThis.fetch;
    this.defaultHeaders = options.headers || {};
    if (!this.fetchImpl) throw new TypeError("A fetch implementation is required");
  }

  async request(path, options = {}) {
    const url = `${this.baseUrl}/${String(path).replace(/^\/+/, "")}`;
    const response = await this.fetchImpl(url, {
      method: "GET",
      headers: { Accept: "application/json", ...this.defaultHeaders, ...(options.headers || {}) },
      signal: options.signal
    });
    const contentType = response.headers?.get?.("content-type") || "";
    const body = contentType.includes("application/json")
      ? await response.json().catch(() => null)
      : await response.text().catch(() => "");

    if (!response.ok) {
      throw new DshFindApiError(`dshfind request failed with HTTP ${response.status}`, {
        status: response.status,
        url,
        body
      });
    }
    return body;
  }

  health(options = {}) {
    return this.request("/healthz", options);
  }

  suggest(query, options = {}) {
    return this.request(appendQuery("/v1/suggest", { q: required(query, "query") }), options);
  }

  listPlugins(params = {}, options = {}) {
    return this.request(appendQuery("/v1/plugins", {
      q: params.q,
      page: params.page,
      per_page: params.perPage ?? params.per_page,
      category: params.category,
      language: params.language,
      grade: params.grade,
      owner: params.owner,
      tag: params.tag,
      min_score: params.minScore ?? params.min_score,
      featured: params.featured,
      official: params.official,
      archived: params.archived,
      insider: params.insider,
      has_install: params.hasInstall ?? params.has_install,
      is_plugin: params.isPlugin ?? params.is_plugin,
      sort: params.sort,
      order: params.order,
      data_version: params.dataVersion ?? params.data_version
    }), options);
  }

  getPlugin(owner, repo, options = {}) {
    const encodedOwner = encodeURIComponent(required(owner, "owner"));
    const encodedRepo = encodeURIComponent(required(repo, "repo"));
    return this.request(appendQuery(`/v1/plugins/${encodedOwner}/${encodedRepo}`, {
      snapshot_days: options.snapshotDays ?? options.snapshot_days
    }), options);
  }

  getCatalog(options = {}) {
    return this.request(appendQuery("/v1/catalog", {
      data_version: options.dataVersion ?? options.data_version
    }), options);
  }

  getMarketManifest(options = {}) {
    return this.request("/market/manifest.json", options);
  }

  listMarketPlugins(params = {}, options = {}) {
    return this.request(appendQuery("/market/v1/plugins", {
      q: params.q,
      category: params.category,
      limit: params.limit,
      cursor: params.cursor
    }), options);
  }
}

export default DshFindClient;
