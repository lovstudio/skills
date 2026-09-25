---
name: lov-dev-to-prod
description: >
  将开发态项目收敛为可验证的生产构建与本地安装成果：适用于“把 dev 转成 prod” “生产就绪检查”或 “turn this dev app into a production build”，覆盖配置、构建、签名、安装和发布交接边界。
license: MIT
allowed-tools:
  - Bash
metadata:
  author: LovStudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - production-readiness
    - local-install
    - desktop
    - tauri
    - electron
    - release-handoff
  compatibility: "Portable Agent Skills format. Python 3.8+ standard library; target-project build and native verification tools as applicable."
  dependencies: []
---

# 生产就绪助手 · Production Readiness

将一个仍以开发命令、调试配置或本机服务为中心的项目，收敛成可复查的生产制品。
它先确定交付范围，再修复阻塞项，最后用真实构建、签名或安装证据确认结果；外部发布始终是显式的下一步，而非默认副作用。

## Product contract

- **输入**：目标项目、预期交付范围（本地安装、可分发制品或外部发布前准备）、目标平台，以及已有的构建/签名配置。
- **输出**：生产就绪报告、最小必要的项目改动、实际构建与验证结果，以及在明确授权时的本地安装证据。
- **不承诺**：没有真实构建和运行验证时，不称为“生产就绪”；未获明确授权时，不创建发布、标签、上传或商店提交。

## Triggers

### Activate when

- 用户说“把这个项目从 dev 转成 prod”“帮我做生产就绪检查”“打一个可安装的正式包”或“把开发态应用装到本机应用程序”。
- User asks to “turn this dev app into a production build”, “prepare this project for production”, or “make a verified local desktop install”.
- 用户已有 Tauri、Electron、原生桌面或 Web 项目，需要确认开发服务器、环境变量、构建命令、签名与安装边界后再交给发布流程。

### Do not activate when

- 用户要把版本公开发布到 GitHub、官网、商店或 CI/CD；交给 `lov-app-release` 或 `lov-release-via-cicd`，由它们拥有远端状态与发布回读。
- 用户只要诊断普通功能错误、单项 UI 修改或代码重构；交给相应的修复、设计或重构 Skill。
- 用户的目标是性能、内存或后台任务优化而不是生产构建；交给 `lov-app-optimizer`。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Read `skill.yaml` and resolve the shared Profile before inspecting the project.
- Use `SKILL_DIR` when provided; otherwise infer this installed Skill root from the active runtime.
- Read [the composition record](references/skill-composition.md) and [the production checklist](references/production-readiness.md) before deciding scope.
- Verify that `scripts/production_audit.py`, `references/production-readiness.md`, and the target project rules are available. If a required local resource is missing, name its relative path and stop before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="$(pwd)"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Freeze the production target and authority

- Separate three scopes: **local production install**, **signed distributable artifact**, and **external public release**. Never infer the third from the first two.
- Read the target repository's instructions, build configuration, version sources, package manager, and current worktree. Preserve unrelated changes.
- Confirm only the missing user-facing choice that changes the outcome: platform, intended destination, or whether external publication is authorized.
- State the acceptance condition before editing. Examples: a macOS `.app` passes signature and Gatekeeper checks; a Windows installer has a signed executable; a Web build is created from the production command and its deployment remains out of scope.

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.

### Step 2: Map the development-to-production boundary

Run the deterministic baseline first:

```bash
python3 "$SKILL_DIR/scripts/production_audit.py" --root . --format markdown
```

Use it to locate version sources, development and production commands, packaging configuration, explicit updater settings, and obvious placeholder configuration. The report is an audit aid, not proof that a product is ready.

Then inspect the concrete boundary:

1. Development server URLs, debug flags, mock backends, dev-only tooling, logging, and unsafe local assumptions.
2. Production command, bundle identifiers, version alignment, packaged assets, environment-variable delivery, and platform permissions.
3. Signing, notarization, code-signing identity, updater endpoints, and release metadata only when the target declares them. Never invent credentials, endpoint values, or release channels.
4. Existing running processes and user data. Do not replace an installed application while it is in active use without first coordinating a safe handoff.

### Step 3: Implement the smallest complete production path

1. Make only the source/configuration changes needed to satisfy the declared target.
2. Keep development commands working unless the user explicitly asks to remove them.
3. Keep secrets outside source control and reports. Report missing credential *names* and their effect, never values.
4. Run the repository's applicable quality gate in its established package-manager order.
5. Build from the real production command, not a browser preview or a development server.

### Step 4: Verify the actual artifact

Use the checks applicable to the platform from `references/production-readiness.md`.

- For macOS, verify the bundle identifier and version, `codesign --verify --deep --strict`, `spctl -a -vv -t exec`, and notarization stapling when the build claims to be notarized.
- For a local install, stage the finished artifact, move the existing application to a recoverable location only with explicit install authority, copy the new app cleanly, then compare the installed executable digest with the staged artifact.
- For other platforms, use the native installer/signature verification supplied by the project and platform. A file existing on disk is not enough.
- If a test or native check fails, report `blocked` or `implemented_not_verified`; do not substitute a dev-server check.

### Step 5: Hand off or report

- Use `production-artifact-verified` only after a real artifact passes the agreed checks.
- Use `ready-for-release-handoff` only when the artifact, version, release notes, and required credentials are ready for a separate explicit release request.
- Send external release work to `lov-app-release` or `lov-release-via-cicd` with a compact artifact-level handoff: version sources, build command, verified artifact path, checks passed, and remaining release obligations.
- Record one real Input → Prompt → Output case before calling a new version of this Skill complete. Do not manufacture evidence or scores.

### Step 6: Validate the Skill source

Run:

```bash
python3 scripts/validate_skill.py .
```

Verify a documented activation phrase routes here, a release-only request routes to the downstream release Skill, and the local installed link resolves to this source.

## Dependencies

- Python 3.8+ standard library for the production audit helper.
- The target project's own package manager, compiler, signing tools, and platform verification tools where relevant.
- No cloud service, credential, or external sibling Skill is required for the local readiness workflow.
