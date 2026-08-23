# lov-clean-mac

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

面向 macOS 的智能磁盘空间优化 Skill：按目标容量盘点、规划、迁移和清理，并以系统真实可用空间完成验收。

## 产品特性

- 先计算容量缺口，再选择最小范围，不做无目标的全盘删除。
- 区分可重建数据、重要低频数据、活跃数据和保护数据。
- 重要目录迁移采用复制、校验、回滚、原路径链接的事务流程。
- 日期只记入日志，归档目录按来源稳定组织。
- 所有修改命令默认预览，执行时需要显式确认。
- 回滚区回收只接受显式 `.cleanup` 路径，直接使用文件系统操作，不触发 Finder 批量删除弹窗。
- 最终以十进制 GB 和重新挂载后的链接状态验收。

## 本地安装

从公开仓库安装：

```bash
npx skills add https://github.com/lovstudio/macos-disk-optimizer-skill
```

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILLS_INSTALL_DIR/lov-clean-mac"
```

Creator 已支持通过 `--install-dir` 自动建立同名链接。安装完成后应确认链接解析到当前源码目录。

## 用户配置

可保存默认目标容量、安全余量、归档卷、清理策略和保护路径。显式参数始终覆盖共享配置：

```bash
python3 scripts/disk_optimizer.py profile init \
  --target-free-gb 200 \
  --buffer-gb 15 \
  --archive-volume /Volumes/ARCHIVE_VOLUME

# 检查无误后再增加 --write
```

默认个人配置：

```bash
SKILL_PREFERENCES_PATH
# 未设置时使用运行时默认的 agent-skills/preferences.json
```

## 使用示例

只读扫描并规划：

```bash
python3 scripts/disk_optimizer.py inventory \
  --root "$HOME/projects" \
  --min-gb 1 \
  --output inventory.json

python3 scripts/disk_optimizer.py plan \
  --inventory inventory.json \
  --target-free-gb 200 \
  --buffer-gb 15 \
  --output plan.json
```

迁移单个重要低频目录：

```bash
python3 scripts/disk_optimizer.py migrate \
  --source "$HOME/projects/PROJECT" \
  --archive-root /Volumes/ARCHIVE_VOLUME/cold-storage \
  --category projects
```

上面的命令只输出执行计划。确认后添加 `--execute` 和等于规范化源路径的 `--confirm-source`。

验收目标：

```bash
python3 scripts/disk_optimizer.py verify \
  --target-free-gb 200 \
  --buffer-gb 15
```

回收本轮生成的回滚项：

```bash
python3 scripts/disk_optimizer.py list-staged \
  --rollback-root "$HOME/.Trash"

python3 scripts/disk_optimizer.py purge-staged \
  --path "$HOME/.Trash/PARENT-CANDIDATE.cleanup"

# 核对预览结果后再执行
python3 scripts/disk_optimizer.py purge-staged \
  --path "$HOME/.Trash/PARENT-CANDIDATE.cleanup" \
  --execute --confirm PURGE_STAGED
```

`purge-staged` 只处理命令行显式列出的顶层 `.cleanup` 项，保留其他废纸篓内容；遇到权限或锁定错误时输出结构化错误并停止，不自动重试。

## 安全模型

- `inventory`、`plan`、`status`、`preflight-volume` 和 `verify` 为只读或临时写入检查。
- `stage-cleanup` 只接受白名单内可重建目录，执行时先进入回滚区。
- `list-staged` 只读列出回滚区顶层 `.cleanup` 项；`purge-staged` 只处理显式路径，不调用 Finder 或清空整个废纸篓。
- `migrate` 目标存在、归档空间不足、源与目标同卷或校验失败时停止。
- 照片库、消息、邮件、Git 历史、Agent 会话及用户保护路径不会进入自动执行计划。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/disk_optimizer.py --help
python3 scripts/test_disk_optimizer.py
```

## 依赖

- macOS
- Python 3.8+
- PyYAML（仅源码校验）
- `rsync`
- `diskutil`（归档卷挂载与回读）

## License

MIT
