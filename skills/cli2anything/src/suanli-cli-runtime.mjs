#!/usr/bin/env node
// lov-suanli-cli — schema 驱动的共绩算力 Open API 与大模型云服务命令行。
// 命令表由随包分发的 openapi.json 在启动时构建；签名、加密与鉴权头交给 ../sdk/index.mjs。
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { KEYCHAIN_SERVICES, SuanliClient, readKeychainSecret } from "../sdk/index.mjs";

const PKG_DIR = dirname(dirname(fileURLToPath(import.meta.url)));
const CLI = "lov-suanli-cli";
const METHODS = ["get", "post", "put", "patch", "delete"];
const GLOBAL_FLAGS = new Set(["data", "raw", "dry_run", "help", "confirm_write", "token", "api_version", "private_key_file", "platform_public_key_file", "llm_api_key", "envelope"]);

const kebab = s => String(s).replace(/_/g, "-").replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();

function buildCommands(spec) {
  const commands = new Map();
  for (const [path, item] of Object.entries(spec.paths || {})) {
    for (const [method, op] of Object.entries(item)) {
      if (!METHODS.includes(method)) continue;
      const name = kebab(op.operationId);
      const params = op.parameters || [];
      commands.set(name, {
        name,
        operationId: op.operationId,
        method: method.toUpperCase(),
        path,
        summary: (op.summary || "").trim(),
        tag: (op.tags || ["其他"])[0],
        llm: Boolean(op.security?.some(s => "LlmBearer" in s)),
        queryParams: params.filter(p => p.in === "query"),
        hasBody: Boolean(op.requestBody),
        bodyRequired: Boolean(op.requestBody?.required),
        write: Boolean(op["x-write-operation"]),
        encryption: Boolean(op["x-suanli-auth"]?.encryption),
        observation: op["x-observation"],
      });
    }
  }
  return commands;
}

function parseArgs(argv) {
  const flags = new Map();
  const positional = [];
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      positional.push(token);
      continue;
    }
    const raw = token.slice(2);
    const eq = raw.indexOf("=");
    const key = (eq < 0 ? raw : raw.slice(0, eq)).replace(/-/g, "_");
    if (eq >= 0) {
      flags.set(key, raw.slice(eq + 1));
      continue;
    }
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) flags.set(key, true);
    else {
      flags.set(key, next);
      i += 1;
    }
  }
  return { flags, positional };
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

function buildQuery(command, flags) {
  const query = {};
  const known = new Map(command.queryParams.map(p => [p.name.replace(/-/g, "_"), p.name]));
  for (const [key, value] of flags) {
    if (GLOBAL_FLAGS.has(key)) continue;
    if (!known.has(key)) throw new Error(`未知参数 --${kebab(key)}；用 ${CLI} ${command.name} --help 查看可用参数`);
    query[known.get(key)] = value === true ? "true" : String(value);
  }
  for (const p of command.queryParams) {
    if (p.required && query[p.name] === undefined) throw new Error(`缺少必填参数 --${kebab(p.name)}`);
  }
  return query;
}

