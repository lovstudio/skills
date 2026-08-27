import { redactHeaders, shapeMaybeJson } from "./json-shape.mjs";

const DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222";
const DEFAULT_XSRF_COOKIE = "XSRF-TOKEN";
const DEFAULT_XSRF_HEADER = "X-XSRF-TOKEN";
const DEFAULT_API_VERSION = "2026-04-20";

export class CdpError extends Error {
  constructor(message, details) {
    super(message);
    this.name = "CdpError";
    this.details = details;
  }
}

export class CdpConnection {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 1;
    this.pending = new Map();
    this.handlers = new Map();

    socket.addEventListener("message", (event) => this.handleMessage(event.data));
    socket.addEventListener("close", () => {
      for (const { reject } of this.pending.values()) {
        reject(new CdpError("CDP socket closed"));
      }
      this.pending.clear();
    });
  }

  static async connect(webSocketDebuggerUrl) {
    if (typeof WebSocket !== "function") {
      throw new CdpError("Global WebSocket is not available. Use Node 22+ or provide a WebSocket implementation.");
    }

    const socket = new WebSocket(webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new CdpError("Timed out connecting to CDP WebSocket")), 10_000);
      socket.addEventListener("open", () => {
        clearTimeout(timeout);
        resolve();
      }, { once: true });
      socket.addEventListener("error", (event) => {
        clearTimeout(timeout);
        reject(new CdpError("Failed to connect to CDP WebSocket", event));
      }, { once: true });
    });

    return new CdpConnection(socket);
  }

  send(method, params = {}) {
    const id = this.nextId++;
    const payload = { id, method, params };
    const promise = new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
    this.socket.send(JSON.stringify(payload));
    return promise;
  }

  on(method, handler) {
    const handlers = this.handlers.get(method) || new Set();
    handlers.add(handler);
    this.handlers.set(method, handlers);
    return () => handlers.delete(handler);
  }

  close() {
    this.socket.close();
  }

  handleMessage(data) {
    const message = JSON.parse(data);
    if (message.id) {
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) {
        pending.reject(new CdpError(message.error.message || "CDP command failed", message.error));
      } else {
        pending.resolve(message.result);
      }
      return;
    }

    for (const handler of this.handlers.get(message.method) || []) {
      handler(message.params);
    }
  }
}

export class BrowserPageSession {
  constructor(connection, target, options = {}) {
    this.connection = connection;
    this.target = target;
    this.apiVersion = options.apiVersion || DEFAULT_API_VERSION;
    this.xsrfCookieName = options.xsrfCookieName || DEFAULT_XSRF_COOKIE;
    this.xsrfHeaderName = options.xsrfHeaderName || DEFAULT_XSRF_HEADER;
  }

  static async connect(options = {}) {
    const cdpEndpoint = options.cdpEndpoint || DEFAULT_CDP_ENDPOINT;
    const target = await resolvePageTarget({
      cdpEndpoint,
      url: options.url,
      targetUrlIncludes: options.targetUrlIncludes
    });
    const connection = await CdpConnection.connect(target.webSocketDebuggerUrl);
    return new BrowserPageSession(connection, target, options);
  }

  close() {
    this.connection.close();
  }

  async navigate(url) {
    await this.connection.send("Page.enable");
    return this.connection.send("Page.navigate", { url });
  }

  async evaluateFunction(fn, arg) {
    const expression = `(${fn.toString()})(${JSON.stringify(arg)})`;
    const result = await this.connection.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true
    });

    if (result.exceptionDetails) {
      const text = result.exceptionDetails.text || result.exceptionDetails.exception?.description || "Browser evaluation failed";
      throw new CdpError(text, result.exceptionDetails);
    }

    return result.result?.value;
  }

  fetchJson(path, options = {}) {
    return this.evaluateFunction(browserFetchJson, {
      path,
      method: options.method || "GET",
      headers: options.headers || {},
      body: options.body,
      apiVersion: options.apiVersion ?? this.apiVersion,
      xsrfCookieName: options.xsrfCookieName || this.xsrfCookieName,
      xsrfHeaderName: options.xsrfHeaderName || this.xsrfHeaderName
    });
  }

  async captureNetwork(options = {}) {
    const seconds = Number(options.seconds || 20);
    const includeBodies = Boolean(options.includeBodies);
    const urlIncludes = options.urlIncludes || "/api/";
    const entries = new Map();
    const unsubs = [];

    await this.connection.send("Network.enable");
    unsubs.push(this.connection.on("Network.requestWillBeSent", (event) => {
      const request = event.request || {};
      if (!shouldCaptureUrl(request.url, urlIncludes)) return;
      entries.set(event.requestId, {
        requestId: event.requestId,
        method: request.method,
        url: request.url,
        resourceType: event.type,
        requestHeaders: redactHeaders(request.headers),
        requestBodyShape: shapeMaybeJson(request.postData, headerValue(request.headers, "content-type"))
      });
    }));

    unsubs.push(this.connection.on("Network.responseReceived", (event) => {
      const entry = entries.get(event.requestId);
      if (!entry) return;
      const response = event.response || {};
      entry.status = response.status;
      entry.mimeType = response.mimeType;
      entry.responseHeaders = redactHeaders(response.headers);
    }));

    unsubs.push(this.connection.on("Network.loadingFinished", (event) => {
      const entry = entries.get(event.requestId);
      if (entry) entry.encodedDataLength = event.encodedDataLength;
    }));

    if (options.onReady) await options.onReady();
    await delay(seconds * 1000);

    for (const unsub of unsubs) unsub();

    if (includeBodies) {
      for (const entry of entries.values()) {
        if (!isShapeableMime(entry.mimeType)) continue;
        try {
          const body = await this.connection.send("Network.getResponseBody", { requestId: entry.requestId });
          entry.responseBodyShape = body.base64Encoded
            ? { type: "string", contentEncoding: "base64", length: body.body.length }
            : shapeMaybeJson(body.body, entry.mimeType || "");
        } catch (error) {
          entry.responseBodyError = error.message;
        }
      }
    }

    return {
      capturedAt: new Date().toISOString(),
      target: this.target.url,
      urlIncludes,
      includeBodies,
      entries: [...entries.values()]
    };
  }
}

