# lov-rename-project

![Version](https://img.shields.io/badge/version-2.3.1-CC785C)

可审计的项目重命名 Skill：先生成计划，再替换普通产品名引用，单独审阅
CLI 别名、存储命名空间、迁移、Schema 与环境变量等兼容契约；同时覆盖项目
根目录迁移、运行中进程、启动器与宿主项目索引，以及历史任务 `cwd` 兼容，
最后精确提交、推送并回读 GitHub 仓库状态。

## 安装

```bash
npx skills add lovstudio/skills --skill lov-rename-project
```

Requires: Python 3.8+、Git；GitHub 仓库回读另需 `gh` CLI。

## 快速开始

```bash
# 只扫描，不改文件
python3 scripts/rename_project.py Ataru --old-name lovcode \
  --report /tmp/rename-project-plan.json

# 跳过项目自定义的生成目录（可重复）
python3 scripts/rename_project.py Ataru --old-name lovcode \
  --skip-dir private-runtime --report /tmp/rename-project-plan.json

# 审阅计划后应用普通引用
python3 scripts/rename_project.py Ataru --old-name lovcode --apply

# 完成精确 staging、提交和推送；GitHub 改名最后回读验证
python3 scripts/rename_project.py Ataru --old-name lovcode \
  --apply --commit --push --github
```

默认跳过二进制、生成目录和 lockfile，并把可能影响兼容性的文件列为
`compatibility_review`；只有显式传入 `--include-compat` 才会处理这类引用。
`.runtime`、`.codex-upstream` 等私有运行副本默认不扫描，也可通过重复的
`--skip-dir` 排除项目特有生成目录。
存储目录、`Application Support`、搜索索引和 `join("旧名称")` 等路径型引用
也会进入兼容审阅。若只迁移指定数据路径，可以使用重复的
`--include-compat-path`，避免批量处理旧 CLI、环境变量和迁移契约。

若重命名包含目录迁移，Skill 会把“源码替换、根目录移动、运行时重建、宿主
项目注册、历史任务兼容”作为不同层处理：运行中的 Agent 不会为了改名被
强制退出；需要时保留旧路径符号链接，并通过宿主 UI/API 回读新项目名、路径
和稳定 project ID，确认既有任务仍可搜索和重开。
完整流程见 [SKILL.md](SKILL.md)。
