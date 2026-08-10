---
name: lov-release-via-cicd
disable-model-invocation: true
description: >
  Configure CI/CD and publish new versions for Node, Tauri, Vite, shell, and
  GitHub Release projects. Use when the user asks to setup release workflow,
  publish a new version, verify macOS signing/notarization, recover a failed
  GitHub Release, or mentions "release-via-cicd", "配置并发布新版", "签名",
  "notarize", "GitHub Release", or "CI/CD 发布".
license: MIT
compatibility: >
  Requires Git, GitHub CLI (`gh`), the project's package manager, and platform
  build tools. Tauri macOS signing additionally requires Apple Developer ID
  certificate and notarization credentials.
metadata:
  author: contributors
  version: "8.6.0"
  tags: release cicd github-actions tauri macos-signing notarization changesets
---

# Release via CI/CD

幂等、自适应的发布流程。**默认自动执行 setup + publish**。

**默认使用 changesets**，除非用户明确选择保留 semantic-release。

## Step 0: 开场笑话 🎭

**在开始发布前，先讲一个程序员笑话放松一下：**

从以下笑话中随机选一个讲：

1. > 为什么程序员总是搞混万圣节和圣诞节？因为 Oct 31 = Dec 25
2. > 程序员最讨厌的数字是什么？2.0——因为它意味着重写
3. > "我的代码能跑了！" "太好了，提交吧。" "等等，我先看看为什么能跑..."
4. > 产品经理：这个需求很简单。程序员：你这句话本身就很复杂。
5. > 为什么程序员喜欢暗黑模式？因为 bugs 都怕光
6. > git commit -m "最终版" → git commit -m "最终版2" → git commit -m "这次真的是最终版"
7. > 99 个 bug 在代码里，99 个 bug～ 修掉一个，编译一下，127 个 bug 在代码里...

讲完笑话后，继续执行发布流程。

## 参数

```
无参数      → setup + publish（默认，自动模式）
setup      → 仅检查/修复配置
publish    → 仅执行发布
--keep-semantic-release  → 保留现有 semantic-release 配置
patch|minor|major        → 指定版本类型
```

## 自动模式行为

**原则：除非非常不确定，否则自动执行**

1. **自动提交**：有未提交更改时，自动 `git add -A && git commit`
   - 提交信息从 diff 内容推断（如 "fix: update xxx" 或 "feat: add xxx"）
   - 仅当变更复杂且无法推断意图时才询问

2. **自动版本**：默认 patch，除非用户显式指定
   - **首次发布（无 tag）→ `0.1.0`**（不是 1.0.0！1.0+ 需要用户明确指定）
   - 当前版本 `0.x.y` → 保持 `0.x` 前缀，按 patch/minor 递增
   - 默认 → patch（最安全的选择）
   - 用户参数 `minor` → minor
   - 用户参数 `major` → major
   - 用户显式指定 `1.0.0` 或 `major` 且当前 ≥ 0.x → 才可升到 1.0+
   - 检测到 `BREAKING` 变更 → 询问用户是否使用 major

   **版本号哲学**：0.x 表示「功能在持续演进」，1.0 表示「稳定 API 承诺」。无用户指引时永远不要自行跳到 1.0+。如果已有错误的 1.0+ tag，应提议重写（删除旧 tag/release，从 0.x 重新开始）。

3. **询问条件**：只有以下情况才询问用户
   - 工作区有多个不相关的变更
   - 变更涉及敏感文件（如 .env, secrets）
   - 版本类型无法自动推断（如 refactor 可能是 patch 或 minor）

4. **自动分支处理**：如果在 feature 分支
   - 自动提交当前变更
   - 自动 push 到 remote
   - 自动切换到 main 并 merge feature 分支
   - 使用 `--no-ff` 保留分支历史

5. **自动 Issue 处理**：从分支名/commit 检测关联 issue
   - 分支名格式：`*/issue-<number>*` 或 `*/<number>-*`
   - Commit 格式：`Closes #<number>` / `Fixes #<number>` / `Resolves #<number>`
   - 发布成功后自动 comment + close

