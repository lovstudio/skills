# DSH 插件开发 SOP（完整 grounded 版）

本文件是 `dsh-plugin-creator` skill 的渐进披露参考：SKILL.md 保留精简流程，此处展开每一步的权威出处与门槛细节。每一条均可在仓库内定位（相对路径从仓库根起）。检索日期 2026-08-20。

## 0. 心智模型

- **一切皆插件**：没有特权核心。模型适配器、工具注册表、session log、agent loop 本身都是插件，都可从配置替换；扩展 dsh = 在其它插件旁再挂一个插件。出处 `docs/architecture.md`（Cordis 段）。
- **插件两种形态**（`packages/AGENTS.md`「Plugin exports」）：函数插件（named export `name`/`inject`/`Config`/`apply`，无 default export）或 Service 子类（default export）。混用会被 Loader 丢弃函数插件命名空间（`docs/postmortem/0001-acp-default-export-drops-inject.md`）。
- **注册即副作用**：所有贡献经 `ctx.effect()` / `ctx.on()` / `ctx.waterfall()`；registry 的 `register()` 返回 disposer，卸载自动撤销。出处 `docs/cordis-primer.md`、`packages/README.md`。

## 1. 决定「做什么」与「挂哪里」

1. 查 `docs/architecture.md`「Where new behavior goes」表确定机制。
2. 查 `docs/cookbook/extension-cookbook.md`「feature → mechanism map」找同类 feature 现成机制；没有一行修改 loop。
3. 判断是否需要 capability seam（三角色：Service Definition / Service Provider / Consumer）。一个角色不构成 seam；新增能力要三角色齐。出处 `docs/glossary.md`「capability-seam」。
4. 选现有 group；新 group 是纯容器（无 package.json、无源码，package 在其下一层）。出处 `docs/cookbook/adding-a-package.md`。

## 2. 建 package 骨架

目录（`docs/cookbook/adding-a-package.md`）：

```
packages/<group>/<pkg>/
  package.json
  tsconfig.json
  src/index.ts
  src/types.ts     # 只放类型，无运行时代码
  src/invariant.ts # 每包必须有，构建为 lib/invariant.js
  README.md        # + README.zh.md 双语配对
```

package.json 不变量（由 `scripts/check-workspace-constraints.ts` 强制）：

- `private: true`；`version` 对齐 root；`type: module`。
- `main: lib/index.js`、`types: lib/types/index.d.ts`、`exports["."].types` / `exports["."].default` 指到同上。
- `@deepseek-ai/cordis` 同时进 peerDependencies + devDependencies（同 range）。
- 每个 dsh peer dep 镜像进 devDependencies；`@deepseek-ai/schemastery` 进 dependencies（运行时校验器）。
- `files` 精确为 `lib/index.js`、`lib/invariant.js`、`lib/types/**/*.d.ts`（+ 包特定产物）；不发布 `src`、declaration map、JS map、stale root declaration。

tsconfig：extends `tsconfig.base.json`（Client 用 `tsconfig.base.client.json`），`rootDir: src`、`outDir: lib/types`，references 每个 workspace dep。

注册进聚合：普通 package 只进**一个** aggregate —— Host 进 `tsconfig.host.json`、Client 进 `tsconfig.client.json`。出处 `docs/development.md`「TypeScript project layout」。`api/remotes` 是唯一 split 聚合的例外，勿复制。

## 3. 写插件本体

- 事件 vs service method：事件做拦截/策略，service method 做直接能力调用。出处 `docs/cordis-primer.md`「Practical Rules」。
- waterfall listener 必须 `next()` 委托；return 不 next = 短路。出处 `docs/cordis-primer.md`「Cordis Waterfall Semantics」、`docs/architecture.md`「Turn flow」。
- typed event 用 declaration merging；事件 JSDoc 带 `@mode`。出处 `packages/AGENTS.md`、`docs/cordis-primer.md`「Dispatch Modes」。
- 命名用 role 词表（Controller/Store/Registry/Runtime/Resolver/Provider/Backend/…）命名当下职责，不命名第一个实现/未来扩展/Cordis 基类；ctx key 单复数与 role 一致。出处 `docs/cookbook/adding-a-package.md`「Name the role that exists」。
- Config：部署可变选择做成合法 Config 字段，不写 `DEFAULT_*` 硬编码；显式 `resolve(request): Spec`，不在 `run()` 藏 `?? default`。出处 `packages/AGENTS.md`「No hardcoded tunables」。
- 可选 service 用 `ctx.get(name)`，保留 `ctx.<name>` 给声明式注入。出处 `packages/AGENTS.md`「Optional services」。
- 跨边界 opaque id 用 `Branded<B>`，不裸 string。出处 `packages/AGENTS.md`。
- 生命周期/并发/子进程/teardown 改动先读 `docs/defensive-patterns.md`。