function usage(commands, spec) {
  const byTag = new Map();
  for (const c of commands.values()) {
    if (!byTag.has(c.tag)) byTag.set(c.tag, []);
    byTag.get(c.tag).push(c);
  }
  const lines = [
    `${CLI} — ${spec.info?.title || "共绩算力 API"}（${commands.size} 个操作）`,
    "",
    "用法:",
    `  ${CLI} <command> [--<查询参数> 值] [--data '<json>'|@file.json]`,
    "",
    "全局选项:",
    "  --dry-run          只打印将要发出的请求（凭据只显示是否已提供），不调用",
    "  --confirm-write    写操作必须带上才会发出",
    "  --raw              输出原始响应体",
    "  --envelope         Open API 输出完整 {code,message,data}，默认只输出 data",
    "  --api-version <v>  请求头 version，默认 1.0.0",
    "  --help             查看某个命令的参数",
    "",
    "凭据（环境变量优先，缺失时读 macOS 钥匙串；都不落盘）:",
    "  SUANLI_TOKEN                      Open API 密钥（console.suanli.cn/settings/key）",
    `                                    或钥匙串条目 ${KEYCHAIN_SERVICES.token}`,
    "  SUANLI_PRIVATE_KEY_FILE           可选：设置后按 RSA 模式生成 sign_str",
    "  SUANLI_PLATFORM_PUBLIC_KEY_FILE   加密接口需要：平台返回的公钥",
    "  SUANLI_LLM_API_KEY                大模型云服务 API Key（console.suanli.cn/models）",
    `                                    或钥匙串条目 ${KEYCHAIN_SERVICES.llmApiKey}`,
    "  SUANLI_KEYCHAIN=0                 不读钥匙串",
    "",
    "存入钥匙串（会提示输入两次，不回显）:",
    `  security add-generic-password -a "$USER" -s ${KEYCHAIN_SERVICES.token} -w`,
    "",
    "命令（W = 写操作，E = 请求体需加密）:",
  ];
  for (const tag of byTag.keys()) {
    lines.push(`  ${tag}`);
    for (const c of byTag.get(tag)) {
      const marks = `${c.write ? "W" : " "}${c.encryption ? "E" : " "}`;
      lines.push(`    ${c.name.padEnd(56)} ${c.method} ${c.path} ${marks}`.trimEnd());
    }
  }
  return lines.join("\n");
}

function commandHelp(command) {
  const lines = [`${command.name} — ${command.summary}`, `${command.method} ${command.path}`, ""];
  if (command.write) lines.push("写操作：需 --confirm-write 才会发出。", "");
  if (command.encryption) lines.push("请求体需加密：只能用 RSA 模式（SUANLI_PRIVATE_KEY_FILE 与 SUANLI_PLATFORM_PUBLIC_KEY_FILE）。", "");
  if (command.queryParams.length) {
    lines.push("查询参数:");
    for (const p of command.queryParams) lines.push(`  --${kebab(p.name).padEnd(24)} ${p.required ? "（必填）" : ""}${String(p.description || "").split("\n")[0]}`);
    lines.push("");
  }
  if (command.hasBody) lines.push(`请求体: --data '<json>' 或 --data @file.json${command.bodyRequired ? "（必填）" : ""}`, "");
  lines.push(`证据: ${command.observation}（未带凭据实测）`);
  return lines.join("\n");
}

// 取值顺序：命令行参数 → 环境变量 → macOS 钥匙串；空字符串视为未提供。
function resolveCredential(command, flags) {
  const [flag, envName, service] = command.llm
    ? ["llm_api_key", "SUANLI_LLM_API_KEY", KEYCHAIN_SERVICES.llmApiKey]
    : ["token", "SUANLI_TOKEN", KEYCHAIN_SERVICES.token];
  const fromFlag = flags.get(flag);
  if (typeof fromFlag === "string" && fromFlag) return { value: fromFlag, source: "flag" };
  if (process.env[envName]) return { value: process.env[envName], source: "env" };
  const fromKeychain = readKeychainSecret(service);
  return fromKeychain ? { value: fromKeychain, source: "keychain" } : { value: undefined, source: null };
}

function redactHeaders(headers) {
  const out = { ...headers };
  if (out.token) out.token = "<已提供>";
  if (out.sign_str) out.sign_str = "<已生成>";
  if (out.Authorization) out.Authorization = "Bearer <已提供>";
  return out;
}

