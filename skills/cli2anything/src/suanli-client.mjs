// SuanliClient — 共绩算力 Open API 与大模型云服务的 SDK。
// 签名与加密规则来自 https://docs.suanli.cn/api-key/rsa；凭据只经构造参数或环境变量在内存中传入。
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { constants, createPrivateKey, createPublicKey, publicEncrypt, sign } from "node:crypto";

export const OPENAPI_BASE_URL = "https://openapi.suanli.cn";
export const LLM_BASE_URL = "https://api.suanli.cn/v1";
export const DEFAULT_API_VERSION = "1.0.0";
// 文档规定：2048 位密钥每段最多 244 字节明文。
export const ENCRYPT_CHUNK_BYTES = 244;

// macOS 钥匙串条目名：security add-generic-password -a "$USER" -s <service> -w
export const KEYCHAIN_SERVICES = { token: "suanli-token", llmApiKey: "suanli-llm-key" };

// 环境变量缺失时由 CLI 与 Swagger 代理调用；SUANLI_KEYCHAIN=0 关闭，非 macOS 或条目不存在时返回 undefined。
export function readKeychainSecret(service, env = process.env) {
  if (process.platform !== "darwin" || env.SUANLI_KEYCHAIN === "0") return undefined;
  try {
    const value = execFileSync("security", ["find-generic-password", "-s", service, "-w"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: 10000,
      env,
    }).trim();
    return value || undefined;
  } catch {
    return undefined;
  }
}

// 生成时由适配器替换为 operationId → { method, path, base, encryption, write } 的完整表。
export const OPERATIONS = /*__SUANLI_OPERATIONS__*/ {};

export class SuanliApiError extends Error {
  constructor(message, { status, code, body } = {}) {
    super(message);
    this.name = "SuanliApiError";
    this.status = status;
    this.code = code;
    this.body = body;
  }
}

export function buildSigningString({ path, version, timestamp, token, body = "" }) {
  return `${path}\n${version}\n${timestamp}\n${token}\n${body ?? ""}`;
}

export function signRequest(privateKey, fields) {
  return sign("sha256", Buffer.from(buildSigningString(fields), "utf8"), toPrivateKey(privateKey)).toString("base64");
}

export function encryptBody(platformPublicKey, payload) {
  const text = typeof payload === "string" ? payload : JSON.stringify(payload);
  const data = Buffer.from(text, "utf8");
  const key = toPublicKey(platformPublicKey);
  const chunks = [];
  for (let start = 0; start < data.length; start += ENCRYPT_CHUNK_BYTES) {
    chunks.push(publicEncrypt({ key, padding: constants.RSA_PKCS1_PADDING }, data.subarray(start, start + ENCRYPT_CHUNK_BYTES)));
  }
  return Buffer.concat(chunks).toString("base64");
}

export function serializeQuery(query = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null) continue;
    params.set(key, Array.isArray(value) ? value.join(",") : String(value));
  }
  return params.toString();
}

export class SuanliClient {
  constructor(options = {}) {
    const env = options.env || process.env;
    this.token = options.token ?? env.SUANLI_TOKEN;
    this.version = String(options.version ?? env.SUANLI_API_VERSION ?? DEFAULT_API_VERSION);
    this.baseUrl = trimSlash(options.baseUrl ?? env.SUANLI_BASE_URL ?? OPENAPI_BASE_URL);
    this.privateKey = options.privateKey ?? readKeyFile(env.SUANLI_PRIVATE_KEY_FILE);
    this.platformPublicKey = options.platformPublicKey ?? readKeyFile(env.SUANLI_PLATFORM_PUBLIC_KEY_FILE);
    this.llmApiKey = options.llmApiKey ?? env.SUANLI_LLM_API_KEY;
    this.llmBaseUrl = trimSlash(options.llmBaseUrl ?? env.SUANLI_LLM_BASE_URL ?? LLM_BASE_URL);
    this.fetchImpl = options.fetch || globalThis.fetch;
    this.now = options.now || (() => Date.now());
  }

  get mode() {
    return this.privateKey ? "rsa" : "token";
  }