## Step 1: 自动检测项目

```
类型: Tauri (src-tauri/) | Monorepo (pnpm-workspace.yaml) | Node (package.json) | Shell (无 package.json)
目标: npm | GitHub Release | 二进制
子类型:
  - Obsidian 插件 → GitHub Release Only（tag 触发，无 npm）
  - Vite/前端项目 (private: true) → GitHub Release + dist.zip
发布工具:
  - 检测到 semantic-release → 询问是否迁移到 changesets（推荐）
  - 检测到 changesets → 继续使用
  - 未配置 → 自动配置 changesets
```

**Shell 项目**：只需 workflow + tag + CHANGELOG.md
**Vite/前端项目**：GitHub Release + 上传 `{project}-{version}.zip`

**所有项目类型**：必须维护 CHANGELOG.md，发布前自动在顶部添加新版本变更记录，workflow 从中提取 release notes。禁止使用 `generate_release_notes: true`。

### semantic-release 迁移检测

检测是否使用 semantic-release：
```bash
# 检查 package.json 是否有 semantic-release 相关配置
grep -q "semantic-release" package.json && echo "semantic-release detected"
# 检查 workflow 是否调用 semantic-release
grep -rq "semantic-release" .github/workflows/ && echo "workflow uses semantic-release"
```

**如果检测到 semantic-release 且未传 `--keep-semantic-release`**：
1. 使用 AskUserQuestion 询问用户是否迁移到 changesets
2. 推荐迁移（changesets 更灵活、支持 Monorepo）
3. 用户同意后执行迁移（见下方「迁移步骤」）

### 迁移到 changesets 步骤

```bash
# 1. 初始化 changesets
pnpm add -D @changesets/cli
pnpm changeset init

# 2. 更新 .changeset/config.json
cat > .changeset/config.json << 'EOF'
{
  "$schema": "https://unpkg.com/@changesets/config@3.1.1/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [],
  "linked": [],
  "access": "public",
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}
EOF

# 3. 移除 semantic-release 配置
# - 从 package.json 删除 "release" 配置块
# - 从 devDependencies 删除 semantic-release 相关包

# 4. 更新 workflow（见下方 Workflow 模板）
```

---

## Setup 阶段

### 检查并报告

```
✓/✗ .github/workflows/release.yml
✓/✗ .github/workflows/release.yml 包含 `permissions: contents: write`
✓/✗ Repo workflow permissions (write)
✓/✗ [Node] package.json (packageManager, scripts)
✓/✗ [Node] package.json 包含 packageManager 字段
✓/✗ [Node] .changeset/config.json（推荐）
⚠️ [Node] semantic-release 检测（建议迁移到 changesets）
✓/✗ [npm] NPM_TOKEN secret
✓/✗ CHANGELOG.md 存在且格式正确（## x.y.z 格式）
✓/✗ [Tauri] Cargo.toml 版本同步
✓/✗ 区域/国内镜像由独立 post-CI workflow 同步，不在主发布 DAG 中
```

### 自动修复

**Repo 权限**:
```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
gh api "repos/${REPO}/actions/permissions/workflow" -X PUT \
  -f default_workflow_permissions=write -F can_approve_pull_request_reviews=true
```

**packageManager 字段**（如缺失）:
```bash
# 按 lockfile/现有字段检测，不要强行改成 pnpm
if node -e "process.exit(require('./package.json').packageManager ? 0 : 1)" 2>/dev/null; then
  node -p "require('./package.json').packageManager"
elif [ -f bun.lock ] || [ -f bun.lockb ]; then
  BUN_VERSION=$(bun --version)
  # 在 package.json 中添加 "packageManager": "bun@${BUN_VERSION}"
elif [ -f pnpm-lock.yaml ]; then
  PNPM_VERSION=$(pnpm --version)
  # 在 package.json 中添加 "packageManager": "pnpm@${PNPM_VERSION}"
elif [ -f yarn.lock ]; then
  YARN_VERSION=$(yarn --version)
  # 在 package.json 中添加 "packageManager": "yarn@${YARN_VERSION}"
else
  NPM_VERSION=$(npm --version)
  # 在 package.json 中添加 "packageManager": "npm@${NPM_VERSION}"
fi
```

