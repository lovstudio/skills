---
name: lov-organize-storage
description: 按项目、用途与生命周期盘点整块存储盘，规划同卷安全重命名与迁移，输出映射、回滚记录和不可删除门禁。Use when a drive or archive folder is messy or needs project-based organization.
license: MIT
compatibility: "Python 3.8+; macOS/Linux; same-volume rename; no external service required."
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - storage-organizer
    - archive
    - project-taxonomy
    - safe-rename
    - rollback
---

# 存储整理师 · Storage Organizer

把一整块存储盘或大型归档目录从「按类型堆放」改成「按项目分类」：先只读盘点，再给出最小迁移映射，最后用同卷 rename 执行并留下映射、日志和回滚脚本。默认不删除任何文件。

## Triggers

### Activate when

- “整个盘太乱”“按项目分类”“把这块盘整理清爽”“归档盘重新分类”。
- “整理外置硬盘 / SSD / NAS 挂载目录”“按项目而不是文件类型放”。
- “organize my drive”“project-first storage”“reorganize this archive volume”。
- “help me organize this drive by project”“use project-first storage for this archive volume”。
- 根目录里同时散落着相机项目、个人归档、成片、app 数据、安装包和系统目录，需要建立清晰的一级分类。

### Do not activate when

- 单个代码仓库的目录重构、import、构建路径或测试发现改进 → 交给 `lov-better-project-structure`。
- 只查找并删除重复文件 → 交给 `lov-safe-dedupe`；本 Skill 只做只读重复信号，不执行删除。
- 相机卡或存储卡首次转存、整卡校验与授权清卡 → 交给 `lov-migrate-camera-media`。
- 只清理 Mac 本地缓存或释放本地磁盘 → 交给 `lov-clean-mac`。
- 只重命名一个项目或仓库并保持兼容 → 交给 `lov-rename-project`。
- 用户只要预览或复盘，不要实际移动 → 停在安全计划和迁移映射，不执行 apply。

## Execution boundary

- 默认只读。`inventory` 与 `plan` 不修改目标盘。
- 只有用户明确确认迁移范围后，才允许执行 `apply --confirm`。
- 只做同卷 rename；跨卷复制、云同步、远程仓库和发布不在本 Skill。
- 不删除、不覆盖、不格式化。目标存在时停止并报告。
- 不移动系统目录：`.Trashes`、`.Spotlight-V100`、`.fseventsd`、`$RECYCLE.BIN`、`System Volume Information`。
- 不移动运行中的工程、被打开的 app 库、回收站里的唯一副本，除非用户明确覆盖并完成安全门禁。
- 每次 apply 必须先生成 mapping 和 rollback；完成后逐项 verify，并报告未移动项。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.lov-organize-storage` namespace at the start of every run. Keep
the source portable: resolved personal values belong in the shared profile,
never here.

When the user directly states a durable preference or workspace fact, persist
it through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets, credentials,
or private paths.

See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. This Skill stays a Single Skill:
the inventory, taxonomy, plan, apply, and verify stages share one safety model
and one migration log.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify `scripts/storage_organizer.py`, `references/storage-taxonomy.md`,
  `references/safety-gates.md`, and `references/skill-composition.md` exist
  before work. If one is missing, stop and name the expected relative path.
- Resolve `context.profile` with the precedence: current request, project
  context, Skill-specific records, shared preferences, shared user/brand
  profile, then safe defaults.
- Ask at most one focused question if the target root or output location is
  genuinely ambiguous.

```bash
export SKILL_DIR="/path/to/lov-organize-storage"
python3 "$SKILL_DIR/scripts/profile_store.py" read \
  --skill-id lov-organize-storage --pretty
```

### Step 1: Read-only inventory

- Record the volume path, filesystem type, total/free space, top-level entries,
  project markers, app libraries, installers, broken symlinks, system dirs, and
  any trash directory.
- Never read, move, or empty `.Trashes` during inventory; record its size and
  contents count only.
- Detect copy-suffix patterns (`name 1.ext`, `name 2.ext`) as a read-only
  signal. Deduplication and deletion belong to a separate capability.

```bash
python3 "$SKILL_DIR/scripts/storage_organizer.py" inventory \
  --root "/Volumes/Example" \
  --sizes \
  --out /tmp/storage-inventory.json