### 工具 `execute()` 契约要点（`docs/cookbook/adding-a-tool.md`）

- args 由 `defineTool` 按统一 schema 校验后传入；仍要手查 DSL 不表达的约束（非空串、正数、跨字段规则）。
- 声明并返回一个 canonical JSON 值；`output.schema` 用 `ValueSchemaSpec`，`output.render(args, value)` 负责模型可见 prose。
- 抛错或返回非法值即 `isError`；基础设施失败抛错，领域内非理想态（如非零退出码）在 canonical 值里表达。
- 尊重 `exec.signal`；异步通知用 `exec.agent`（`agent.inject`），不是唤醒。
- UI 呈现走 `presentCall` / `presentResult` 的 card 意图（generic/terminal/diff/search/web），且必须是 `args`（+result）的纯函数，回放可用。

## 4. invariant

每包 `src/invariant.ts` 注册 manifest 名，检查一个事件/数据关系；否则给 `No runtime invariant:` 理由。由 `verify-package-invariants` 强制。出处 `packages/AGENTS.md`「Every package owns ./invariant」。

## 5. 测试（`docs/testing.md`）

- unit：每个 registry 有 HMR-safety 测试（dispose 贡献 fiber，断言清理）。
- coverage 门禁 `pnpm run test:coverage`：`packages/*/*/src` 每文件 100%（行覆盖必要不充分）。
- product-visible 插件 → 非 unit 的 REAL-composition 测试：手搓 `ctx.plugin(...)` 不够；boot test-only `cordis.yml` 经 Loader/app，mock 只外部 service 或非确定输入，断言 model-visible/durable/user-visible 输出。
- model-/user-visible 变更 → 同 PR 加 keyless snapshot（经 runnable example 的 owning snapshot suite）。
- 每个 example 有 keyless + with-key smoke（无 key 自跳过，CI 仍绿）。

## 6. 文档

- README（`docs/cookbook/adding-a-package.md`「Write the package README」）：service API/config/events/extension points 在前；末尾固定 `## Model Experience`（`What the model sees` / `Token effect` / `KV Cache effect`）+ `## Known Limitations and Deferred Work`。
- 双语：README 需 `.zh.md` 配对，走 i18n contract。出处 `docs/AGENTS.md`「Pairs update together」。
- Agent Note：非平凡变更同 PR 至少一篇；仅机械/局部编辑豁免。出处 `docs/AGENTS.md`「Writing rules」。
- 改了 documented type 同 PR 更新 owning subsystems page（`verify-type-equiv` 抓漂移）。

## 7. 验证（`docs/cookbook/adding-a-package.md`「Verify」）

```sh
pnpm install
pnpm run doc-sync
pnpm run constraints && pnpm run typecheck && pnpm run lint
pnpm run build && pnpm run hygiene
```

再按行为跑相关检查（不默认全量）。出处 `AGENTS.md`「Run relevant checks locally」、`docs/testing.md`。

## 8. 提交

- labels：一个 `kind/*` + 所有 material `area/*`。出处 root `AGENTS.md`「Labels」。
- PR history 刻意拆分；Agent Note 同 PR。

## 常见三类插件速查

| 想做什么 | 机制 | 出处 |
|---|---|---|
| 新增模型可调用工具 | `ctx.tools.register(defineTool({...}))`，schema 自动进 prompt | `docs/cookbook/adding-a-tool.md`、`docs/cookbook/extension-cookbook.md`「A tool plugin」 |
| 拦截/放行工具或请求（权限、沙箱、plan mode） | `ctx.on('tools/pre-execute', (exec, next) => ...)` 返回 typed decision | `docs/cookbook/extension-cookbook.md`「A hook plugin」 |
| 新增可替换能力 | 三角色 seam，参考 `packages/shell` 三件套 | `docs/glossary.md`「capability-seam」 |
| 给模型注入上下文 | `agent.inject({...})`（下一请求可见，非唤醒） | `docs/architecture.md`「Where new behavior goes」 |
| UI 渲染 session | 监听 `session/event`，输入回 `agent.followup()` | `docs/cookbook/extension-cookbook.md`「A UI plugin」 |