async function main() {
  const argv = process.argv.slice(2);
  const spec = JSON.parse(await readFile(resolve(PKG_DIR, "openapi.json"), "utf8"));
  const commands = buildCommands(spec);
  if (["--version", "-v", "version"].includes(argv[0])) {
    console.log(JSON.parse(await readFile(resolve(PKG_DIR, "package.json"), "utf8")).version);
    return;
  }
  if (!argv[0] || ["help", "--help", "-h"].includes(argv[0])) {
    console.log(usage(commands, spec));
    return;
  }
  const command = commands.get(argv[0]);
  if (!command) {
    const near = [...commands.keys()].filter(k => k.includes(argv[0].split("-")[0])).slice(0, 8);
    console.error(`未知命令: ${argv[0]}`);
    if (near.length) console.error(`可能想用: ${near.join(", ")}`);
    process.exit(1);
  }
  const { flags, positional } = parseArgs(argv.slice(1));
  if (positional.length) throw new Error(`不接受位置参数：${positional.join(" ")}；查询参数用 --name 值`);
  if (flags.has("help")) {
    console.log(commandHelp(command));
    return;
  }

  const query = buildQuery(command, flags);
  const body = await readBody(flags.get("data"));
  if (command.bodyRequired && body === undefined && !flags.get("dry_run")) throw new Error(`${command.name} 需要请求体：--data '<json>' 或 --data @file.json`);
  const credential = resolveCredential(command, flags);
  const client = new SuanliClient({
    token: command.llm ? undefined : credential.value,
    version: typeof flags.get("api_version") === "string" ? flags.get("api_version") : undefined,
    llmApiKey: command.llm ? credential.value : undefined,
    privateKey: typeof flags.get("private_key_file") === "string" ? await readFile(resolve(flags.get("private_key_file")), "utf8") : undefined,
    platformPublicKey: typeof flags.get("platform_public_key_file") === "string" ? await readFile(resolve(flags.get("platform_public_key_file")), "utf8") : undefined,
  });

  if (flags.get("dry_run")) {
    if (command.llm) {
      const prepared = client.prepareLlm(command.method, command.path, { body });
      console.log(JSON.stringify({ operationId: command.operationId, method: prepared.init.method, url: prepared.url, headers: redactHeaders(prepared.init.headers), hasCredential: Boolean(client.llmApiKey), credentialSource: credential.source, body: body ?? null }, null, 2));
      return;
    }
    const prepared = client.prepare(command.method, command.path, { query, body, encryption: command.encryption && Boolean(client.privateKey && client.platformPublicKey) });
    console.log(JSON.stringify({
      operationId: command.operationId,
      method: prepared.init.method,
      url: prepared.url,
      mode: prepared.mode,
      headers: redactHeaders(prepared.init.headers),
      hasCredential: Boolean(client.token),
      credentialSource: credential.source,
      signed: prepared.signed,
      encrypted: prepared.encrypted,
      encryptionRequired: command.encryption,
      write: command.write,
      body: body ?? null,
    }, null, 2));
    return;
  }

  if (command.write && !flags.get("confirm_write")) {
    console.error(`${command.name} 是写操作（${command.method} ${command.path}），会改变账户资源或产生费用。确认后加 --confirm-write 重试，或先用 --dry-run 检查请求。`);
    process.exit(3);
  }

  if (command.llm) {
    if (!client.llmApiKey) {
      console.error(`缺少大模型 API Key：设置 SUANLI_LLM_API_KEY，或存入钥匙串：security add-generic-password -a "$USER" -s ${KEYCHAIN_SERVICES.llmApiKey} -w（Key 在 console.suanli.cn/models 的 API 密钥页创建）。`);
      process.exit(2);
    }
    const result = await client.llmRequest(command.method, command.path, { body });
    if (body?.stream) {
      for await (const chunk of result.body) process.stdout.write(chunk);
      return;
    }
    console.log(flags.get("raw") ? JSON.stringify(result) : JSON.stringify(result, null, 2));
    return;
  }
  if (!client.token) {
    console.error(`缺少 API 密钥：设置 SUANLI_TOKEN，或存入钥匙串：security add-generic-password -a "$USER" -s ${KEYCHAIN_SERVICES.token} -w`);
    console.error("密钥在 console.suanli.cn/settings/key 创建；团队账号下开发者角色不能创建，需向主账号或管理员索取。");
    process.exit(2);
  }
  const result = await client.request(command.method, command.path, { query, body, encryption: command.encryption, envelope: Boolean(flags.get("envelope") || flags.get("raw")) });
  console.log(flags.get("raw") ? JSON.stringify(result) : JSON.stringify(result, null, 2));
}

main().catch(error => {
  console.error(error?.message || String(error));
  if (error?.code) console.error(`code: ${error.code}`);
  process.exit(1);
});
