const DEFAULT_BASE_URL = "https://api.dshfind.com";
const CATEGORIES_QUERY = "query DshFindCategories { pluginFacets { categories { value count } } }";
export const DSHFIND_DATASET_QUERY = "query DshFindDataset { dataset { dataVersion asOf } }";
export const DSHFIND_FACETS_QUERY = "query DshFindFacets { pluginFacets { categories { value count } languages { value count } tags { value count } grades { value count } } }";
export const DSHFIND_GRAPHQL_PLUGINS_QUERY = "query DshFindPlugins($first: Int = 20, $after: String, $filter: PluginFilter, $sort: PluginSort = DEFAULT, $order: SortOrder = DESC) { plugins(first: $first, after: $after, filter: $filter, sort: $sort, order: $order) { totalCount dataVersion asOf nodes { id fullName name owner repositoryUrl description tags language stars contributors pushedAt archived category score grade isFeatured isOfficial isInsider isRisky riskNote isPlugin install { cmd source kind pkgName npmPublished releaseTgzUrl releaseTag probedAt } } pageInfo { hasNextPage endCursor } } }";
export const DSHFIND_GRAPHQL_PLUGIN_QUERY = "query DshFindPlugin($fullName: ID!, $locale: String, $days: Int = 30) { plugin(fullName: $fullName) { id fullName name owner repositoryUrl description tags language stars contributors pushedAt archived category score grade rating { score grade calculatedAt version } isFeatured isOfficial isInsider isRisky riskNote isPlugin install { cmd source kind pkgName npmPublished releaseTgzUrl releaseTag probedAt } firstSeenAt lastSyncedAt i18n(locale: $locale) { locale description intro highlights updatedAt } snapshots(days: $days) { date stars contributors pushedAt } growth { windowDays stars contributors } } }";

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
    const method = options.method || "GET";
    const requestBody = options.body === undefined
      ? undefined
      : typeof options.body === "string"
        ? options.body
        : JSON.stringify(options.body);
    const response = await this.fetchImpl(url, {
      method,
      headers: {
        Accept: "application/json",
        ...(requestBody === undefined ? {} : { "Content-Type": "application/json" }),
        ...this.defaultHeaders,
        ...(options.headers || {})
      },
      body: requestBody,
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

  listCategories(options = {}) {
    return this.request(appendQuery("/graphql", { query: CATEGORIES_QUERY }), options);
  }

  graphql(query, variables = {}, options = {}) {
    return this.request("/graphql", {
      ...options,
      method: "POST",
      body: {
        query: required(query, "query"),
        variables,
        ...(options.operationName ? { operationName: options.operationName } : {})
      }
    });
  }

  getDataset(options = {}) {
    return this.graphql(DSHFIND_DATASET_QUERY, {}, { ...options, operationName: "DshFindDataset" });
  }

  listFacets(options = {}) {
    return this.graphql(DSHFIND_FACETS_QUERY, {}, { ...options, operationName: "DshFindFacets" });
  }

  listGraphqlPlugins(params = {}, options = {}) {
    const filter = params.filter || graphqlFilter(params);
    return this.graphql(DSHFIND_GRAPHQL_PLUGINS_QUERY, {
      first: params.first ?? 20,
      after: params.after ?? null,
      filter: Object.keys(filter).length ? filter : null,
      sort: params.sort ?? "DEFAULT",
      order: params.order ?? "DESC"
    }, { ...options, operationName: "DshFindPlugins" });
  }

  getGraphqlPlugin(fullName, params = {}, options = {}) {
    return this.graphql(DSHFIND_GRAPHQL_PLUGIN_QUERY, {
      fullName: required(fullName, "fullName"),
      locale: params.locale ?? null,
      days: params.snapshotDays ?? params.days ?? 30
    }, { ...options, operationName: "DshFindPlugin" });
  }

  getGraphqlSchema(options = {}) {
    return this.request("/graphql/schema", {
      ...options,
      headers: { Accept: "application/graphql", ...(options.headers || {}) }
    });
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

function graphqlFilter(params) {
  return compact({
    category: params.category,
    language: params.language,
    grade: params.grade,
    q: params.q,
    owner: params.owner,
    tag: params.tag,
    minScore: params.minScore ?? params.min_score,
    featured: params.featured,
    official: params.official,
    archived: params.archived,
    insider: params.insider,
    risky: params.risky,
    hasInstall: params.hasInstall ?? params.has_install,
    isPlugin: params.isPlugin ?? params.is_plugin
  });
}

function compact(value) {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined));
}

export default DshFindClient;
