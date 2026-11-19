// PlaneClient — Plane REST API v1 的最小 SDK。
// 凭据只经构造参数或环境变量在内存中传入，不写入源码或生成文件。
const DEFAULT_BASE_URL = "http://localhost";

export class PlaneClient {
  constructor(options = {}) {
    this.baseUrl = String(options.baseUrl || process.env.PLANE_BASE_URL || DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.apiKey = options.apiKey || process.env.PLANE_API_KEY;
    this.fetchImpl = options.fetch || globalThis.fetch;
  }

  async request(method, path, { query, body, headers } = {}) {
    if (!this.apiKey) throw new Error("PlaneClient 需要 apiKey（构造参数或 PLANE_API_KEY）");
    const url = new URL(this.baseUrl + path);
    for (const [key, value] of Object.entries(query || {})) {
      if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
    }
    const response = await this.fetchImpl(url, {
      method,
      headers: { "X-API-Key": this.apiKey, ...(body !== undefined ? { "Content-Type": "application/json" } : {}), ...headers },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    const text = await response.text();
    const parsed = text ? safeJson(text) : null;
    if (!response.ok) {
      const error = new Error(`Plane API ${response.status} ${response.statusText} on ${method} ${url.pathname}`);
      error.status = response.status;
      error.body = parsed ?? text;
      throw error;
    }
    return parsed;
  }

  get(path, query) { return this.request("GET", path, { query }); }
  post(path, body, query) { return this.request("POST", path, { body, query }); }
  patch(path, body, query) { return this.request("PATCH", path, { body, query }); }
  delete(path, query) { return this.request("DELETE", path, { query }); }

  // schema 中已验证存在的常用入口；其余 130 个操作用 request() 按 openapi.json 直接调用。
  getCurrentUser() { return this.get("/api/v1/users/me/"); }
  listProjects(slug, query) { return this.get(`/api/v1/workspaces/${encodeURIComponent(slug)}/projects/`, query); }
  listWorkItems(slug, projectId, query) { return this.get(`/api/v1/workspaces/${encodeURIComponent(slug)}/projects/${encodeURIComponent(projectId)}/issues/`, query); }
  createWorkItem(slug, projectId, body) { return this.post(`/api/v1/workspaces/${encodeURIComponent(slug)}/projects/${encodeURIComponent(projectId)}/issues/`, body); }
  listStates(slug, projectId, query) { return this.get(`/api/v1/workspaces/${encodeURIComponent(slug)}/projects/${encodeURIComponent(projectId)}/states/`, query); }
  listLabels(slug, projectId, query) { return this.get(`/api/v1/workspaces/${encodeURIComponent(slug)}/projects/${encodeURIComponent(projectId)}/labels/`, query); }
  listCycles(slug, projectId, query) { return this.get(`/api/v1/workspaces/${encodeURIComponent(slug)}/projects/${encodeURIComponent(projectId)}/cycles/`, query); }
  listModules(slug, projectId, query) { return this.get(`/api/v1/workspaces/${encodeURIComponent(slug)}/projects/${encodeURIComponent(projectId)}/modules/`, query); }

  // 实例元信息，唯一无需 API key 的端点。
  async getInstance() {
    const response = await this.fetchImpl(new URL(this.baseUrl + "/api/instances/"));
    return safeJson(await response.text());
  }
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export default PlaneClient;
