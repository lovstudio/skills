---
name: lov-npm-publisher
description: >
  为全新或已有 npm 包建立免重复登录的自动发布链，兼容 GitHub Actions OIDC（trusted publishing）与本地 granular NPM_TOKEN（bypass）两种平级方式，处理首次引导、发布审计与线上回读。Use when the user asks to 自动发布 npm 包、publish npm without login、发布 npm 包不用登录。
license: MIT
compatibility: "Python 3.9+, git, npm, and a GitHub-hosted Actions runner. Trusted publishing requires a currently supported Node/npm combination; bypass uses a granular NPM_TOKEN."
metadata:
  author: contributors
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - npm
    - trusted-publishing
    - oidc
    - bypass-2fa
    - github-actions
    - release-automation
  dependencies: []
---

# lov-npm-publisher

把 npm 包从“每次登录或维护长期 token”迁移到可审计的自动发布链。支持两种平级的认证方式：

- **oidc** — GitHub Actions trusted publishing，CI 免长期 token（推荐给 GitHub 仓库的持续发版）；
- **bypass** — 本地 granular NPM_TOKEN，直接 `npm publish`（适合本地快速发布、无 CI 的包）。

输出必须区分首次引导、认证配置、发布执行和 registry 回读，不能把工作流生成等同于已经发布。

## Triggers

### Activate when

- 用户说“自动发布 npm 包”“发布新 npm 包但不要每次登录”“把 npm 发版改成 GitHub Actions”。
- 用户说“用 NPM_TOKEN 本地发布这个包”“publish this npm package locally without login”。
- User says “publish npm without login”, “automate npm releases”, or “set up tokenless npm publishing”.
- 用户需要批量判断包是否首次发布、选择 OIDC 还是 NPM_TOKEN，或验证发版是否真的上线。

### Do not activate when

- 发布的是 Agent Skill 而不是 npm package；使用 `lov-skill-publisher`。
- 只做通用 GitHub Release、Tauri 签名或多平台 CI/CD；使用 `lov-release-via-cicd`。
- 用户只问 npm 认证原理而不要求配置或发布；直接解释，不修改仓库。

## User Profile (cross-session)

Read `skill.yaml` on every invocation. Resolve the current request, project
context, Skill records, shared preferences, and the shared user/brand Profile in
that order. Keep repository names, workflow choices, and credentials out of the
portable source unless the user explicitly asks to persist a non-secret default.

Persist only direct durable statements through `scripts/profile_store.py` and
report the canonical Profile path. Never persist npm tokens, OTP values, cookies,
OIDC assertions, or secret-like environment values. See
`references/user-profile.md` for the full contract.

## Skill Group Composition

Read `references/skill-composition.md` before invoking an adjacent Skill. Sibling
Skills are optional artifact-level handoffs, not hidden runtime dependencies.

## Workflow (MANDATORY)

Follow these steps in order.

### Step 0: Resolve runtime and current npm rules

1. Resolve this source as `SKILL_DIR` and the target package directory from the
   request or current working directory.
2. Read `references/npm-publishing-contract.md` and recheck the linked npm
   documentation when authentication behavior, supported runners, or deprecation
   dates could have changed.
3. Read `references/skill-composition.md` before choosing an optional handoff.
4. Verify `package.json`, git, npm, and `scripts/publish.py` exist. Do not
   request or print credentials during this read-only phase.

### Step 1: Audit without changing external state

Run the planner first:

```bash
python3 "$SKILL_DIR/scripts/publish.py" PACKAGE_DIR --dry-run --json
```

The audit must establish:

- package name, version, visibility, `private` flag, registry, and repository URL;
- GitHub owner/repository and the exact workflow filename;
- whether the package exists on the npm registry and whether this exact version
  already exists;
- whether an existing workflow contains `id-token: write`, `npm publish`, and no
  long-lived publish secret;
- whether the state is `bootstrap_required`, `package_exists`, or
  `registry_unknown`.

Do not turn a timeout, authorization error, or registry outage into “package does
not exist”. Stop before publication when registry state is unknown.

### Step 2: Select the authentication path

The planner emits `auth.mode` as `oidc` or `bypass`. With `--auth-mode auto`
(the default), it resolves to `oidc` when a GitHub repository resolves and
`bypass` otherwise; pass `--auth-mode oidc|bypass` to override inference. Both
modes are first-class and equal; prefer `oidc` for GitHub-repository continuous
releases and `bypass` for local, CI-less, or new-package publication.

#### oidc — GitHub trusted publishing

Trusted publishing cannot be registered for a name that does not yet exist. For
`bootstrap_required`, explain that one interactive identity proof is unavoidable,
then perform it only when the request authorizes publication:

