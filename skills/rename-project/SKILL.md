---
name: lov-rename-project
license: MIT
compatibility: 'Requires Python 3.8+ (stdlib only) and Git for repository operations.
  GitHub verification is optional and requires the gh CLI. The bundled scanner is
  UTF-8 text aware, skips binary/generated files (including private runtime clones),
  accepts additional --skip-dir values, and defaults to a read-only plan before applying
  changes. Live-process inspection and host-state updates use the operating system
  or host application''s own interfaces.

  '
description: 在保留兼容键与运行连续性的前提下重命名项目、路径和仓库。支持明确输入与结果回读。Use to rename a project and preserve
  compatibility.
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 2.3.1
  tags:
  - project-maintenance
  - rename
  - git
  - github
  - compatibility
  - migration
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
---

# 项目改名 · Project Renamer

## Triggers

### Activate when

- “在保留兼容键与运行连续性的前提下重命名项目、路径和仓库。”
- “Rename a project and preserve compatibility.”

### Do not activate when

- 只是查询本 Skill 的说明，或请求与上述结果无关的任务；不执行实际业务操作。
- 用户仅要预览或审查时，不进入修改、提交或发布分支。


This is a non-interactive workflow: the explicit invocation supplies the target,
and the command returns a reviewable plan before any write.

Use the bundled `scripts/rename_project.py` instead of a blind `grep`/`sed`
replacement. The command produces a machine-readable plan, classifies
compatibility-sensitive references, and stages only files changed by this run.

## Arguments

`<new-name>` is the new product or repository name. Pass `--old-name` when the
remote name is not the product name or when a legacy alias must be handled
explicitly. The default scan covers common source, configuration, and
documentation text files while skipping binary files, generated directories,
and lockfiles.

Use repeated `--skip-dir <directory-name>` arguments for project-specific
generated trees that are not in the built-in skip set. The defaults include
common build/cache directories plus `.runtime` and `.codex-upstream`; generated
private application clones should never flood the compatibility plan.

## Rename layers

A complete rename may span several independent layers. Audit all of them, but
do not collapse them into one repository-wide replacement:

1. product text and package or bundle metadata;
2. the filesystem project root;
3. generated/private runtime clones built from that root;
4. host registrations such as launchers, project catalogs, IDEs, and task UIs;
5. historical task records whose original `cwd` may be immutable;
6. Git remotes and GitHub repository state.

The scanner owns the first layer. Filesystem moves, live processes, host state,
and historical task compatibility require explicit migration and readback.

## Workflow

### 1. Establish scope and baseline

Run from the project root, or pass `--root`:

```bash
python3 scripts/rename_project.py Ataru \
  --old-name lovcode \
  --skip-dir private-runtime \
  --report /tmp/rename-project-plan.json
```

The default is a read-only plan. It detects the current name from
`origin` → `package.json` → directory name, records the current worktree state,
and reports each match as one of:

- `would_change`: ordinary product-name reference;
- `compatibility_review`: path or line looks like a legacy alias, storage
  namespace, migration, schema, data directory, or environment contract;
- `preserved`: excluded by an explicit `--preserve` regular expression.

Review this list before applying. Do not infer that every occurrence of the old
name should disappear: a CLI alias, on-disk namespace, migration key, or
environment variable may be part of the public compatibility contract.

The scanner also marks path-like old-name references such as application-data
directories, `Application Support` paths, search-index locations, and
`join("<old-name>")` expressions as compatibility-sensitive. This keeps a
product rename separate from a storage migration.

Before any path move, also record:

- the canonical source path and exact absent destination path;
- processes whose executable, arguments, or `cwd` are inside the source root;
- launcher metadata, project-discovery mappings, and host project registrations;
- the current task ID, title, pin/archive state, transcript location, project ID,
  and recorded `cwd` when the host exposes them.

Do not quit a desktop app or terminate agents merely to make a rename easier.
When active work depends on the old path, preserve a compatibility entry and
prove the same processes remain alive after migration.

### 2. Apply the product rename

```bash
python3 scripts/rename_project.py Ataru \
  --old-name lovcode \
  --apply \
  --report /tmp/rename-project-result.json
```

The scanner handles the exact, lower-case, upper-case, and title-case variants
of the old name. It writes UTF-8 text only and records before/after SHA-256
digests in the report. Existing edits in a target file stop the run unless
`--allow-dirty` is supplied after that file has been reviewed. Unrelated dirty
files remain untouched.

### 3. Resolve compatibility references explicitly

Keep legacy references by default. If a reviewed compatibility path should
also be renamed, opt in explicitly:

```bash
python3 scripts/rename_project.py Ataru \
  --old-name lovcode \
  --include-compat \
  --preserve '(^|/)(migrations|storage|legacy)/' \
  --apply
```

For a narrower migration, include only reviewed compatibility paths instead of
opening every legacy contract:

```bash
python3 scripts/rename_project.py Ataru \
  --old-name lovcode \
  --include-compat-path '^src-tauri/src/app/core\\.rs$' \
  --include-compat-path '^src-tauri/src/app/session_(cache|listing)\\.rs$' \
  --apply
```

Use this pattern when a data namespace should move from `lovcode` to `ataru`
while the old CLI alias, environment variables, storage fallback, or migration
keys remain intact. `--include-compat` remains available for a fully reviewed
compatibility sweep. Use `--include-locks` only when package or Cargo lockfiles
are part of the requested rename; lockfile updates should normally come from
the package manager so their integrity data remains valid.