```

### Step 2: Classify by project first

Read `references/storage-taxonomy.md`. Use this order:

1. Project or event with a delivery or source set → `01_项目/`.
2. Personal, non-project archive → `02_个人归档/`.
3. Finished media, films, or loose clips → `03_媒体库/`.
4. App-managed library or database → `04_应用数据/`.
5. Installer, admin, pending, quarantine, or migration record → `99_管理/`.

Preserve existing internal conventions. In particular, camera ingest
directories keep `原始素材/`、`处理素材/`、`转存校验/` where they already exist.
Date-sliced snapshots are not duplicates and must not be merged merely to make
the tree shallower.

### Step 3: Build and validate the minimal move map

- Write the smallest possible map: move whole containers, do not reshuffle their
  interiors unless the project boundary requires it.
- Use relative source and destination paths inside the target root.
- Run the planner; it validates same-volume rename, destination conflicts,
  nested moves, system-directory denylist, app-library collisions, recent
  activity, zero-byte-only directories, and exFAT sidecars.

```bash
python3 "$SKILL_DIR/scripts/storage_organizer.py" plan \
  --root "/Volumes/Example" \
  --map /tmp/storage-move-map.json \
  --out /tmp/storage-move-plan.json
```

Read `references/safety-gates.md` and resolve every hard block before asking for
confirmation. A plan with warnings is not approval to execute.

### Step 4: Present the dry run and obtain one confirmation

Report at minimum:

- target root and filesystem;
- number of planned moves and total logical size;
- destination conflicts: zero;
- deletions: zero;
- system directories and trash: untouched;
- hard blocks and warnings, with the exact reason;
- what will not move and why.

Only an explicit user confirmation advances to apply. If the user changes the
scope, rerun the plan instead of editing the old plan in place.

### Step 5: Apply with mapping and rollback

```bash
python3 "$SKILL_DIR/scripts/storage_organizer.py" apply \
  --plan /tmp/storage-move-plan.json \
  --confirm \
  --accept-warnings \
  --log-dir "/Volumes/Example/99_管理/迁移记录_2026-09-10"
```

The apply command:

- refuses blocked plans and unaccepted warnings;
- performs same-volume renames only;
- never overwrites an existing destination;
- carries exFAT `._*` sidecars when the filesystem does not move them
  automatically;
- writes `mapping.json` and `rollback.sh` before reporting success;
- records old/new inode, size, and timestamp evidence per move.

### Step 6: Verify and report

```bash
python3 "$SKILL_DIR/scripts/storage_organizer.py" verify \
  --plan /tmp/storage-move-plan.json \
  --log-dir "/Volumes/Example/99_管理/迁移记录_2026-09-10"
```

Verify every destination exists, every source is gone, and sidecars are paired.
Compare pre/post top-level totals. Report the new tree, old → new mapping,
rollback path, untouched system directories, and every item left for a separate
decision.

### Step 7: Hand off adjacent work

- Duplicate deletion → `lov-safe-dedupe` after a full hash and quarantine.
- Capacity cleanup on the Mac itself → `lov-clean-mac`.
- Camera-card ingest → `lov-migrate-camera-media`.
- Single code repository structure → `lov-better-project-structure`.
- If a user-visible report is published outside the local task, apply the
  `lov-branding-consistency` review to the public copy only.

## Safety invariants

- Same volume only; a cross-device move is a copy and is out of scope.
- No deletion; quarantine means rename into a visible holding directory first.
- No overwrite; destination existence is a hard stop.
- No system directory movement; trash is sealed by default.
- No movement of a source with a recent file or an open writer unless the user
  explicitly overrides and the override is recorded.
- App libraries remain at their expected paths unless the user confirms the
  consuming app has been repointed.
- Historical JSON and log paths are evidence; do not rewrite them. Record the
  old → new mapping instead.

## Dependencies

- Python 3.8+.
- PyYAML for `scripts/validate_skill.py`.
- macOS or Linux shell utilities; `du` is optional and used only when `--sizes`
  is requested.
- No network service, credential, or remote account is required.
- `lov-branding-consistency` is the only optional sibling review for public
  report copy; it is not needed for migration mechanics.
