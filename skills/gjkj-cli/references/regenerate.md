# 重新生成随附的 CLI

`assets/cli/` 是 `lov-cli2anything`（cli2anything++，suanli.cn 适配器）的生成物：`openapi.json`（OpenAPI 3.1，83 个操作，
每个操作带 `x-evidence` 与 `x-observation`）、`sdk/index.mjs`、`bin/lov-suanli-cli.mjs`、`swagger/`、`manifest.json`、`api-graph.json`。
不要手改这些文件；接口有变化时整体重新生成。

1. 用 `lov-cli2anything` 的 suanli.cn 适配器重新生成到一个临时目录（发现证据来自官方公开文档与 Apifox 公开分享，无需登录；
   若要把实测结果并入，按该 Skill 的规则只记录全部成功的只读调用）。
2. 校验：`manifest.json` 的 `operationCount`、`secretsIncluded: false`；`node --check` 三个入口；`lov-suanli-cli --help`。
3. 用新目录整体替换 `assets/cli/`（保留目录名），跑 `python3 scripts/gjkj_cli.py doctor`（`operations == manifest_operations`）
   和一次只读调用（如 `run -- storage-get-regions`）。
4. 按 [commands.md](commands.md) 核对命令名是否变化；更新 SKILL.md 中的接口数、版本、CHANGELOG，三处 version 同步。

命令名由 operationId 转 kebab-case 得到；`gjkj_cli.py` 的写操作、加密、实测标记都直接读 `openapi.json`，无需另外维护。