### 4. Migrate the filesystem root without interrupting active work

Treat a directory move as a separate guarded operation. Resolve both paths,
verify that the destination does not exist, move the directory, and immediately
create an old-path symlink when active or historical tasks still reference it:

```bash
test -d /absolute/path/old-project
test ! -e /absolute/path/new-project
mv /absolute/path/old-project /absolute/path/new-project
ln -s /absolute/path/new-project /absolute/path/old-project
```

Use exact paths rather than unresolved environment variables or globs. The
symlink is a compatibility contract, not a duplicate checkout. Keep it until
every active process, launcher, host registration, historical task, attachment,
and automation has either migrated or been proven independent of the old path.

A running process normally keeps the moved directory inode as its `cwd`, but
its command line can continue to display the old spelling. Verify the process
identity and canonical `cwd`; do not mistake a stale command-line string for a
failed move. Do not rebuild or replace an active private runtime bundle during
the move. Point the launcher at the new root and let the next normal launch
regenerate it; the compatibility symlink keeps the current runtime valid.

### 5. Update host registrations through the active host

Update every discovered registration to the new canonical path, for example:

- a launcher's embedded project root or bundle metadata;
- a project-discovery CLI or local app catalog;
- the desktop host's project name and source folders;
- task-to-project assignments and pinned/searchable task metadata.

Prefer the host application's UI, API, or supported CLI while it is running.
Directly editing a backing JSON or SQLite file may leave the host's in-memory
state stale and can be overwritten later. After saving, read the project name,
path, and stable project ID back from the active host.

Do not rewrite immutable historical task metadata just to make every old string
disappear. A task created under the old root may retain its original `cwd` while
remaining correctly assigned to the renamed project. Preserve the old-path
symlink, give important tasks a searchable title or pin when authorized, and
verify that the host can still list and reopen them from the shared task store.

### 6. Verify source, runtime, path, and task continuity

```bash
git diff --check
git diff --name-only
git diff --stat
rg -n --hidden -g '!{.git,node_modules,dist,build,target,.runtime,.codex-upstream}/**' 'lovcode|Lovcode|LOVCODE'
```

The final search is an audit, not an instruction to replace every remaining
match. Explain each intentional compatibility match in the task result.

For a live path migration, also verify:

- the new root resolves canonically and the old root resolves to its symlink;
- pre-migration process IDs are still alive and their canonical `cwd` is new;
- launchers and discovery tools read back the new root;
- the active host reads back the renamed project without changing its project ID;
- the current task remains active/searchable and its transcript still exists;
- generated runtime verification and the project's normal test suite pass.

### 7. Commit and publish exact files

Only after the diff is reviewed:

```bash
python3 scripts/rename_project.py Ataru \
  --old-name lovcode \
  --apply --commit --push
```

The command uses `git add -- <changed files>`, verifies the staged file set,
commits with `chore: rename project from <old> to <new>`, and pushes the current
branch to `origin`. It never uses `git add -A`, so pre-existing untracked
artifacts are not swept into the rename commit.

### 8. Rename and verify the GitHub repository

After the source commit is pushed, add `--github`:

```bash
python3 scripts/rename_project.py Ataru \
  --old-name lovcode \
  --apply --commit --push --github
```

The optional GitHub step requires `gh`, checks the remote first, runs the rename,
then reads the repository name back through `gh repo view`. If the remote or
CLI is unavailable, the local rename result remains explicit and the GitHub
step is reported as incomplete rather than implied successful.

## Dirty worktrees and rollback

Unrelated dirty files are preserved. A target file with existing edits requires
review before using `--allow-dirty`; this prevents a rename commit from silently
absorbing another task's changes. The JSON report plus `git diff` provide the
changed-file and hash evidence. Before committing, use `git restore --staged`
to unstage the exact file set; after committing, use a normal reviewed revert
commit if the rename must be rolled back.

For a filesystem migration, rollback means first stopping new writes through
the new canonical path, removing only the verified compatibility symlink, and
moving the exact destination back to the exact source. Never delete either path
recursively. Preserve a backup before editing host state outside the repository,
and prefer the host's own undo/edit flow when available.

## Failure handling

The command exits non-zero for invalid names, unreadable text, dirty target
files, unexpected staging contents, missing remotes, failed pushes, or an
unverified GitHub rename. Nested project roots are staged relative to their
actual Git repository, and requested JSON reports are also written on failure.
A plan can be rerun safely because plan mode is read-only and apply mode reports
its exact changed paths.

## Execution boundary

自然语言请求即可触发；无需旧 slash 路径、参数插值或指定助手。明确解析当前请求中的
项目、目标文件、选项与输出位置；用当前宿主实际提供的文件、搜索、CLI 和浏览器能力。
项目依赖版本与外部 API 在执行时核实，不能假设示例是现行配置。随包脚本从 Skill 根解析，
业务文件从目标项目根解析。先读当前状态，保护已有未提交内容与其他任务的暂存区。
分析、预览请求保持只读；修改、提交、推送、部署和发布各依当前请求的明确范围执行。
不绕过保护、自动发送消息、强制结束用户进程或抢前台。失败保留可诊断原始错误。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