  // 只构造请求、不发出；CLI 的 --dry-run 与 Swagger 代理共用这一步，保证签名的就是实际发送的内容。
  prepare(method, path, { query, body, encryption = false } = {}) {
    const upper = String(method).toUpperCase();
    const qs = serializeQuery(query);
    const signingPath = qs ? `${path}?${qs}` : path;
    let wireBody = "";
    if (body !== undefined && body !== null && upper !== "GET") {
      if (encryption) {
        if (!this.privateKey || !this.platformPublicKey) {
          throw new Error("该接口要求请求体加密，只能用 RSA 模式调用：提供 privateKey 与 platformPublicKey（或 SUANLI_PRIVATE_KEY_FILE、SUANLI_PLATFORM_PUBLIC_KEY_FILE）。");
        }
        wireBody = encryptBody(this.platformPublicKey, body);
      } else {
        wireBody = typeof body === "string" ? body : JSON.stringify(body);
      }
    }
    const timestamp = String(this.now());
    const headers = { "Content-Type": "application/json", version: this.version, timestamp };
    if (this.token) headers.token = this.token;
    if (this.privateKey && this.token) {
      headers.sign_str = signRequest(this.privateKey, { path: signingPath, version: this.version, timestamp, token: this.token, body: wireBody });
    }
    return {
      url: `${this.baseUrl}${signingPath}`,
      init: { method: upper, headers, body: upper === "GET" || wireBody === "" ? undefined : wireBody },
      mode: this.mode,
      signed: Boolean(headers.sign_str),
      encrypted: Boolean(encryption && wireBody),
      signingPath,
    };
  }

  async request(method, path, { query, body, encryption = false, envelope = false } = {}) {
    if (!this.token) throw new Error("SuanliClient 需要 token（构造参数或 SUANLI_TOKEN）。");
    const prepared = this.prepare(method, path, { query, body, encryption });
    const response = await this.fetchImpl(prepared.url, prepared.init);
    const text = await response.text();
    const parsed = safeJson(text);
    if (!response.ok) {
      throw new SuanliApiError(`共绩 Open API HTTP ${response.status} on ${prepared.init.method} ${path}`, { status: response.status, body: parsed ?? text });
    }
    if (!parsed || typeof parsed !== "object") {
      throw new SuanliApiError(`共绩 Open API 返回了非 JSON 响应：${prepared.init.method} ${path}`, { status: response.status, body: text });
    }
    if (parsed.code !== "0000") {
      const message = parsed.message ?? parsed.msg ?? "unknown error";
      throw new SuanliApiError(`共绩 Open API ${parsed.code}: ${message}`, { status: response.status, code: parsed.code, body: parsed });
    }
    return envelope ? parsed : parsed.data;
  }

  // 按 operationId 调用生成表里的任意 Open API 接口。
  call(operationId, { query, body, envelope } = {}) {
    const op = OPERATIONS[operationId];
    if (!op) throw new Error(`未知 operationId: ${operationId}`);
    if (op.base === "llm") return this.llmRequest(op.method, op.path, { body });
    return this.request(op.method, op.path, { query, body, encryption: op.encryption, envelope });
  }

  prepareLlm(method, path, { body } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (this.llmApiKey) headers.Authorization = `Bearer ${this.llmApiKey}`;
    // 文档的 Base URL 已含 /v1，operation path 也以 /v1 开头，这里去掉重复段。
    const suffix = path.replace(/^\/v1(?=\/)/, "");
    return {
      url: `${this.llmBaseUrl}${suffix}`,
      init: { method: String(method).toUpperCase(), headers, body: body === undefined ? undefined : JSON.stringify(body) },
    };
  }

  async llmRequest(method, path, { body } = {}) {
    if (!this.llmApiKey) throw new Error("大模型云服务需要 API Key（构造参数 llmApiKey 或 SUANLI_LLM_API_KEY）。");
    const prepared = this.prepareLlm(method, path, { body });
    const response = await this.fetchImpl(prepared.url, prepared.init);
    if (body?.stream) {
      if (!response.ok) throw new SuanliApiError(`大模型云服务 HTTP ${response.status}`, { status: response.status, body: safeJson(await response.text()) });
      return response;
    }
    const text = await response.text();
    const parsed = safeJson(text);
    if (!response.ok) {
      const message = parsed?.error?.message ?? parsed?.message ?? text;
      throw new SuanliApiError(`大模型云服务 HTTP ${response.status}: ${message}`, { status: response.status, code: parsed?.error?.code ?? parsed?.code, body: parsed ?? text });
    }
    return parsed;
  }

  chatCompletions(body) {
    return this.llmRequest("POST", "/v1/chat/completions", { body });
  }

  listModels() {
    return this.llmRequest("GET", "/v1/models");
  }
}

function toPrivateKey(key) {
  if (typeof key !== "string" && !Buffer.isBuffer(key)) return key;
  const text = String(key);
  return text.includes("-----BEGIN")
    ? createPrivateKey(text)
    : createPrivateKey({ key: Buffer.from(text.replace(/\s+/g, ""), "base64"), format: "der", type: "pkcs8" });
}

function toPublicKey(key) {
  if (typeof key !== "string" && !Buffer.isBuffer(key)) return key;
  const text = String(key);
  return text.includes("-----BEGIN")
    ? createPublicKey(text)
    : createPublicKey({ key: Buffer.from(text.replace(/\s+/g, ""), "base64"), format: "der", type: "spki" });
}

function readKeyFile(path) {
  return path ? readFileSync(path, "utf8") : undefined;
}

function trimSlash(value) {
  return String(value).replace(/\/+$/, "");
}

function safeJson(text) {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export default SuanliClient;
