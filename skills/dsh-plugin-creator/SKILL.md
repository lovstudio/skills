---
name: dsh-plugin-creator
description: Create a @deepseek-ai/dsh-* plugin package end-to-end — choose the extension point or capability seam, scaffold the package, implement the tool/hook/service, and run the repo gates. 触发：新增插件 / 加工具 / 开发 capability。
metadata:
  version: "0.2.0"
  tags: [plugin, package, capability-seam, tool, dsh]
---

# DSH Plugin Creator

Use this skill when adding or modifying a plugin (`@deepseek-ai/dsh-*` package) in this repository. It compresses the repo's extension-point map, package checklist, and testing policy into one ordered procedure. Each step names the authoritative file; the full grounded detail with per-step sources lives in `references/plugin-dev-sop.md`.

## Triggers

Activate when the user asks to add a plugin, package, capability seam, tool, hook, or model provider to this repo.

- "给本项目加一个插件" / "新增一个 capability" / "加一个模型工具" / "封一个 skill"
- "create a dsh plugin", "add a package", "scaffold a tool", "add an llm adapter"

Do not activate when the task only runs a skill, reviews code, or fixes a bug in an existing package without adding a contribution.

## Mental model

- Everything is a plugin; there is no privileged core (`docs/architecture.md`). Extending dsh means mounting a plugin beside the others.
- Two plugin forms (`packages/AGENTS.md` "Plugin exports"): a function plugin exporting `name`/`inject`/`Config`/`apply` with no default export, or a `Service` subclass with a default export. Never mix the forms.
- Every contribution is an effect: `ctx.effect()` / `ctx.on()` / `ctx.waterfall()`. A registry's `register()` returns the disposer, so teardown and hot-reload unwind automatically.

## Workflow

### 1. Decide the mechanism and home

1. Read `docs/architecture.md` "Where new behavior goes" and pick the mechanism: register a `ctx.tools` tool, listen on an `agent/*` / `tools/*` event, or define a new capability seam.
2. Check `docs/cookbook/extension-cookbook.md` "feature → mechanism map" for an existing mechanism before inventing one.
3. A swappable capability needs all three seam roles — Service Definition, Service Provider, Consumer — never one role alone (`docs/glossary.md` capability-seam).
4. Pick an existing group under `packages/<group>/`; a new group is a pure container.

### 2. Scaffold the package

Create `packages/<group>/<pkg>/` with `package.json`, `tsconfig.json`, `src/index.ts`, `src/types.ts` (types only), `src/invariant.ts`, and a bilingual `README.md` + `README.zh.md`. Follow the `package.json` invariants (private, version aligned to root, `type: module`, cordis in both peer and dev deps, exact `files` list) and register the package in exactly one aggregate — `tsconfig.host.json` or `tsconfig.client.json`. Full checklist: `docs/cookbook/adding-a-package.md`.

### 3. Implement the plugin

- Waterfall listeners must call `next()` to delegate; returning without it short-circuits (`docs/cordis-primer.md`).
- Typed events use declaration merging and carry an `@mode` tag.
- Name the current role from the role table (`Controller`/`Store`/`Registry`/`Provider`/`Backend`/…), not the first implementation.
- Deployment-varying choices are `Config` fields, not `DEFAULT_*` constants; explicit `resolve(request): Spec`, no hidden `?? default` in `run()`.
- Optional services use `ctx.get(name)`; cross-boundary ids use `Branded<B>`.
- For a tool, follow the `execute()` contract in `docs/cookbook/adding-a-tool.md`: typed args, one canonical JSON value, honor `exec.signal`, `output.render` owns prose, presenters stay pure.

### 4. Add the invariant

Every package owns `src/invariant.ts` registering its manifest name and checking one event or data relation, or stating `No runtime invariant:` with a reason (`packages/AGENTS.md`).

### 5. Test

Follow `docs/testing.md`: an HMR-safety test for every registry, per-file 100% coverage on `packages/*/*/src`, a non-unit REAL-composition test for any product-visible plugin, and a keyless snapshot in the same PR for any model- or user-visible change.

### 6. Document

Write the package `README.md` with service API, config, events, and extension points first, then the canonical `## Model Experience` and `## Known Limitations and Deferred Work` sequence. Pair it with `README.zh.md`, and add an Agent Note in the same PR for any non-trivial change.

### 7. Verify

```sh
pnpm install
pnpm run doc-sync
pnpm run constraints && pnpm run typecheck && pnpm run lint
pnpm run build && pnpm run hygiene
```

Then run only the checks the changed surface reaches — do not default to the full suite.

### 8. Commit

Split independent changes; label `kind/*` plus every material `area/*`; keep the Agent Note in the same PR.

## References

- `references/plugin-dev-sop.md` — the full grounded SOP with per-step sources.
- `references/skill-composition.md` — how this skill hands off to the `dsh-*` skill family.

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
