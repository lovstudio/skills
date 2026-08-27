import type { ListLogsParams, LogDetailOptions } from "./zenmux-client.mjs";

export interface BrowserPageTransport {
  fetchJson(path: string, options?: {
    method?: string;
    headers?: Record<string, string>;
    body?: unknown;
    apiVersion?: string;
  }): Promise<{
    ok: boolean;
    status: number;
    url: string;
    body: unknown;
  }>;
}

export interface ZenMuxBrowserClientOptions {
  apiVersion?: string;
  headers?: Record<string, string>;
}

export class ZenMuxBrowserClient {
  constructor(pageSession: BrowserPageTransport, options?: ZenMuxBrowserClientOptions);
  request(path: string, options?: { method?: string; headers?: Record<string, string>; body?: unknown; apiVersion?: string }): Promise<unknown>;
  listLogs(params?: ListLogsParams, options?: { headers?: Record<string, string> }): Promise<unknown>;
  getLogActivity(requestId: string, options?: LogDetailOptions): Promise<unknown>;
  listApiKeys(options?: { headers?: Record<string, string> }): Promise<unknown>;
  listAllApiKeys(options?: { headers?: Record<string, string> }): Promise<unknown>;
  getFinishReasons(options?: { headers?: Record<string, string> }): Promise<unknown>;
  getGeneration(requestId: string, options?: { headers?: Record<string, string>; legacy?: boolean }): Promise<unknown>;
  getLegacyGeneration(requestId: string, options?: { headers?: Record<string, string> }): Promise<unknown>;
  getGenerationRequest(requestId: string, options?: { headers?: Record<string, string>; type?: "userRequest" | "providerRequest" }): Promise<unknown>;
  getGenerationResponse(requestId: string, options?: { headers?: Record<string, string>; type?: "userResponse" | "providerResponse" }): Promise<unknown>;
  getLogDetail(requestId: string, options?: LogDetailOptions): Promise<{
    requestId: string;
    activity: unknown;
    generation: unknown;
    requestPayload?: unknown;
    responsePayload?: unknown;
  }>;
}

export default ZenMuxBrowserClient;
