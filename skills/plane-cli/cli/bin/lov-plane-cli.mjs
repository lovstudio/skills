#!/usr/bin/env node
// lov-plane-cli — schema 驱动的 Plane REST API v1 命令行。
// 命令表由随包分发的 openapi.json 在启动时构建，不硬编码任何端点。
import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PKG_DIR = dirname(dirname(fileURLToPath(import.meta.url)));
const CONFIG_PATH = process.env.PLANE_CLI_CONFIG || resolve(homedir(), ".config/lov-plane-cli/config.json");
const DEFAULT_BASE_URL = "http://localhost";

const kebab = s => String(s).replace(/_/g, "-").replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();

async function loadSpec() {
  return JSON.parse(await readFile(resolve(PKG_DIR, "openapi.json"), "utf8"));
}

async function loadConfig() {
  try {
    return JSON.parse(await readFile(CONFIG_PATH, "utf8"));
  } catch {
    return {};
  }
}

// 把 OpenAPI 展开成命令表：一个 operationId 一条命令。
function buildCommands(spec) {
  const commands = new Map();
  for (const [path, item] of Object.entries(spec.paths || {})) {
    const shared = item.parameters || [];
    for (const [method, op] of Object.entries(item)) {
      if (!["get", "post", "patch", "put", "delete"].includes(method)) continue;
      const name = kebab(op.operationId || `${method}-${path}`);
      const params = [...shared, ...(op.parameters || [])];
      commands.set(name, {
        name,
        method: method.toUpperCase(),
        path,
        summary: (op.summary || "").trim(),
        tag: (op.tags || ["Other"])[0],
        pathParams: params.filter(p => p.in === "path"),
        queryParams: params.filter(p => p.in === "query"),
        hasBody: Boolean(op.requestBody),
        bodyRequired: Boolean(op.requestBody?.required),
      });
    }
  }
  return commands;
}

// path 参数支持三种写法：位置参数、--slug 这类原名、以及 -w/-p 短别名。
const ALIASES = { w: "slug", workspace: "slug", p: "project_id", project: "project_id", id: "pk" };

function parseArgs(argv) {
  const positional = [];
  const flags = new Map();
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("-")) {
      positional.push(token);
      continue;
    }
    const raw = token.replace(/^--?/, "");
    const [key, inlineValue] = raw.includes("=") ? [raw.slice(0, raw.indexOf("=")), raw.slice(raw.indexOf("=") + 1)] : [raw, undefined];
    const normalized = ALIASES[key] || key.replace(/-/g, "_");
    if (inlineValue !== undefined) {
      flags.set(normalized, inlineValue);
      continue;
    }
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("-")) {
      flags.set(normalized, true);
      continue;
    }
    flags.set(normalized, next);
    i += 1;
  }
  return { positional, flags };
}

async function readBody(value) {
  if (value === undefined) return undefined;
  if (typeof value !== "string") throw new Error("--data 需要 JSON 字符串或 @文件路径");
  const text = value.startsWith("@") ? await readFile(resolve(value.slice(1)), "utf8") : value;
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error(`--data 不是合法 JSON：${error.message}`);
  }
}

