---
name: lov-macos-disk-optimizer
description: >
  This skill should be used for “帮我清出至少 200GB”、“智能清理 Mac 磁盘”、“处理归档卷”、“避免 Finder 清理弹窗” or “optimize my Mac disk space”; it plans guarded cleanup, migration, and capacity verification.
license: MIT
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
metadata:
  author: contributors
  version: "0.2.0"
  tags:
    - macos
    - disk-cleanup
    - cold-storage
    - storage-optimization
  compatibility: "macOS; Python 3.8+; rsync; diskutil; direct filesystem access for exact rollback-item purging."
  dependencies: []
---

# lov-macos-disk-optimizer — macOS 磁盘空间智能优化

在保护用户资料、活跃项目与原有路径的前提下，将 Mac 的真实可用空间提升到指定目标。先只读盘点与生成计划，再对明确候选执行可回滚清理或冷存储迁移，最终以系统数据卷的真实字节数验收。

## Triggers

### Activate when

- 用户说“帮我清出至少 200GB”“智能清理一下 Mac 磁盘”或“把暂时不用的重要资料迁移到外置盘”。
- 用户提供 Mole、DaisyDisk、Finder 储存空间或 `du` 扫描结果，希望直接分析并执行安全优化。
- 用户说 “optimize my Mac disk space”, “free TARGET_GB on macOS”, or “archive inactive files to an external drive”。

### Do not activate when

- 用户要诊断 SMART 告警、坏道、文件系统损坏或恢复误删文件；交给存储健康或数据恢复能力。
- 用户要抹盘、重新分区、格式化系统卷或迁移整个 macOS 安装；交给磁盘管理流程。
- 用户只要管理云端配额，或目标系统不是 macOS。
- 用户只问某个文件是否重要但没有容量优化目标；先回答该文件用途，不启动整盘工作流。

## User Configuration

此 Skill 可保存默认目标容量、安全余量、归档卷、清理策略和保护路径。严格按 [用户配置](references/user-config.md) 解析；显式请求和 CLI 参数始终优先，不把任何个人路径写入 Skill 源码。

## Required Resources

- `$SKILL_DIR/scripts/disk_optimizer.py`
- `$SKILL_DIR/references/safety-and-classification.md`
- `$SKILL_DIR/references/user-config.md`

## Workflow (MANDATORY)

### Step 0: 解析目标与边界

1. 解析 `TARGET_FREE_GB`，默认按十进制 GB 理解；若用户只说“多留一点”，先读取当前空间并给出带 15 GB 余量的合理目标。
2. 解析可选 `ARCHIVE_VOLUME`、`PROTECTED_PATHS`、清理策略和是否保持原路径链接。
3. 把人物、项目背景、目录别名和“为什么暂时不用”等信息视为内部判断线索，默认不写入最终报告。
4. 任何修改前阅读 [安全与分类](references/safety-and-classification.md)。

### Step 1: 建立真实容量基线

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" status
```

- 以 `/System/Volumes/Data` 的真实可用字节数为完成口径。
- 计算 `TARGET_FREE_GB + BUFFER_GB - 当前可用空间`。
- 目标已达到时仍检查是否有明确的低风险优化诉求；不要为了“清理感”扩大范围。

### Step 2: 只读盘点并生成最小计划

只扫描与当前任务相关的根目录。将运行时路径写入任务临时目录，不写回 Skill 源码。

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" inventory \
  --root ROOT_A --root ROOT_B \
  --protected PROTECTED_PATH \
  --min-gb 0.5 \
  --output INVENTORY_JSON

python3 "$SKILL_DIR/scripts/disk_optimizer.py" plan \
  --inventory INVENTORY_JSON \
  --target-free-gb TARGET_FREE_GB \
  --buffer-gb BUFFER_GB \
  --output PLAN_JSON
```

计划优先级固定为：

1. 官方清理命令可重建的缓存、模拟器、依赖与构建产物；
2. 明确低频且重要的资料迁移到冷存储；
3. 其他大目录只进入人工复核；
4. 保护数据永不进入执行计划。

修改日期只作信号，不能单独证明目录闲置。不同目录中包含同一构建产物时，不重复计算释放量。

### Step 3: 预检外置归档卷

需要迁移时先执行：

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" preflight-volume \
  --archive-root ARCHIVE_ROOT \
  --required-gb REQUIRED_GB
```

- 确认卷已挂载、可写、剩余空间充足，源与目标不在同一卷。
- 使用按内容来源稳定组织的目录，如 `cold-storage/projects`、`cold-storage/media`；日期只进入日志，不作为主目录层级。
- 目标已存在时停止覆盖，先判断它是正式归档还是不完整副本。

### Step 4: 执行可重建清理

优先调用工具自身的清理命令，例如 npm、Homebrew、CocoaPods、Xcode 或模拟器命令。没有专用命令时，对白名单内的明确目录使用两阶段清理：

```bash
# 先预览
python3 "$SKILL_DIR/scripts/disk_optimizer.py" stage-cleanup \
  --path REBUILDABLE_PATH