export async function listTargets(cdpEndpoint = DEFAULT_CDP_ENDPOINT) {
  const response = await fetch(`${normalizeCdpEndpoint(cdpEndpoint)}/json`);
  if (!response.ok) throw new CdpError(`Failed to list CDP targets: HTTP ${response.status}`);
  return response.json();
}

export async function openTarget(cdpEndpoint = DEFAULT_CDP_ENDPOINT, url = "about:blank") {
  const endpoint = `${normalizeCdpEndpoint(cdpEndpoint)}/json/new?${encodeURIComponent(url)}`;
  let response = await fetch(endpoint, { method: "PUT" });
  if (!response.ok && [404, 405].includes(response.status)) {
    response = await fetch(endpoint);
  }
  if (!response.ok) throw new CdpError(`Failed to open CDP target: HTTP ${response.status}`);
  return response.json();
}

export async function resolvePageTarget(options = {}) {
  const cdpEndpoint = options.cdpEndpoint || DEFAULT_CDP_ENDPOINT;
  const targets = await listTargets(cdpEndpoint);
  const target = targets.find((item) => {
    if (item.type !== "page" || !item.webSocketDebuggerUrl) return false;
    if (options.targetUrlIncludes) return item.url?.includes(options.targetUrlIncludes);
    if (options.url) return sameOrigin(item.url, options.url);
    return item.url && item.url !== "about:blank";
  });

  if (target) return target;
  return openTarget(cdpEndpoint, options.url || "about:blank");
}

function browserFetchJson(input) {
  const headers = { Accept: "application/json", ...(input.headers || {}) };
  const hasHeader = (name) => Object.keys(headers).some((key) => key.toLowerCase() === name.toLowerCase());
  const readCookie = (name) => {
    const prefix = `${name}=`;
    const item = document.cookie.split(/;\s*/).find((part) => part.startsWith(prefix));
    return item ? decodeURIComponent(item.slice(prefix.length)) : "";
  };

  if (input.apiVersion && !hasHeader("x-api-version")) headers["x-api-version"] = input.apiVersion;
  const xsrf = input.xsrfCookieName ? readCookie(input.xsrfCookieName) : "";
  if (xsrf && input.xsrfHeaderName && !hasHeader(input.xsrfHeaderName)) headers[input.xsrfHeaderName] = xsrf;
  const requestUrl = new URL(input.path, location.origin);
  const sameSite = requestUrl.hostname === location.hostname || (
    requestUrl.hostname.endsWith(`.${location.hostname}`) ||
    location.hostname.endsWith(`.${requestUrl.hostname}`) ||
    requestUrl.hostname.split(".").slice(-2).join(".") === location.hostname.split(".").slice(-2).join(".")
  );
  const ctoken = sameSite ? (readCookie("ctoken") || readCookie("_CHIPS-ctoken")) : "";
  if (ctoken && !requestUrl.searchParams.has("ctoken")) requestUrl.searchParams.set("ctoken", ctoken);

  let body = input.body;
  if (body !== undefined && body !== null && typeof body !== "string") {
    if (!hasHeader("content-type")) headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }

  return fetch(requestUrl.toString(), {
    method: input.method || "GET",
    headers,
    body,
    credentials: "include"
  }).then(async (response) => {
    const contentType = response.headers.get("content-type") || "";
    const text = await response.text();
    let parsed = text;
    if (contentType.includes("json")) {
      try {
        parsed = JSON.parse(text);
      } catch {
        parsed = null;
      }
    }

    return {
      ok: response.ok,
      status: response.status,
      statusText: response.statusText,
      url: response.url,
      contentType,
      body: parsed
    };
  });
}

function normalizeCdpEndpoint(cdpEndpoint) {
  return String(cdpEndpoint || DEFAULT_CDP_ENDPOINT).replace(/\/+$/, "");
}

function shouldCaptureUrl(url, urlIncludes) {
  return Boolean(url && (!urlIncludes || url.includes(urlIncludes)));
}

function headerValue(headers = {}, name) {
  const match = Object.entries(headers || {}).find(([key]) => key.toLowerCase() === name.toLowerCase());
  return match?.[1] || "";
}

function isShapeableMime(mimeType = "") {
  return /json|text|javascript|event-stream|xml|x-www-form-urlencoded/i.test(mimeType);
}

function sameOrigin(a, b) {
  try {
    return new URL(a).origin === new URL(b).origin;
  } catch {
    return false;
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
