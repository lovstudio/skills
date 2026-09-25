---
name: lov-app-release
description: >
  执行一次可验证的多渠道应用发版：统一版本与文档，构建并签名 iOS/Android，发布 GitHub 与官网，提交商店并回读线上状态。用于“发布新版”“同步更新所有渠道”及 “release the app everywhere”。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "1.0.1"
  tags:
    - app-release
    - ios
    - android
    - github-release
    - production-deploy
  compatibility: "Portable Agent Skills format. Requires Git and the target project's own platform build and deployment tools."
  dependencies: []
---

# 应用发版助手 · App Release Pilot

把同一个应用版本真正发布到项目已经声明的全部渠道，并以远端状态、签名、
制品哈希和公开入口作为完成证据。构建成功只是中间状态，不是发布完成。

## Triggers

### Activate when

- 用户说“发布新版”“发个新版本”“同步更新 GitHub、iOS、Android、官网和文档”。
- 用户要求“把这个 App 全渠道上线”“完成发版并逐项验证”。
- The user says “release the app everywhere”, “ship a new app version”, or
  “sync GitHub, iOS, Android, website, and docs”.

### Do not activate when

- 用户只要配置或修复 CI/CD 流水线；交给专门的 CI/CD 发布能力。
- 用户只发布 npm、Python、Rust 库或普通 GitHub tag；交给通用包发布能力。
- 用户只要本地调试包、模拟器构建或真机安装，且没有提出外部发布。
- 用户明确只要发版计划、审计或原因分析，不要求改变外部状态。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve the Skill and read the applicable contracts

- Resolve `SKILL_DIR` from the active Skill context.
- Read `$SKILL_DIR/references/release-contract.md` completely on every run.
- Read only the channel references that match the detected release surface:
  - Android → `$SKILL_DIR/references/android.md`
  - iOS / App Store → `$SKILL_DIR/references/ios-app-store.md`
  - GitHub, website, downloads, or docs →
    `$SKILL_DIR/references/web-github-docs.md`
- Use the target repository's own instructions, scripts, signing setup, and
  deployment configuration as the source of truth.

### Step 1: Resolve release intent and authority

- Work from the repository named by the user or the current Git root.
- “发布新版”, “release”, “ship”, or an explicit list of production channels
  authorizes the normal in-scope release actions for those channels: version
  updates, signing, upload, tag/push, production deploy, and review submission.
- “准备发版”, “审计发版”, or “给我方案” stops before external publication.
- Do not ask again for production confirmation when the user already requested
  a release. Ask only when the target project is ambiguous, two independent
  products are present, or a major/breaking version choice changes the public
  contract.
- Never print passwords, private keys, bearer tokens, signing secrets, or full
  credential file contents. Report credential names and validity only.

### Step 2: Establish the release baseline

1. Confirm the real Git root, active branch, worktrees, `main`/`master`, remote,
   dirty files, and ahead/behind counts.
2. Preserve unrelated user changes. Determine whether generated version-file
   drift is a release input or a build residue before editing it.
3. Fetch remote branches and tags, then identify the last release and commits
   since it.
4. Detect every version source, including package manifests, native manifests,
   Android `versionCode`, iOS marketing/build versions, website download paths,
   and documentation.
5. Detect the real distribution surface from existing configuration. Do not
   invent a Play Store, App Store, website, or hosting provider that the project
   does not use.
6. Query drift-prone external state now: latest GitHub Release, store version
   and review status, public download, production deployment, and pricing when
   the product is paid.

Maintain a channel matrix internally with: channel, previous state, intended
action, artifact/version, completion condition, and current evidence.

### Step 3: Select and synchronize the version

- Use an explicit user version first, then the repository's release policy.
- Without an explicit version, infer SemVer from changes: breaking public
  change → major; user-visible feature → minor; fixes/docs/build-only → patch.
- Preserve an established pre-1.0 policy. Confirm before crossing a public
  compatibility boundary.
- Keep platform build identifiers monotonic even when the marketing version
  changes. Android `versionCode` and iOS `CFBundleVersion` must exceed uploaded
  builds.