# 明确执行，只移入回滚区，不清空废纸篓
python3 "$SKILL_DIR/scripts/disk_optimizer.py" stage-cleanup \
  --path REBUILDABLE_PATH \
  --execute --confirm STAGE_REBUILDABLES
```

禁止向脚本传入用户目录、磁盘根目录、Git 历史、照片库、消息、邮件、Agent 会话或额外保护路径。多路径执行时让脚本完成全部预检；任一路径发生权限或锁定错误时，脚本应回滚本轮已经移动的路径并返回结构化错误。

### Step 5: 事务式迁移重要低频资料

每个候选独立执行“复制 → 校验 → 源进入本机回滚区 → 原路径链接 → 记录日志”：

```bash
# 先预览
python3 "$SKILL_DIR/scripts/disk_optimizer.py" migrate \
  --source SOURCE_PATH \
  --archive-root ARCHIVE_ROOT \
  --category media

# 用户已要求直接执行时，确认字符串必须等于规范化源路径
python3 "$SKILL_DIR/scripts/disk_optimizer.py" migrate \
  --source SOURCE_PATH \
  --archive-root ARCHIVE_ROOT \
  --category media \
  --verify metadata \
  --execute --confirm-source NORMALIZED_SOURCE_PATH
```

- 高价值小型资料使用 `--verify checksum`；大型媒体可使用完整相对路径、文件数和字节数校验。
- 复制中出现动态文件、权限、资源分支或目标冲突时，停止该候选并保留源目录；换一个稳定候选补足容量。
- 代码与普通数据默认不复制资源分支；只有确认应用包依赖扩展属性时使用 `--preserve-xattrs`。
- 外置卷断开时符号链接暂时不可用，最终报告必须说明这一点。

### Step 6: 精确回收本轮回滚项

清理前确认所有迁移写入结束，并正常卸载归档卷。不要调用 Finder 的批量 `delete`、`empty trash` 或自动重试；锁定或系统保护项目会触发模态确认框，重复提交会造成弹窗风暴。

先列出本机回滚区内由本 Skill 生成的项目：

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" list-staged \
  --rollback-root "$HOME/.Trash" \
  --output STAGED_JSON
```

只把 `STAGED_JSON` 中明确的顶层 `.cleanup` 路径传给预览命令：

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" purge-staged \
  --path ROLLBACK_ITEM \
  --output PURGE_PLAN_JSON
```

核对路径、大小和项目数量后，使用显式确认执行：

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" purge-staged \
  --path ROLLBACK_ITEM \
  --execute --confirm PURGE_STAGED \
  --output PURGE_RESULT_JSON
```

该命令只删除显式 `.cleanup` 项，保留用户原有废纸篓内容，不跟随符号链接，不重试失败项，并输出每个项目的 `purged`、`already-absent` 或 `error` 状态。发生错误时停止并保留剩余回滚项。完成后重新挂载归档卷，再验证迁移链接和真实容量。

### Step 7: 真实验收与最小补充

```bash
python3 "$SKILL_DIR/scripts/disk_optimizer.py" verify \
  --target-free-gb TARGET_FREE_GB \
  --buffer-gb BUFFER_GB \
  --link MIGRATED_SOURCE_PATH
```

- `passed=true`、容量达到 `TARGET_FREE_GB + BUFFER_GB`、所有迁移链接重新挂载后有效，三项同时成立才算完成。
- 若只差少量空间，仅追加最小必要的可重建构建产物；不要扩大到照片、会话、浏览器资料或活跃源码。
- 最终报告列出：清理前后容量、实际释放量、迁移映射、已清理类别、保留项、重建代价、断盘影响和未解决异常。

## Failure Recovery

- 动态文件或复制失败：源目录保持原状；将不完整目标移出正式归档树后再决定重试。
- 校验差异：不移动源目录、不建立链接；重新同步差异并复验。
- 清理后空间不增长：检查本机废纸篓、APFS 快照和仍被进程占用的文件，再读取真实数据卷容量。
- Finder 出现删除确认框：立即停止调用 Finder 的自动化进程，读取 `list-staged`，改用 `purge-staged` 的显式路径模式；不要重复提交同一批删除。
- `purge-staged` 返回 `partial-failure`：保留错误项目和结构化结果，逐项复核权限或占用状态后再由用户发起新的显式操作。
- 重新挂载后链接失效：核对卷名和归档位置；回滚副本清空前优先修复链接。
- 执行脚本返回退出码 `3`：表示目标或候选不足，不是脚本崩溃；继续最小补充或报告差额。

## Validation

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
python3 "$SKILL_DIR/scripts/disk_optimizer.py" --help
python3 "$SKILL_DIR/scripts/disk_optimizer.py" status
python3 "$SKILL_DIR/scripts/test_disk_optimizer.py"
```

激活回归：“帮我清出至少 200GB，并把低频资料放到外置盘。”

不触发回归：“这块 SSD 的 SMART 告警意味着什么？”

## Dependencies

- macOS
- Python 3.8+
- `rsync`
- `diskutil` 用于归档卷挂载与回读；回滚项回收使用 Python 直接文件系统操作，不调用 Finder

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