**Shell 项目 Workflow**:
模板见 `references/general-release-playbooks.md`。Shell 项目也必须支持 `workflow_dispatch`，并从 `CHANGELOG.md` 提取 release notes。

**Node 项目原则**:
- 必须支持 `workflow_dispatch`
- Tauri 用 job chaining（GITHUB_TOKEN 限制）
- npm 包需要 `NPM_TOKEN`
- workflow 必须按 `packageManager` 选择 bun/pnpm/yarn/npm，不要强行写死 pnpm
- Bun 项目使用 `oven-sh/setup-bun@v2`、`bun install --frozen-lockfile`、`bun run build`
- pnpm 项目使用 `pnpm/action-setup@v4`，**不要指定 version**（读取 packageManager 字段）
- Tauri macOS 交叉编译需添加 Rust targets: `aarch64-apple-darwin,x86_64-apple-darwin`

**CHANGELOG.md 集成**:
- 发布时从 `CHANGELOG.md` 提取对应版本内容作为 release notes
- Fallback: CHANGELOG.md 无内容时用 GitHub 自动生成
- 避免 `generate_release_notes` 在多 job 重复

### 区域镜像必须后置

- 主发布 DAG 只负责构建、签名/公证、上传权威发布源并公开 Release。
- 国内、区域或社区镜像必须由公开 Release 之后单独调度的 post-CI workflow 同步；禁止把镜像上传放进平台构建 job，也禁止让 `publish-release` 依赖镜像 job。
- post-CI workflow 必须按不可变 tag 从权威发布源重新下载资产，再上传镜像，确保镜像内容与已发布资产一致。
- 调度失败只输出 warning；镜像 workflow 允许独立失败和重试，不得回滚或阻塞主 Release。
- 主工作流成功后先报告权威 Release 成功，再独立监控并验证镜像状态。模板见 `references/general-release-playbooks.md`。

---

## Publish 阶段

### 前置检查
```bash
git status --porcelain      # 不干净 → 自动提交（见自动模式）
git branch --show-current   # 非 main/master → 自动合并（见分支处理）
git pull --rebase
# CHANGELOG.md 检查：不存在 → 自动创建（从 git log 生成历史记录）
# 发布前必须在 CHANGELOG.md 顶部添加新版本变更记录
```

**长 workflow 防漂移**：
- 创建 release commit 和 tag 前，必须确认本轮要发布的 diff 已经全部提交。
- `git tag` 后记录 `RELEASE_COMMIT=$(git rev-parse HEAD)`；workflow、release、验证都只对应这个 commit。
- workflow 运行期间如果用户继续修改工作区，发布完成后只做 `git status` 报告，不要把新脏改动补进已打 tag 的版本。
- 如果必须包含这些新改动，重新 bump 一个新版本；不要静默移动已发布/已公告的 tag。

### 自动分支合并
```bash
BRANCH=$(git branch --show-current)
MAIN_BRANCH="main"  # 或 master，自动检测

# 如果不在 main 分支
if [ "$BRANCH" != "$MAIN_BRANCH" ]; then
  # 1. 提交并推送当前分支
  git add -A && git commit -m "<auto message>" || true
  git push origin "$BRANCH"

  # 2. 切换到 main 并拉取最新
  git checkout "$MAIN_BRANCH"
  git pull origin "$MAIN_BRANCH"

  # 3. 合并 feature 分支（保留历史）
  git merge "$BRANCH" --no-ff -m "Merge branch '$BRANCH' into $MAIN_BRANCH

<changeset description>

Closes #<issue_number>"  # 如果检测到关联 issue
fi
```