- Synchronize all authoritative manifests and generated native project files
  that are intentionally tracked. Verify the generated output after native
  build tools run because they may rewrite versions.
- Add a dated changelog section and update README, release documentation,
  website download paths, visible version labels, and related tests.
- Keep user-facing notes about product value and observable changes. Do not
  expose internal prompts, migration context, credentials, or production intent.

### Step 4: Run the repository quality gate

- Install dependencies using the existing lockfile policy when needed.
- Run the project's complete release gate, not a narrow smoke test: unit tests,
  type/build checks, native checks, linting, and any repository-specific audit.
- Fix in-scope failures and rerun the full gate.
- Record counts and exact remaining warnings. A platform's future policy warning
  may be reported without blocking a release that the platform accepts today.

### Step 5: Build and verify Android

If Android is in scope, follow `references/android.md` completely.

Completion requires the configured Android distribution channel to receive a
signed, versioned artifact. For direct download, the public bytes must match the
local SHA-256. For a store track, read back version code and release state.

### Step 6: Build, upload, and submit iOS

If iOS is in scope, follow `references/ios-app-store.md` completely.

Completion requires an uploaded build processed as valid and eligible, bound to
the intended App Store version, and submitted through the current review flow.
An asynchronous final review may remain pending; report that exact state.

### Step 7: Commit, merge, tag, and publish GitHub

If source or GitHub is in scope, follow `references/web-github-docs.md`.

- Commit only the release changes and intended artifacts.
- Merge or fast-forward the completed work into the repository's main branch.
- Create an annotated version tag from the release commit using the changelog
  section as notes.
- Push main and tag, then create or update the GitHub Release with verified
  artifacts and checksum files.
- Never move a published tag to absorb later edits. Publish a new version when
  additional changes must be included.

### Step 8: Deploy the website and public downloads

If a website or public download is in scope, follow
`references/web-github-docs.md`.

- Use the already-linked production project and existing deployment provider.
- Deploy the release commit and confirm the production deployment is ready.
- Read back the custom domain, visible version/download path, response headers,
  artifact size, content type, and SHA-256 from an anonymous request.
- A private GitHub Release is not a public download source. Keep a verified
  same-domain or public object-storage URL when anonymous access is required.

### Step 9: Perform final cross-channel readback

Re-query every external system after mutation. The final matrix must prove:

- Git main equals the pushed release commit and the worktree is clean apart
  from explicitly preserved user changes.
- The annotated tag and GitHub Release point at that commit and contain the
  expected assets.
- Android reports the intended version/signing identity and is downloadable or
  present on its configured store track.
- iOS reports the intended marketing version and build, valid processing state,
  review state, release type, encryption declaration, and price when relevant.
- The production domain resolves to the new deployment and serves the expected
  version and bytes.
- README, changelog, and detailed release notes agree with the shipped result.

Do not translate “uploaded”, “processing”, “waiting for review”, or “staged”
into “publicly available”. State each channel independently.

### Step 10: Report the release

Lead with the version and overall outcome. Include compact bullets for:

- source commit, tag, and GitHub Release URL;
- iOS version/build, processing and review state, and price if applicable;
- Android artifact URL, supported variants, and SHA-256;
- production website URL and deployment identifier;
- documentation files and quality-gate counts;
- any platform-accepted warning or pending asynchronous review.

## Dependencies

No Skill-specific runtime dependency. The target project supplies Git, package
manager, native SDKs, signing tools, store credentials, GitHub CLI, and hosting
CLI as required by its detected channels.

## Runtime context

运行前读取同目录 `skill.yaml`，由宿主的 `skill-runtime` 按“当前请求、项目上下文、个人配置、品牌 Profile、安全默认值”的顺序注入，只使用 manifest 声明的字段。

- 缺少 `required: true` 字段时，按 `questions` 向用户提出一个聚焦问题；回答只用于本次运行，除非用户明确要求保存。
- Profile 只用于公开品牌事实；个人配置只用于决策，不自动写入产物或源码。
- 调试报错提供可复制的 `context_id`、字段路径和来源，不输出秘密、完整私人路径或原始内容。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