```bash
npm login
npm publish --access public
```

Re-read the exact package and version from the npm registry. A successful command
without registry visibility is not completion.

For `package_exists`, configure or verify the exact repository/workflow binding.
With a current npm CLI, the plan emits a command shaped like:

```bash
npm trust github PACKAGE --repo OWNER/REPO --file publish.yml --allow-publish
```

This management action requires interactive identity proof. If it was already
configured, verify the existing binding rather than replacing it blindly.

#### bypass — local granular NPM_TOKEN

A granular (Bypass-2FA) `npm_` token publishes directly, including new packages.
Detect the token without reading its value; `auth.token` reports whether
`NPM_TOKEN` or a `~/.npmrc` `_authToken` is present. When it is missing, warn and
request a granular token before publishing. `auth.publish_command` carries the
exact command; never echo the token value.

### Step 3: Generate the workflow or the publish command

After resolving blocking audit errors, materialize the mode-specific artifact:

```bash
python3 "$SKILL_DIR/scripts/publish.py" PACKAGE_DIR --write --json
```

For `oidc`, the writer emits the tokenless workflow. It is conservative:

- it preserves an equivalent OIDC workflow;
- it refuses to replace an unrelated or token-based workflow unless `--force`
  is explicitly justified;
- it never writes `NPM_TOKEN`, an npm access token, or an OTP;
- it grants only `contents: read` and `id-token: write`;
- it uses a hosted runner and lockfile-aware install command;
- it runs build and test scripts when present before `npm publish`.

Review the diff. The package's `repository.url` must match the GitHub repository
used by the trusted publisher; fix the package metadata before publishing when it
does not match.

For `bypass`, the writer sets `write_state` to `not-applicable` — no workflow is
generated. Use the `auth.publish_command` from the plan as the release command.

### Step 4: Run the release gate

Before triggering the workflow:

1. Confirm the requested version is not already present. npm versions are
   immutable; never retry by overwriting the same version.
2. Run the package's existing test and build gates.
3. Inspect the payload with `npm pack --dry-run --json`; reject secrets,
   unintended source files, private paths, or missing build output.
4. Confirm the release commit is clean and contains the workflow and package
   version intended for the tag.
5. Do not expose credentials in command output or logs.

### Step 5: Trigger and verify the release

Only when the user asked to publish, act by mode:

- `oidc` — create/push the intended version tag or run the configured manual
  workflow, then follow the GitHub Actions run to a terminal state.
- `bypass` — run `auth.publish_command` from the plan against the granular
  `NPM_TOKEN`.

Then verify independently:

```bash
npm view PACKAGE@VERSION version --registry https://registry.npmjs.org
```

For public repositories, also check the npm provenance record when supported.
Report the exact version, workflow run (or local publish), registry result, and
provenance state. `queued`, `in_progress`, a generated YAML file, or an accepted
`npm publish` request is not equivalent to a live package version. A root
endpoint `404` right after publish can be CDN lag; re-read the specific version
endpoint before concluding failure.

### Step 6: Report the state precisely

Use these states:

- `audited` — repository and registry state classified;
- `bootstrap-required` — package name does not yet exist;
- `workflow-written` — tokenless OIDC workflow exists locally;
- `trusted-publisher-configured` — npm binding was verified;
- `publish-command-ready` — bypass mode resolved a publish command and token;
- `publish-triggered` — CI accepted the release request;
- `published` — publish (CI or local) finished successfully;
- `verified-live` — exact package and version were read back from npm;
- `blocked` — name the missing identity proof, registry evidence, or failed gate.

## Validation

Exercise both registry branches and both auth modes without external writes:

```bash
python3 scripts/publish.py CASE_DIR --registry-state missing --dry-run --json
python3 scripts/publish.py CASE_DIR --registry-state exists --dry-run --json
python3 scripts/publish.py CASE_DIR --auth-mode oidc --dry-run --json
python3 scripts/publish.py CASE_DIR --auth-mode bypass --dry-run --json
python3 scripts/validate_skill.py .
```

An activation check should route “帮我把这个新 npm 包自动发布，以后不要登录”
and “用 NPM_TOKEN 本地发布这个包” here. “把这个 Agent Skill 上架到
LovStudio” must stay with `lov-skill-publisher`.

## Dependencies

- Python 3.9+ standard library for the planner/writer.
- Git and a valid GitHub repository for automatic repository inference.
- Node/npm versions currently supported by npm Trusted Publishing.
- PyYAML only for local Skill source validation.
- npm/GitHub authentication is required only for the authorized external setup
  and publish steps; no credential is stored by this Skill.