### 自动 Issue 检测与处理
```bash
# 从分支名提取 issue 号
BRANCH=$(git branch --show-current)
ISSUE_NUM=""

# 匹配模式：issue-123, 123-feature, feature/issue-123
if [[ "$BRANCH" =~ issue-([0-9]+) ]]; then
  ISSUE_NUM="${BASH_REMATCH[1]}"
elif [[ "$BRANCH" =~ ^([0-9]+)- ]]; then
  ISSUE_NUM="${BASH_REMATCH[1]}"
elif [[ "$BRANCH" =~ /([0-9]+)- ]]; then
  ISSUE_NUM="${BASH_REMATCH[1]}"
fi

# 从 commit message 提取（作为补充）
if [ -z "$ISSUE_NUM" ]; then
  COMMITS=$(git log "$MAIN_BRANCH"..HEAD --format=%s 2>/dev/null)
  ISSUE_NUM=$(echo "$COMMITS" | grep -oE '(Closes|Fixes|Resolves) #[0-9]+' | head -1 | grep -oE '[0-9]+')
fi

# 验证 issue 存在且未关闭
if [ -n "$ISSUE_NUM" ]; then
  STATE=$(gh issue view "$ISSUE_NUM" --json state -q '.state' 2>/dev/null || echo "")
  if [ "$STATE" = "OPEN" ]; then
    echo "检测到关联 Issue #$ISSUE_NUM"
  else
    ISSUE_NUM=""  # 忽略已关闭的 issue
  fi
fi
```

### 发布后自动关闭 Issue
```bash
# 在 workflow 成功后执行
if [ -n "$ISSUE_NUM" ]; then
  VERSION="v${VERSION}"
  RELEASE_URL="https://github.com/${REPO}/releases/tag/${VERSION}"

  # 添加评论
  gh issue comment "$ISSUE_NUM" --body "已在 ${VERSION} 中修复。

Release: ${RELEASE_URL}"

  # 关闭 issue
  gh issue close "$ISSUE_NUM" --reason completed

  echo "✓ Issue #$ISSUE_NUM 已关闭"
fi
```

### 自动提交逻辑
```bash
# 1. 检查变更
CHANGES=$(git status --porcelain)
if [ -z "$CHANGES" ]; then exit; fi

# 2. 分析变更推断提交类型
#    - 修改现有文件 → fix
#    - 添加新文件 → feat
#    - 删除文件 → chore
#    - 配置文件 → chore

# 3. 推断提交描述（从文件名/diff 内容）
#    - 单文件：直接用文件名
#    - 多文件同类：归纳共同点
#    - 复杂变更：才询问用户

# 4. 自动提交
git add -A && git commit -m "${TYPE}: ${DESC}"
```

### 自动版本推断
```bash
# 版本类型优先级：
# 1. 用户显式参数 (patch/minor/major/具体版本号)
# 2. 检测到 BREAKING 变更 → 询问用户
# 3. 无 tag（首次发布）→ v0.1.0（不是 v1.0.0！）
# 4. 当前 0.x → 保持 0.x，按 patch/minor 递增
# 5. 默认 patch（最安全）
#
# ⚠️ 1.0+ 需要用户明确指定，绝不自行跳到 1.0+

LATEST=$(git tag -l 'v*' | sort -V | tail -1)
if [ -z "$LATEST" ]; then
  NEXT="v0.1.0"  # 首次发布从 0.1.0 开始
else
  # 解析当前版本并递增
  # 0.1.0 + patch → 0.1.1
  # 0.1.1 + minor → 0.2.0
  # 只有用户显式指定 major 或 1.0.0 才跳到 1.x
fi

# 检查是否有 BREAKING 变更
LAST_MSG=$(git log -1 --format=%s)
if [[ "$LAST_MSG" =~ ^BREAKING ]] || [[ "$LAST_MSG" =~ ^major: ]]; then
  echo "检测到可能的 BREAKING CHANGE: $LAST_MSG"
  echo "是否使用 major 版本？(y/N)"
  # 使用 AskUserQuestion 工具询问
fi

VERSION_TYPE="${USER_SPECIFIED_VERSION:-patch}"
```

