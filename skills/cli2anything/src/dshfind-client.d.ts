export interface DshFindClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  headers?: Record<string, string>;
}

export interface RequestOptions {
  signal?: AbortSignal;
  headers?: Record<string, string>;
  method?: string;
  body?: unknown;
  operationName?: string;
}

export declare const DSHFIND_DATASET_QUERY: string;
export declare const DSHFIND_FACETS_QUERY: string;
export declare const DSHFIND_GRAPHQL_PLUGINS_QUERY: string;
export declare const DSHFIND_GRAPHQL_PLUGIN_QUERY: string;

export declare class DshFindApiError extends Error {
  status: number;
  url: string;
  body: unknown;
}

export declare class DshFindClient {
  constructor(options?: DshFindClientOptions);
  request(path: string, options?: RequestOptions): Promise<unknown>;
  health(options?: RequestOptions): Promise<unknown>;
  suggest(query: string, options?: RequestOptions): Promise<unknown>;
  listPlugins(params?: Record<string, unknown>, options?: RequestOptions): Promise<unknown>;
  listCategories(options?: RequestOptions): Promise<unknown>;
  graphql(query: string, variables?: Record<string, unknown>, options?: RequestOptions): Promise<unknown>;
  getDataset(options?: RequestOptions): Promise<unknown>;
  listFacets(options?: RequestOptions): Promise<unknown>;
  listGraphqlPlugins(params?: Record<string, unknown>, options?: RequestOptions): Promise<unknown>;
  getGraphqlPlugin(fullName: string, params?: Record<string, unknown>, options?: RequestOptions): Promise<unknown>;
  getGraphqlSchema(options?: RequestOptions): Promise<unknown>;
  getPlugin(owner: string, repo: string, options?: RequestOptions & { snapshotDays?: number }): Promise<unknown>;
  getCatalog(options?: RequestOptions & { dataVersion?: string }): Promise<unknown>;
  getMarketManifest(options?: RequestOptions): Promise<unknown>;
  listMarketPlugins(params?: Record<string, unknown>, options?: RequestOptions): Promise<unknown>;
}

export default DshFindClient;
