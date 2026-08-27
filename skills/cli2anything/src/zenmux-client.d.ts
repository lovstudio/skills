export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export type GenerationPayloadType =
  | "userRequest"
  | "providerRequest"
  | "userResponse"
  | "providerResponse";

export interface ZenMuxClientOptions {
  apiKey?: string;
  authorization?: string;
  baseUrl?: string;
  cookie?: string;
  csrfToken?: string;
  csrfHeaderName?: string;
  apiVersion?: string;
  fetchImpl?: typeof fetch;
  headers?: Record<string, string>;
}

export interface ListLogsParams {
  apiKeys?: string[];
  startTime?: number;
  stopTime?: number;
  page?: number;
  pageNo?: number;
  pageSize?: number;
  requestId?: string;
  modelSlugs?: string[];
  providerSlugs?: string[];
  finishReasons?: string[];
}

export interface LogDetailOptions {
  includePayloads?: boolean;
  requestType?: Extract<GenerationPayloadType, "userRequest" | "providerRequest">;
  responseType?: Extract<GenerationPayloadType, "userResponse" | "providerResponse">;
  query?: Record<string, string | number | boolean | undefined | null>;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export class ZenMuxApiError extends Error {
  status?: number;
  url?: string;
  body?: unknown;
}

export class ZenMuxClient {
  constructor(options?: ZenMuxClientOptions);
  request(path: string, options?: RequestInit & { body?: unknown }): Promise<unknown>;
  listLogs(params?: ListLogsParams, options?: { headers?: Record<string, string>; signal?: AbortSignal }): Promise<unknown>;
  getLogActivity(requestId: string, options?: LogDetailOptions): Promise<unknown>;
  listApiKeys(options?: { headers?: Record<string, string>; signal?: AbortSignal }): Promise<unknown>;
  listAllApiKeys(options?: { headers?: Record<string, string>; signal?: AbortSignal }): Promise<unknown>;
  getFinishReasons(options?: { headers?: Record<string, string>; signal?: AbortSignal }): Promise<unknown>;
  getGeneration(requestId: string, options?: { headers?: Record<string, string>; legacy?: boolean; signal?: AbortSignal }): Promise<unknown>;
  getLegacyGeneration(requestId: string, options?: { headers?: Record<string, string>; signal?: AbortSignal }): Promise<unknown>;
  getGenerationRequest(requestId: string, options?: { headers?: Record<string, string>; type?: "userRequest" | "providerRequest"; signal?: AbortSignal }): Promise<unknown>;
  getGenerationResponse(requestId: string, options?: { headers?: Record<string, string>; type?: "userResponse" | "providerResponse"; signal?: AbortSignal }): Promise<unknown>;
  getLogDetail(requestId: string, options?: LogDetailOptions): Promise<{
    requestId: string;
    activity: unknown;
    generation: unknown;
    requestPayload?: unknown;
    responsePayload?: unknown;
  }>;
}

export default ZenMuxClient;