### Shell 项目

```bash
# 获取最新 tag 并递增
LATEST=$(git tag -l 'v*' | sort -V | tail -1)
NEXT="v0.1.0"  # 无 tag 时默认 0.1.0（不是 1.0.0！）
# 自动递增 patch（0.1.0 → 0.1.1），minor 需用户指定

git tag "$NEXT" && git push --tags
# workflow 自动触发
```

### Node 项目

**自动模式**（默认）:
- 版本：从 commit 类型自动推断（见自动版本推断）
- 方式：默认 `local`（最快）

**询问模式**（仅当无法推断时）:
```
版本: [patch] / [minor] / [major]
方式: [local] 快速本地 | [ci] 通过 PR | [ci-auto] PR+自动合并
```

**Local 路径（Tauri）**:
```bash
# 1. 创建 changeset（如缺失）
cat > .changeset/<name>.md << 'EOF'
---
"<package>": patch
---

<description>
EOF

# 2. Bump version
pnpm changeset version  # 或项目自定义的 changeset:version 脚本
git add . && git commit -m "chore: release v${VERSION}"
git push

# 3. 创建并推送 tag（workflow checkout 需要 tag 存在）
git tag v${VERSION} && git push origin v${VERSION}

# 4. 触发构建
gh workflow run release.yml -f tag=v${VERSION}
sleep 3
RUN_ID=$(gh run list -w release.yml -L 1 --json databaseId -q '.[0].databaseId')
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Workflow: https://github.com/$REPO/actions/runs/$RUN_ID"

# 5. **必须**等待 workflow 完成（指数退避轮询）
gh_view_json() {
  local run_id="$1"
  local json="$2"
  local query="$3"
  local attempt=1
  while [ "$attempt" -le 5 ]; do
    if gh run view "$run_id" --json "$json" -q "$query"; then
      return 0
    fi
    sleep $((attempt * 2))
    attempt=$((attempt + 1))
  done
  return 1
}

DELAY=5
MAX_DELAY=60
while true; do
  STATUS=$(gh_view_json "$RUN_ID" status '.status') || {
    echo "GitHub API 暂时不可用，下一轮继续重试..."
    sleep "$DELAY"
    continue
  }
  if [ "$STATUS" = "completed" ]; then
    CONCLUSION=$(gh_view_json "$RUN_ID" conclusion '.conclusion' || echo "unknown")
    echo "Workflow $CONCLUSION"
    break
  fi
  echo "Status: $STATUS, waiting ${DELAY}s..."
  sleep $DELAY
  DELAY=$((DELAY * 2 > MAX_DELAY ? MAX_DELAY : DELAY * 2))
done
```

**Local 路径（纯 Node）**:
```bash
pnpm build && pnpm changeset publish
git push --follow-tags
NOTES=$(awk -v ver="${VERSION}" '/^## / { if (found) exit; if ($2 == ver) { found=1; next } } found { print }' CHANGELOG.md)
gh release create "v${VERSION}" --notes "${NOTES:-Release v${VERSION}}" --latest
```

**CI 路径**:
```bash
git add -A && git commit -m "chore: add changeset" && git push
# 等待 Version Packages PR
gh pr merge ... --squash --delete-branch  # ci-auto
```

---

## References

- Tauri/macOS signing/notarization/Windows fallback: `references/tauri-release-workflow.md`
- Shell, Vite, monorepo templates, post-release mirror separation, workflow monitoring, README/Vercel audits, issue automation, and failure recovery: `references/general-release-playbooks.md`

When a referenced template conflicts with this `SKILL.md`, follow the stricter rule: maintain `CHANGELOG.md`, preserve package manager choice, do not print secrets, wait for workflow completion with retry, and verify final release assets before reporting success.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
