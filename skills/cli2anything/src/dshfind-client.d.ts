export interface DshFindClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  headers?: Record<string, string>;
}

export interface RequestOptions {
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

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
  getPlugin(owner: string, repo: string, options?: RequestOptions & { snapshotDays?: number }): Promise<unknown>;
  getCatalog(options?: RequestOptions & { dataVersion?: string }): Promise<unknown>;
  getMarketManifest(options?: RequestOptions): Promise<unknown>;
  listMarketPlugins(params?: Record<string, unknown>, options?: RequestOptions): Promise<unknown>;
}

export default DshFindClient;
