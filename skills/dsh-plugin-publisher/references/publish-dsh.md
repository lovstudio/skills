# DSH 插件发布 SOP（grounded 版）

本文件是 `dsh-plugin-publisher` skill 的渐进披露参考：SKILL.md 保留精简流程，此处展开每一步的权威出处与判据。每一条均可在仓库内定位（相对路径从仓库根起）。检索日期 2026-08-20。

权威来源：`deepseek-ai/deepseek-harness` 仓库 `docs/user/develop/basic/publish.md`（Package and install a plugin）、`docs/cookbook/adding-a-package.md`、`packages/AGENTS.md`；`dsh-plugin-creator` skill 的 `references/plugin-dev-sop.md` 提供仓库门槛。

## 0. 心智模型

- **bundle vs profile**：bundle 是"这个包贡献什么"（`dsh.bundle.patch` → `cordis.patch.yml`）；profile 是"哪些 bundle 按什么顺序组成一次可启动运行"（`dsh.profile.bundles`）。bundle 是作者分发物，profile 是用户 `dsh --profile <name>` 启动的组合。两者互斥。出处 `docs/user/develop/basic/publish.md`「Two concepts, two manifests」。
- **没有官方插件市场**。官方发现机制 = GitHub `dsh-plugin` topic；分发 = npm / git / tarball 三渠道。出处 `dsh-smart-find` 调研（"官方只提供一个发现机制——GitHub 的 dsh-plugin topic"）。
- **加载顺序**：空根 → profile `bundles` 列表按序（`@deepseek-ai/dsh-base` 最先）→ profile 自身 `cordis.patch.yml` → `$DSH_HOME/cordis.patch.yml` → 每个 `--patch` argv 覆盖层。后层按行覆盖；patch 替换整行 `config`，不深合并。出处 publish.md「The loading order」。

## 1. 前置验证（Step 1）

package.json 不变量（`packages/AGENTS.md` / `docs/cookbook/adding-a-package.md`，由 `scripts/check-workspace-constraints.ts` 强制）：

- `private: false`（要发布）；`version` 对齐 root；`type: module`。
- `main`/`exports` 指向构建产物；`files` 精确列出（`@lovstudio/dsh-*` 外部插件典型为 `index.js` + `cordis.patch.yml`，见 `dsh-inject-system-prompt`）。
- `@deepseek-ai/cordis` 同 range 进 peer + devDeps；每个 dsh peer dep 镜像进 devDeps。
- `@lovstudio/dsh-*` 外部插件：`publishConfig.access: "public"` + `keywords` 含 `dsh-plugin`。

## 2. 仓库门槛（Step 2）

```sh
pnpm install
pnpm run doc-sync
pnpm run constraints && pnpm run typecheck && pnpm run lint
pnpm run build && pnpm run hygiene
```

再按行为跑相关检查（不默认全量）。`lefthook.yml` pre-push 只跑 `pnpm run typecheck`；pre-commit 跑 staged lint / whitespace / 翻译配对 / 第三方声明。CI 负责全矩阵。出处 plugin-dev-sop.md §7、harness `AGENTS.md`。

## 3. npm 渠道（Step 5）

判据：包名公开（`@lovstudio/dsh-*` 或 `@deepseek-ai/dsh-*` 对外包），`publishConfig.access: "public"`，发布时 `lib/`（或 `index.js`）已在 `files` 内。有 `prepublishOnly: pnpm build` 则发布前自动构建。

```sh
pnpm publish --access public
git tag v<VERSION> && git push origin v<VERSION>
npm view <pkg>@<version>    # 验证确切版本 + 期望文件已在 npm 上
```

用户安装：`dsh plugin --profile <name> add <pkg>` —— 装的是预构建产物，无需构建权限。出处 publish.md「Give a surface bundle」前的 npm 说明。

## 4. git 渠道（Step 6）

判据：git install 拿的是源码不是构建产物，pnpm 不会跑 `build`，所以作者必须提供自包含的 `prepare` 脚本（构建入口点；不得假设 sibling monorepo checkout 等 dev-only 上下文）。`turtle-ui` 是工作范例（专用 tsdown config 只转译 `src/`，不做 project references / typecheck）。

```sh
git add -A && git commit -m "release: v<version>"
git push origin main && git tag v<version> && git push origin v<version>
dsh plugin --profile demo add github:<owner>/<repo>#<sha>
```

pnpm ≥10 会拒绝运行 git 依赖的 `prepare` 脚本，直到 profile 的 `pnpm-workspace.yaml` 显式 allowBuilds：

```yaml
allowBuilds:
  <pkg>: true
```

该 allowlist = "允许在安装时执行该包代码"（agent 沙箱外），只 allow 信任来源，并建议 pin commit。首次 `add` 失败时把 pnpm 打印的精确 package key 抄进 allowlist 再重试；不要静默跳过。出处 publish.md「Installing from GitHub: the build-script catch」。

## 5. tarball 渠道（Step 7）

```sh
pnpm pack --out /tmp/<pkg>-<version>.tgz
dsh plugin --profile demo add /tmp/<pkg>-<version>.tgz
shasum /tmp/<pkg>-<version>.tgz
```

构建产物在包内，无需构建权限。出处 publish.md（"Ship a tarball from `pnpm pack`"）。

## 6. community 镜像（Step 8，可选）

harness 内 `packages/community/` 放 out-of-tree / community 插件（现有 `smart-find`）。照 `docs/cookbook/adding-a-package.md` 建骨架；host/client 聚合注册进 `tsconfig.host.json` / `tsconfig.client.json` 之一，不重复。出处 plugin-dev-sop.md §2。

## 7. 验证可加载（Step 9）

```sh
dsh --profile demo --dump-config   # 期望出现 "# == <pkg>" layer
dsh --profile demo                 # 无错启动
```

`dump-config` 显示 layer 才算装上；启动成功才算 `live`。`uploaded`/`published` ≠ `live`。出处 publish.md「Install into a profile」、SKILL.md Step 9。

## 8. 分渠道报告（Step 10）

| Channel | State | Version/artifact | Evidence | Follow-up |
|---------|-------|------------------|----------|-----------|
| npm | published/live | v0.x.y | npm 包页 URL + `npm view` 输出 | 无 |
| git | pushed/live | tag | repo commit/tag | allowBuilds 提示（如遇） |
| tarball | prepared/live | 路径 + checksum | `add` 输出 | 无 |
| community | PR/review | 镜像路径 | PR URL | review 状态 |
| topic | set | — | repo topics 列表 | 无 |

状态词严格：`prepared` / `published` / `pushed` / `live` 是不同的结果，不得混用。
