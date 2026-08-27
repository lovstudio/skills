import { randomUUID } from "node:crypto";
import { createServer } from "node:http";
import { createServer as createNetServer } from "node:net";

const DEFAULT_PORT_START = 47831;
const DEFAULT_PORT_COUNT = 100;
const DEFAULT_API_VERSION = "2026-04-20";
const DEFAULT_TARGET_ORIGIN = "https://zenmux.ai";
const DEFAULT_TARGET_PAGE_URL = "https://zenmux.ai/platform/logs";

export class ExtensionBridgeError extends Error {
  constructor(message, details) {
    super(message);
    this.name = "ExtensionBridgeError";
    this.details = details;
  }
}

export class ExtensionBridgeSession {
  constructor(options = {}) {
    this.targetOrigin = options.targetOrigin || DEFAULT_TARGET_ORIGIN;
    this.targetPageUrl = options.targetPageUrl || DEFAULT_TARGET_PAGE_URL;
    this.apiVersion = options.apiVersion || DEFAULT_API_VERSION;
    this.jobTimeoutMs = Number(options.jobTimeoutMs || 60_000);
    this.jobs = [];
    this.polls = [];
    this.waiters = new Map();
    this.lastSeen = null;
    this.lastPollSeen = null;
    this.extensionVersion = null;
    this.server = createServer((req, res) => this.handle(req, res));
  }

  static async start(options = {}) {
    const port = options.port || await findOpenPort(
      Number(options.portStart || DEFAULT_PORT_START),
      Number(options.portCount || DEFAULT_PORT_COUNT)
    );
    const session = new ExtensionBridgeSession(options);
    await session.listen(port);
    return session;
  }

  listen(port) {
    this.port = port;
    return new Promise((resolve, reject) => {
      this.server.once("error", reject);
      this.server.listen(port, "127.0.0.1", () => {
        this.server.off("error", reject);
        resolve();
      });
    });
  }

  close() {
    for (const poll of this.polls.splice(0)) {
      clearTimeout(poll.timeout);
      try {
        sendJson(poll.res, 200, { type: "noop" }, corsHeaders());
      } catch {}
    }
    for (const [id, waiter] of this.waiters) {
      clearTimeout(waiter.timeout);
      waiter.reject(new ExtensionBridgeError("Extension bridge session closed", { id }));
    }
    this.waiters.clear();
    this.server.close();
  }

  fetchJson(path, options = {}) {
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    const hasHeader = (name) => Object.keys(headers).some((key) => key.toLowerCase() === name.toLowerCase());
    const apiVersion = options.apiVersion ?? this.apiVersion;
    if (apiVersion && !hasHeader("x-api-version")) headers["x-api-version"] = apiVersion;

    let body = options.body;
    if (body !== undefined && body !== null && typeof body !== "string" && !hasHeader("content-type")) {
      headers["Content-Type"] = "application/json";
    }

    return this.proxy({
      url: new URL(path, this.targetOrigin).toString(),
      method: options.method || "GET",
      headers,
      body,
      targetPageUrl: this.targetPageUrl
    });
  }

