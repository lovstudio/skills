import test from "node:test";
import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readFile, rm } from "node:fs/promises";

const execFileAsync = promisify(execFile);

test("cli2anything++ generates a standalone dshfind CLI bundle", async () => {
  const out = "tmp/cli-dshfind-com";
  await rm(out, { recursive: true, force: true });

  await execFileAsync(process.execPath, [
    "./bin/cli2anything.mjs",
    "https://dshfind.com/zh/plugins",
    "--output",
    "cli",
    "--no-open",
    "--no-link",
    "--discovery",
    "./artifacts/dshfind-discovered.json",
    "--out",
    out
  ]);

  const manifest = JSON.parse(await readFile(`${out}/manifest.json`, "utf8"));
  const openapi = JSON.parse(await readFile(`${out}/openapi.json`, "utf8"));
  const apiGraph = JSON.parse(await readFile(`${out}/api-graph.json`, "utf8"));
  const packageJson = JSON.parse(await readFile(`${out}/package.json`, "utf8"));
  const apifox = JSON.parse(await readFile(`${out}/apifox/openapi.json`, "utf8"));
  const apifoxReadme = await readFile(`${out}/apifox/README.md`, "utf8");
  const graphqlSchema = await readFile(`${out}/apifox/graphql.schema.graphql`, "utf8");
  const cliPath = `${out}/bin/cli-dshfind-com.mjs`;
  const cli = await readFile(cliPath, "utf8");

  assert.equal(manifest.target, "dshfind.com");
  assert.equal(manifest.adapter, "dshfind");
  assert.equal(manifest.scope, "plugins");
  assert.equal(openapi.openapi, "3.1.0");
  assert.equal(apiGraph.defaultWorkflowId, "dshfind-plugin-discovery");
  assert.equal(packageJson.name, "cli-dshfind-com");
  assert.equal(manifest.outputs.apifox, "apifox/openapi.json");
  assert.equal(apifox.servers[0].url, "https://api.dshfind.com");
  assert.deepEqual(apifox.security, []);
  assert.match(apifoxReadme, /自动生成接口用例/);
  assert.match(cli, /plugins:list/);
  assert.match(cli, /plugins:categories/);
  assert.match(cli, /graphql:dataset/);
  assert.match(cli, /graphql:facets/);
  assert.match(cli, /graphql:list/);
  assert.match(cli, /graphql:get/);
  assert.match(cli, /graphql:query/);
  assert.match(cli, /graphql:schema/);
  assert.match(cli, /plugins:get/);
  assert.match(cli, /market:list/);
  assert.doesNotMatch(cli, /Cookie|Token|Authorization/);
  assert.match(await readFile(`${out}/sdk/index.mjs`, "utf8"), /DshFindClient/);
  assert.match(graphqlSchema, /type Query/);
  assert.match(graphqlSchema, /pluginFacets: PluginFacets!/);

  await execFileAsync(process.execPath, ["--check", cliPath]);
  const { stdout } = await execFileAsync(process.execPath, [cliPath]);
  assert.match(stdout, /public dshfind plugin directory/);

  await rm(out, { recursive: true, force: true });
});
