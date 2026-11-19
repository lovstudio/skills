#!/usr/bin/env node
// 共绩算力 Swagger 本地代理：只监听 127.0.0.1，凭据只从本进程环境变量读取，
// 每个请求现场生成 timestamp 与 sign_str；浏览器端不接触 token。默认拒绝写操作。
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { KEYCHAIN_SERVICES, SuanliClient, readKeychainSecret } from "../sdk/index.mjs";

const DIR = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const arg = name => {
  const index = args.indexOf(name);
  return index < 0 ? undefined : args[index + 1];
};
const PORT = Number(arg("--port") || process.env.PORT || 4790);
const ALLOW_WRITE = args.includes("--allow-write");
const METHODS = ["get", "post", "put", "patch", "delete"];

const spec = JSON.parse(await readFile(resolve(DIR, "../openapi.json"), "utf8"));
const operations = new Map();
for (const [path, item] of Object.entries(spec.paths)) {
  for (const [method, op] of Object.entries(item)) {
    if (!METHODS.includes(method)) continue;
    operations.set(`${method.toUpperCase()} ${path}`, { path, method: method.toUpperCase(), op, llm: Boolean(op.security?.some(s => "LlmBearer" in s)) });
  }
}

function localSpec() {
  const copy = structuredClone(spec);
  copy.servers = [{ url: `http://127.0.0.1:${PORT}/proxy/openapi`, description: "本机签名代理 → openapi.suanli.cn" }];
  for (const item of Object.values(copy.paths)) {
    if (item.servers) item.servers = [{ url: `http://127.0.0.1:${PORT}/proxy/llm`, description: "本机代理 → api.suanli.cn" }];
  }
  return copy;
}

async function readRequestBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString("utf8");
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("请求体不是合法 JSON");
  }
}

function send(res, status, body, type = "application/json; charset=utf-8") {
  res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(typeof body === "string" ? body : JSON.stringify(body, null, 2));
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://127.0.0.1:${PORT}`);
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) return send(res, 200, await readFile(resolve(DIR, "index.html"), "utf8"), "text/html; charset=utf-8");
    if (req.method === "GET" && (url.pathname === "/drilldown" || url.pathname === "/drilldown.html")) return send(res, 200, await readFile(resolve(DIR, "drilldown.html"), "utf8"), "text/html; charset=utf-8");
    if (req.method === "GET" && url.pathname === "/openapi.json") return send(res, 200, localSpec());

    const match = url.pathname.match(/^\/proxy\/(openapi|llm)(\/.*)$/);
    if (!match) return send(res, 404, { error: "not found" });
    const [, base, path] = match;
    const entry = operations.get(`${req.method} ${path}`);
    if (!entry || entry.llm !== (base === "llm")) return send(res, 404, { error: `openapi.json 中没有 ${req.method} ${path}` });
    if (entry.op["x-write-operation"] && !ALLOW_WRITE) {
      return send(res, 403, { error: `${req.method} ${path} 是写操作，代理默认拒绝。确需调试时用 --allow-write 重启代理。` });
    }

    const client = new SuanliClient({
      token: process.env.SUANLI_TOKEN || readKeychainSecret(KEYCHAIN_SERVICES.token),
      llmApiKey: process.env.SUANLI_LLM_API_KEY || readKeychainSecret(KEYCHAIN_SERVICES.llmApiKey),
    });
    const body = await readRequestBody(req);
    if (entry.llm) {
      if (!client.llmApiKey) return send(res, 401, { error: `代理进程没有大模型 API Key：设置 SUANLI_LLM_API_KEY 或钥匙串条目 ${KEYCHAIN_SERVICES.llmApiKey}` });
      const prepared = client.prepareLlm(req.method, path, { body });
      const upstream = await fetch(prepared.url, prepared.init);
      res.writeHead(upstream.status, { "Content-Type": upstream.headers.get("content-type") || "application/json" });
      for await (const chunk of upstream.body || []) res.write(chunk);
      return res.end();
    }
    if (!client.token) return send(res, 401, { error: `代理进程没有 API 密钥：设置 SUANLI_TOKEN 或钥匙串条目 ${KEYCHAIN_SERVICES.token}` });
    // Swagger UI 会把 version、timestamp 等声明过的头一起发来；这里统一由 SDK 重新生成，忽略浏览器传值。
    const query = Object.fromEntries(url.searchParams);
    const prepared = client.prepare(req.method, path, { query, body, encryption: Boolean(entry.op["x-suanli-auth"]?.encryption) });
    const upstream = await fetch(prepared.url, prepared.init);
    res.writeHead(upstream.status, { "Content-Type": upstream.headers.get("content-type") || "application/json" });
    res.end(await upstream.text());
  } catch (error) {
    send(res, 500, { error: error?.message || String(error) });
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Swagger: http://127.0.0.1:${PORT}`);
  console.log(`Open API 模式: ${process.env.SUANLI_PRIVATE_KEY_FILE ? "RSA 签名" : "Token"}；写操作: ${ALLOW_WRITE ? "允许" : "拒绝"}`);
});