  proxy(payload) {
    const id = randomUUID();
    const job = {
      id,
      url: payload.url,
      method: payload.method || "GET",
      headers: payload.headers || {},
      body: payload.body,
      targetPageUrl: payload.targetPageUrl || this.targetPageUrl
    };

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.waiters.delete(id);
        reject(new ExtensionBridgeError(
          "No cli2anything++ browser extension responded. Load ~/.cli2anything-plus-plus/browser-extension as an unpacked Chrome extension, open the target site in that same browser, then retry.",
          { id, port: this.port }
        ));
      }, this.jobTimeoutMs);
      this.waiters.set(id, { resolve, reject, timeout });
      this.dispatch(job);
    });
  }

  dispatch(job) {
    const poll = this.polls.shift();
    if (poll) {
      clearTimeout(poll.timeout);
      return sendJson(poll.res, 200, { type: "job", job }, corsHeaders());
    }
    this.jobs.push(job);
  }

  async handle(req, res) {
    try {
      if (req.method === "OPTIONS" && req.url.startsWith("/__cap/extension/")) {
        return send(res, 204, "text/plain", "", corsHeaders());
      }
      if (req.method === "GET" && req.url.startsWith("/__cap/extension/hello")) {
        this.recordSeen(req);
        return sendJson(res, 200, { ok: true, bridge: "extension" }, corsHeaders());
      }
      if (req.method === "GET" && req.url.startsWith("/__cap/extension/poll")) {
        this.recordSeen(req);
        this.lastPollSeen = Date.now();
        return this.waitForJob(req, res);
      }
      if (req.method === "POST" && req.url.startsWith("/__cap/extension/result")) {
        this.recordSeen(req);
        const result = JSON.parse(await readBody(req));
        const waiter = this.waiters.get(result.id);
        if (waiter) {
          clearTimeout(waiter.timeout);
          this.waiters.delete(result.id);
          waiter.resolve({
            ok: result.ok ?? (result.status >= 200 && result.status < 300),
            status: result.status,
            statusText: result.statusText,
            url: result.url,
            contentType: result.contentType,
            body: result.body
          });
        }
        return sendJson(res, 200, { ok: true }, corsHeaders());
      }
      if (req.method === "GET" && req.url === "/__cap/health") {
        return sendJson(res, 200, {
          ok: true,
          bridge: "extension",
          port: this.port,
          extensionConnected: Boolean(this.lastSeen && Date.now() - this.lastSeen < 45_000),
          extensionPolling: Boolean(this.lastPollSeen && Date.now() - this.lastPollSeen < 45_000),
          extensionVersion: this.extensionVersion
        });
      }
      return sendJson(res, 404, { message: "not found" });
    } catch (error) {
      return sendJson(res, 502, { message: error?.message || String(error) }, corsHeaders());
    }
  }

  waitForJob(req, res) {
    if (this.jobs.length) {
      return sendJson(res, 200, { type: "job", job: this.jobs.shift() }, corsHeaders());
    }
    const timeout = setTimeout(() => {
      const index = this.polls.findIndex((poll) => poll.res === res);
      if (index !== -1) this.polls.splice(index, 1);
      sendJson(res, 200, { type: "noop" }, corsHeaders());
    }, 8_000);
    this.polls.push({ res, timeout });
    const cleanup = () => {
      clearTimeout(timeout);
      const index = this.polls.findIndex((poll) => poll.res === res);
      if (index !== -1) this.polls.splice(index, 1);
    };
    req.on("aborted", cleanup);
    res.on("close", () => {
      if (!res.writableEnded) cleanup();
    });
  }

  recordSeen(req) {
    this.lastSeen = Date.now();
    try {
      const url = new URL(req.url, "http://127.0.0.1");
      this.extensionVersion = url.searchParams.get("version") || this.extensionVersion;
    } catch {}
  }
}

async function findOpenPort(start, count) {
  for (let port = start; port < start + count; port += 1) {
    if (await isPortOpen(port)) return port;
  }
  throw new ExtensionBridgeError(`No open extension bridge port found from ${start} to ${start + count - 1}`);
}

function isPortOpen(port) {
  return new Promise((resolve) => {
    const tester = createNetServer()
      .once("error", () => resolve(false))
      .once("listening", () => tester.close(() => resolve(true)))
      .listen(port, "127.0.0.1");
  });
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function sendJson(res, status, body, headers = {}) {
  return send(res, status, "application/json; charset=utf-8", JSON.stringify(body), headers);
}

function send(res, status, contentType, body, headers = {}) {
  res.writeHead(status, {
    "content-type": contentType,
    "cache-control": "no-store",
    ...headers
  });
  res.end(body);
}

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type"
  };
}
