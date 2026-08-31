# lov-skill-optimizer

![Version](https://img.shields.io/badge/version-0.11.1-CC785C)

自动审计并优化 Agent Skill：按当前对话优先修复问题，统一 README、SKILL.md、
`skill.yaml` 与 CHANGELOG 版本，然后核对规范源、安装副本和 catalog 的同步状态。
支持独立 Skill 目录、嵌套仓库和已安装副本，不把未发现的位置当成已同步。
付费 Skill 仓库会审计 `src/SKILL.md`，同步时只使用 `public/` 加密分发载荷，避免把
明文规范误装到用户目录。

用户反馈先分三层：仅当前任务、单个 Skill 可复用、所有 Skill 全局可复用。全局规则只进入
用户级共享规范（例如生效中的 `AGENTS.md`），不会机械复制到每个 `SKILL.md`；如果之前放错
了领域 Skill，会迁移到共享层并保留真正的领域规则。任何可复用修改都会使修改前的终稿确认
失效，完成当前产物更新后停下等待下一步。

## 安装

```bash
npx skills add lovstudio/skills --skill lov-skill-optimizer -y -g
```

Requires: Python 3.8+（仅标准库）；Git 用于源码提交/推送核验。

## 使用

```bash
# 审计一个独立 Skill
python3 scripts/lint_skill.py --path /absolute/path/to/skill --json

# 检查规范源、安装副本和 catalog
python3 scripts/inspect_layout.py --path /absolute/path/to/skill --json

# 先比较安装副本，不写入
python3 scripts/sync_installation.py \
  --source /absolute/path/to/canonical-skill \
  --target /absolute/path/to/installed-skill --json

# 审阅后同步普通副本；符号链接只做校验
python3 scripts/sync_installation.py \
  --source /absolute/path/to/canonical-skill \
  --target /absolute/path/to/installed-skill --apply --json

# 统一版本并追加 CHANGELOG
python3 scripts/bump_version.py \
  --path /absolute/path/to/skill \
  --type minor \
  --message "add guarded synchronization audit"

# 审计一个 Skills 根目录
python3 scripts/lint_skill.py --all --root /absolute/path/to/skills --json
```

也可以使用 Skill 名称（`foo`、`lov-foo`、`foo-skill`）；跨仓库或已安装副本优先
使用 `--path`，以确保修改落在规范源上。

## 处理顺序

1. 读取当前对话中的具体问题，区分已认可基线、请求增量和被否决的修复尝试；
2. 运行 lint，检查 frontmatter、触发语句、可移植性、版本漂移和脚本 CLI；
3. 只修改规范源；
4. 统一版本、追加 CHANGELOG；
5. 重新 lint 并读取布局检查结果；
6. 比较并同步已发现的安装副本和 catalog；
7. 精确 staging、提交并推送，逐层报告失败状态。

同一请求中出现多个 Skill 时，按用户给出的顺序逐个处理，每个 Skill 单独 bump
版本并单独输出结果块。

## 输出状态

报告固定包含 `source`、`distribution`、`catalog`、`distribution state`、
`catalog state` 和 `sync state`。安装副本已同步但 catalog 未发现时，整体仍为
`partial`；发现 catalog 后还要比较匹配 Skill 的 digest；本地源码提交不等于
catalog 或线上页面已更新。

## 许可

MIT