function resolveAuth(flags, config) {
  const baseUrl = String(flags.get("base_url") || process.env.PLANE_BASE_URL || config.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
  const apiKey = flags.get("api_key") || process.env.PLANE_API_KEY || config.apiKey;
  return { baseUrl, apiKey: typeof apiKey === "string" ? apiKey : undefined };
}

function usage(commands, spec) {
  const byTag = new Map();
  for (const command of commands.values()) {
    if (!byTag.has(command.tag)) byTag.set(command.tag, []);
    byTag.get(command.tag).push(command);
  }
  const lines = [
    `lov-plane-cli — Plane REST API v1 命令行（${commands.size} 个操作，来自 ${spec.info?.title || "OpenAPI"}）`,
    "",
    "用法:",
    "  lov-plane-cli <command> [路径参数...] [--query 值] [--data '<json>'|@file.json]",
    "",
    "全局选项:",
    "  --base-url <url>   实例地址，默认 $PLANE_BASE_URL 或 http://localhost",
    "  --api-key <key>    API key，默认 $PLANE_API_KEY 或配置文件",
    "  --raw              输出原始响应体，不做 JSON 美化",
    "  --dry-run          只打印将要发出的请求，不实际调用",
    "  --help             查看某个命令的参数说明",
    "",
    "常用别名: -w/--workspace → slug   -p/--project → project_id   --id → pk",
    "",
    `凭据来源: $PLANE_API_KEY 或 ${CONFIG_PATH}（{"baseUrl":"...","apiKey":"..."}）`,
    "获取 API key: 登录 Plane → 头像 → Settings → API tokens → Add API token",
    "",
    "命令:",
  ];
  for (const tag of [...byTag.keys()].sort()) {
    lines.push(`  ${tag}`);
    for (const command of byTag.get(tag).sort((a, b) => a.name.localeCompare(b.name))) {
      lines.push(`    ${command.name.padEnd(42)} ${command.method} ${command.path}`);
    }
  }
  lines.push("", "示例:", "  lov-plane-cli list-projects -w my-workspace", "  lov-plane-cli create-work-item -w my-workspace -p <project-id> --data '{\"name\":\"新任务\"}'");
  return lines.join("\n");
}

function commandHelp(command) {
  const lines = [
    `${command.name} — ${command.summary || "(schema 未提供摘要)"}`,
    `${command.method} ${command.path}`,
    "",
  ];
  if (command.pathParams.length) {
    lines.push("路径参数（按顺序作为位置参数，或用同名选项传入）:");
    for (const p of command.pathParams) lines.push(`  --${kebab(p.name).padEnd(24)} ${(p.description || "").split("\n")[0]}`);
    lines.push("");
  }
  if (command.queryParams.length) {
    lines.push("查询参数:");
    for (const p of command.queryParams) lines.push(`  --${kebab(p.name).padEnd(24)} ${(p.description || "").split("\n")[0]}`);
    lines.push("");
  }
  if (command.hasBody) lines.push(`请求体: --data '<json>' 或 --data @file.json${command.bodyRequired ? "（必填）" : "（可选）"}`, "");
  return lines.join("\n");
}

function buildUrl(command, flags, positional, baseUrl) {
  let path = command.path;
  const queue = [...positional];
  for (const param of command.pathParams) {
    const key = param.name.replace(/-/g, "_");
    let value = flags.get(key);
    if (value === undefined) value = queue.shift();
    if (value === undefined) throw new Error(`缺少路径参数 ${param.name}（用 --${kebab(param.name)} 传入，或作为位置参数）`);
    path = path.replace(`{${param.name}}`, encodeURIComponent(String(value)));
  }
  const url = new URL(baseUrl + path);
  const known = new Set(command.queryParams.map(p => p.name.replace(/-/g, "_")));
  for (const [key, value] of flags) {
    if (["base_url", "api_key", "data", "raw", "dry_run", "help"].includes(key)) continue;
    if (command.pathParams.some(p => p.name.replace(/-/g, "_") === key)) continue;
    if (!known.has(key)) throw new Error(`未知参数 --${kebab(key)}；用 lov-plane-cli ${command.name} --help 查看可用参数`);
    const original = command.queryParams.find(p => p.name.replace(/-/g, "_") === key).name;
    url.searchParams.set(original, value === true ? "true" : String(value));
  }
  return url;
}

async function main() {
  const argv = process.argv.slice(2);
  const spec = await loadSpec();
  const commands = buildCommands(spec);
  const name = argv[0] && !argv[0].startsWith("-") ? argv[0] : undefined;

  if (["--version", "-v", "version"].includes(argv[0])) {
    console.log(JSON.parse(await readFile(resolve(PKG_DIR, "package.json"), "utf8")).version);
    return;
  }
  if (!name || ["help", "--help", "-h"].includes(argv[0])) {
    console.log(usage(commands, spec));
    return;
  }
  const command = commands.get(name);
  if (!command) {
    const near = [...commands.keys()].filter(k => k.includes(name.split("-")[0])).slice(0, 8);
    console.error(`未知命令: ${name}`);
    if (near.length) console.error(`可能想用: ${near.join(", ")}`);
    console.error("运行 lov-plane-cli help 查看全部命令。");
    process.exit(1);
  }

  const { positional, flags } = parseArgs(argv.slice(1));
  if (flags.has("help")) {
    console.log(commandHelp(command));
    return;
  }

  const config = await loadConfig();
  const { baseUrl, apiKey } = resolveAuth(flags, config);
  const url = buildUrl(command, flags, positional, baseUrl);
  const body = await readBody(flags.get("data"));

  if (flags.get("dry_run")) {
    console.log(JSON.stringify({ method: command.method, url: url.toString(), hasApiKey: Boolean(apiKey), body: body ?? null }, null, 2));
    return;
  }
  if (!apiKey) {
    console.error("缺少 API key。设置 PLANE_API_KEY，或用 --api-key，或写入 " + CONFIG_PATH);
    console.error("获取方式: 登录 Plane → 头像 → Settings → API tokens → Add API token");
    process.exit(2);
  }
  if (command.hasBody && command.bodyRequired && body === undefined) throw new Error(`${command.name} 需要请求体：--data '<json>' 或 --data @file.json`);

  const response = await fetch(url, {
    method: command.method,
    headers: { "X-API-Key": apiKey, ...(body !== undefined ? { "Content-Type": "application/json" } : {}) },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await response.text();

  if (!response.ok) {
    console.error(`HTTP ${response.status} ${response.statusText} — ${command.method} ${url.pathname}`);
    if (response.status === 401) console.error("提示: 未提供有效凭据，检查 PLANE_API_KEY。");
    if (response.status === 403) console.error("提示: key 无效或无权访问该工作区/项目。");
    if (text) console.error(text.slice(0, 2000));
    process.exit(1);
  }
  if (!text) return;
  if (flags.get("raw")) {
    console.log(text);
    return;
  }
  try {
    console.log(JSON.stringify(JSON.parse(text), null, 2));
  } catch {
    console.log(text);
  }
}

main().catch(error => {
  console.error(error?.message || String(error));
  process.exit(1);
});
