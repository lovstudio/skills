---
name: dsh-plugin-publisher
description: >
  Publish a validated DSH plugin package (`@deepseek-ai/dsh-*` or `@lovstudio/dsh-*`)
  to npm, git, or tarball channels and verify it loads in the DeepSeek Harness.
  Use when the user asks to publish, release, or ship a plugin. 触发：发布插件 / 上架插件 / release dsh 插件。
license: MIT
compatibility: >-
  Author-only name: the skill keeps the unprefixed id `dsh-plugin-publisher`
  (paired with `dsh-plugin-creator`); the standard `lov-` prefix is not used.
  Requires Node.js >= 20, pnpm >= 10, git, and the `dsh` CLI on PATH (or run
  the gates through the repo's `pnpm dsh`). Publishing to npm needs npm auth;
  git/topic operations need the GitHub CLI. Channel metadata stays outside
  canonical source.
metadata:
  author: Lovstudio
  version: "0.3.1"
  tags:
    - dsh-plugin
    - publisher
    - release
    - npm
    - deepseek-harness
  dependencies:
    - dsh-plugin-creator
---

# dsh-plugin-publisher

Publish one validated DSH plugin package to the DeepSeek Harness distribution
channels and verify each channel can load it. Input is the finished package
source produced by `dsh-plugin-creator`; this skill owns everything after the
commit: validation, repo gates, per-channel release, and load verification.

There is **no official DSH plugin marketplace**. The three supported channels
are npm, git, and tarball; GitHub's `dsh-plugin` topic is the discovery
mechanism. Publish the same plugin across as many channels as the user's
distribution intent needs, keep channel state out of canonical source, and
report evidence per channel.

## Triggers

### Activate when

- 用户说“发布这个 DSH 插件”“上架插件”“推到 npm”“打个 release”“导出 tarball 给用户装”。
- The user asks to publish, release, distribute, upload, or package an existing DSH plugin.

### Do not activate when

- 用户要新建、实现或修改插件；交给 `dsh-plugin-creator`。
- 用户只是要本地验证插件可加载（`dsh --profile demo --dump-config`），并没有发布意图。

## Product boundary

- Input is a local plugin package that already passes `dsh-plugin-creator`'s
  gates: `package.json` invariants hold, `dsh.bundle.patch` (or
  `dsh.plugin.json` for the yoda-style registry channel) is present, and no
  stale build artifacts sit in the tree.
- **Publishing updates only the target plugin's code, never the whole
  harness.** A plugin is often developed as a workspace member inside the
  `deepseek-harness` monorepo (e.g. `packages/client/ui-plugin-market`) but
  published from its own repository (e.g. `lovstudio/dsh-plugin-marketplace`;
  such members are listed in `scripts/release/families.ts` as
  `externalRepositoryMembers`). In that case the release diff is the plugin's
  own files only: sync the changed plugin source plus its committed build
  artifacts to the standalone repo, and leave every other harness change
  (unrelated in-flight features, other packages, root manifests) untouched.
  Keep the standalone repo's self-referencing import style — monorepo-internal
  package references such as `@deepseek-ai/dsh-host-plugin-market-github` map
  to the plugin's own exports (`@lovstudio/dsh-plugin-marketplace/...`) and
  must not be copied over.
- When the user does not name a channel, default to npm for `@lovstudio/dsh-*`
  plugins whose `publishConfig.access` is `public`, and to git for plugins
  meant to be consumed from source. Do not ask a channel-selection question
  when the request omits channels.
- A request may select multiple channels in one run.
- Version, visibility, and target account are publishing inputs. Reuse the
  version from the source package; ask only when the user wants a bump that
  the current manifest does not imply.
- Keep channel metadata, credentials, staging files, and archives outside
  canonical source.
- Do not invent a registry or marketplace that does not exist. If the user
  asks to "上架 DSH 市场", explain the three real channels and the
  `dsh-plugin` topic, then proceed on those.

Supported channels in this version:

- **npm** — publish a prebuilt `lib/` (or plain `index.js`) bundle so
  `dsh plugin add <pkg>` installs ready-to-load code.
- **git** — push the source repo, tag a release, and ship a `prepare` script
  so `dsh plugin --profile <name> add github:owner/repo#<sha>` builds on install.
- **tarball** — `pnpm pack` a self-contained archive for offline / review installs.
- **community mirror (optional)** — register an out-of-tree plugin under
  `packages/community/` in the `deepseek-ai/deepseek-harness` repo so it ships
  with the harness source tree.
- **discovery topic** — add the `dsh-plugin` GitHub topic (and, for lovstudio
  plugins, `dsh`, `deepseek-harness`) so the official discovery surface finds it.

For any additional platform, follow `references/publish-dsh.md` and verify its
current official name, submission contract, public URL, and completion signal
before implementing an adapter. Never call an upload dialog a completed
publication.

## Workflow (MANDATORY)

### Step 0: Resolve roots and settings

- Resolve this Skill as `SKILL_DIR`.
- Resolve the plugin source from an explicit path, current directory, or
  conversation. Confirm it is a DSH plugin (has `dsh.bundle` or `dsh.plugin.json`).
- **Distinguish the development tree from the publishing repository.** All
  lovstudio plugins are developed under `~/lovstudio/dsh-plugins/`, one
  standalone git repository per plugin (e.g.
  `~/lovstudio/dsh-plugins/dsh-plugin-marketplace`); each is installed into
  the harness locally for testing and published from its own repository. When
  a plugin still lives inside the `deepseek-harness` monorepo as a workspace
  member, that member is only the source of the plugin's changes and the
  standalone repo is the release target. Confirm which one the user means
  before publishing.
- Resolve the DSH harness checkout (for gates and the optional community
  mirror) from the repo where the plugin was authored, or
  `$DSH_HARNESS` if set. When publishing from a standalone plugin repo, the
  gates run there — not from the harness root.

### Step 1: Validate canonical source

Check that the source has no generated release artifacts, no platform
metadata, and no uncommitted surprises. Record: package name, version,
`dsh.bundle` / `dsh.plugin.json` shape, files field, git state, and whether a
remote already exists.

Key `package.json` invariants (from the harness `packages/AGENTS.md` /
`docs/cookbook/adding-a-package.md`): `type: module`; entry points declared;
`files` exact (no `src`, maps, or stale root declarations); `@deepseek-ai/cordis`
in peer + dev deps at the same range; every dsh peer dep mirrored into devDeps.
A `@lovstudio/dsh-*` external plugin additionally sets
`publishConfig.access: "public"` and `keywords` including `dsh-plugin`.

### Step 2: Run the repo gates

Run the gates from the plugin's own publishing repository — the standalone
repo when the plugin publishes from one, otherwise the harness root. Never run
the whole-harness gate suite for a plugin that publishes from its own repo:

```sh
# Standalone plugin repo
pnpm install
pnpm run typecheck && pnpm run lint && pnpm run build
pnpm pack --dry-run                 # proves the publish payload packs

# Plugin developed inside the harness monorepo but publishing from its own repo:
# validate only the plugin's changed surface (its package tests/build), not the
# harness-wide suite — unrelated in-flight harness changes must not block or
# leak into the plugin release.
```

Then run only the checks the changed surface reaches — do not default to the
full suite. Any failure blocks publication.

### Step 3: Decide channels and release model

If channels are explicit, proceed. If none are named, select npm (for public
`@lovstudio/*`) and/or git (for source installs) and proceed without asking.

For each channel, resolve only required fields:

- version to publish (reuse the manifest version unless the user asked for a bump);
- npm package name, visibility, and dist-tag;
- git remote, tag name, and whether to pin installs to a commit;
- community mirror group under `packages/<group>/` (default `community`).

Do not ask users to choose implementation details such as staging layout,
archive format, or adapter order.

### Step 4: Build a per-channel plan

Read `references/publish-dsh.md`, then execute only the selected channels.
Keep independent state for each target so one failure does not masquerade as a
successful multi-channel release.

**Build the release diff before touching any channel.** The release diff is
the target plugin's own changes only. When the plugin is developed inside the
harness monorepo and published from a standalone repo:

1. Compare the plugin's monorepo member tree against the standalone repo to
   find the functional delta (for example a one-line icon fix). Ignore
   monorepo-internal import-name differences — the standalone repo keeps its
   self-referencing style.
2. Apply only that delta to the standalone repo: the changed source file(s),
   the committed build artifacts they feed (e.g. `lib/client.cjs`), the
   `package.json` version bump, and the `CHANGELOG.md` entry.
3. Do not copy over other harness files, unrelated in-flight features, or the
   root manifests. `git status` in the standalone repo must show exactly the
   plugin release files before committing.

### Step 5: Publish to npm

Read the npm section of `references/publish-dsh.md`. Ensure the build output is
in the published `files` (run `prepublishOnly: pnpm build` if the manifest
declares it). Then:

```sh
pnpm publish --access public
git tag v<VERSION>
git push origin v<VERSION>
```

Record the published version, dist-tag, and the package page URL. Verify with
`npm view <pkg>@<version>` that the exact version and expected files are live.

### Step 6: Publish to git

Read the git section of `references/publish-dsh.md`. Ensure a self-contained
`prepare` script exists (builds entry points from source; no sibling-monorepo
assumptions). Push the release commit and tag, then verify the git-install
path on a clean profile:

```sh
dsh plugin --profile demo add github:<owner>/<repo>#<sha>
```

If pnpm >= 10 blocks the `prepare` script, record the exact package key the
allowlist needs (`allowBuilds` in the profile's `pnpm-workspace.yaml`) as a
follow-up for the user, not as a silent pass.

### Step 7: Ship a tarball

Read the tarball section of `references/publish-dsh.md`. Build a clean archive
outside canonical source:

```sh
pnpm pack --out /tmp/<pkg>-<version>.tgz
dsh plugin --profile demo add /tmp/<pkg>-<version>.tgz
```

Record the archive path, checksum, file count, and the successful `add`.

### Step 8: Community mirror and discovery topic (optional)

When the plugin should ship with the harness, mirror it under
`packages/community/` (follow `docs/cookbook/adding-a-package.md`), or run the
standard `dsh` PR flow for the `deepseek-ai/deepseek-harness` repo. Tag the
GitHub repo with the `dsh-plugin` topic (and `deepseek-harness`). Record the
topic set and the PR/release state.

### Step 9: Verify load in the harness

Whatever the channels, the final gate is that the plugin loads:

```sh
dsh --profile demo --dump-config   # expect a "# == <pkg>" layer
dsh --profile demo                 # boots without error
```

A parsed archive or a pushed tag is only `published`; the plugin is `live`
only when the layer appears and the harness boots.

### Step 10: Multi-channel report

Report each target separately:

| Channel | State | Version/artifact | Evidence | Follow-up |
|---------|-------|------------------|----------|-----------|
| TARGET | prepared/published/live | VALUE | URL or local path | ACTION |

Use precise states. `published` and `live` represent different outcomes.

## Dependencies

- Node.js >= 20, pnpm >= 10
- `dsh` CLI on PATH (or run gates via `pnpm dsh` from the harness source)
- `git` + GitHub CLI for git/topic/release operations
- npm credentials for the npm channel

## Local development

Validate this publisher Skill's own source with the harness gates, or inspect
`references/publish-dsh.md` for the grounded contract behind each step.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## References

- `references/publish-dsh.md` — the grounded per-channel SOP with authoritative sources.
- `dsh-plugin-creator` — the companion skill that produces the validated package this skill publishes.

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
