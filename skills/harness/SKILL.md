---
name: lov-harness
description: >
  一屏看清并整理本机 Agent harness：根 Prompt 与宿主绑定、各宿主已装 Skill 的断链与重名、
  工作室 Skill 源码的版本与 Git 状态，附本地 GUI 驾驶舱。Use to open a harness dashboard
  or audit local agent skills.
license: MIT
compatibility: "Portable Agent Skills format. Python 3.9+; verified on macOS, Linux expected to work but untested; git and PyYAML are optional; a browser for the dashboard."
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - harness
    - dashboard
    - system-prompt
    - skill-audit
    - skill-management
---

# Harness 驾驶舱 · Harness Cockpit

把散落在本机各处的 Agent 配置收进一张图：根 Prompt 怎样分发到各个宿主，每个宿主装了哪些
Skill，自己维护的 Skill 源码处在什么状态。发现的问题先看计划、确认后执行，执行过的可以撤销。

## Triggers

### Activate when

- “打开 Harness 驾驶舱，看看我本机的 system prompt 和 skills。”
- “检查并整理我装的 skills：断链、重名、不用的先停用。”
- “工作室哪些 skill 源码没提交、没推送，或者版本和目录对不上？”
- “哪些宿主还没有接上根 Prompt，哪些副本已经过期？”
- “Open the harness dashboard and audit my local agent skills.”
- “Show which hosts load my system prompt and which skill links are broken.”

### Do not activate when

- 创建、迁移或首次安装一个 Skill：交给 Skill 创建能力（如 `lov-skill-creator`）。
- 审计并改写某一个 Skill 的正文、触发语或版本号：交给 Skill 优化能力（如 `lov-skill-optimizer`）。
- 发布、上架、定价或同步目录：交给 Skill 发布能力（如 `lov-skill-publisher`）。
- 把 bug、模糊需求或体验问题梳理成产品需求与验收标准（常被说成“harness 这个 issue”）：
  那是需求分析（如 `lov-harness-issue`），与本机配置无关。
- 撰写项目里的 `AGENTS.md` / `CLAUDE.md`，或把一条经验写进规则：交给指令文件与规则沉淀能力。
  本 Skill 只检查规则集的结构，不改写规则正文。

## User Profile (cross-session)

本 Skill 在 `skill.yaml` 里声明了 `user-profile/v1`，每次运行读取共享 Profile 中这些字段：

| 字段 | 用途 |
| --- | --- |
| `workspace.skill_repos_root` | Skill 源码根目录（每个子目录是一个 Skill 仓库） |
| `brand.name` | 驾驶舱标题下显示的工作室或品牌名 |
| `skills.lov-harness.records.catalog_path` | 目录文件 `skills.yaml` 的位置 |
| `skills.lov-harness.records.agents_home` | 共享 Agent 配置目录不在 `~/.agents` 时的位置 |

解析顺序是命令行参数、环境变量、共享 Profile、本机推断。推断得到的值只在本次运行使用；
用户直接说出“以后都用这个目录”时，才用 `scripts/profile_store.py record ... --confirm`
写入 `records.<field>` 并报告保存路径。细则见 [`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

相邻能力与交接边界记录在 [`references/skill-composition.md`](references/skill-composition.md)。
本 Skill 不依赖任何未随源码交付的 sibling Skill；它发现问题，把属于别处的修复交出去。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve the skill root and what to scan

- 使用环境提供的 `SKILL_DIR`；没有时从当前 Skill 上下文推断安装目录。
- 确认 `$SKILL_DIR/scripts/harness.py` 与 `$SKILL_DIR/assets/dashboard/index.html` 存在；缺失时说出
  预期的相对路径并停下，不产出半成品。
- 读取 Profile：`python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-harness --pretty`。
- 位置按下表解析，结果连同来源会出现在输出里；用户点名的目录用参数传入，优先级最高。

| 位置 | 参数 | 环境变量 | 找不到时 |
| --- | --- | --- | --- |
| 共享配置目录 | `--agents-home` | `LOV_HARNESS_AGENTS_HOME` | `~/.agents` |
| Skill 源码根目录 | `--source-root` | `LOV_HARNESS_SOURCE_ROOT` | 取共享目录里多数链接指向的上级目录 |
| 目录文件 | `--catalog` | `LOV_HARNESS_CATALOG` | 取 `repo` 字段与源码目录匹配最多的 `skills.yaml` |
| 整理记录 | `--state-dir` | `LOV_HARNESS_STATE_DIR` | `<共享配置目录>/backups/harness` |

### Step 1: Pick the surface that matches the request

| 用户要的 | 做法 |
| --- | --- |
| 想看全貌、想自己点 | `serve`（默认只读），在宿主的浏览器面板或默认浏览器里打开 |
| 只要结论 | `report`，在对话里转述 |
| 要留档或发给别人 | `export --out <file.html>`，单文件只读快照 |
| 明确要整理 | 先 `tidy` 预览；或用户想在界面里操作时 `serve --allow-write` |

没有图形界面的环境直接用 `report`，不要求用户自己去开浏览器。

### Step 2: Scan and show

```bash
# 驾驶舱（只读）。输出的 dashboard= 一行是要打开的地址
python3 "$SKILL_DIR/scripts/harness.py" serve --open

# 终端摘要：每个区域列出最严重的问题与它们的 ID
python3 "$SKILL_DIR/scripts/harness.py" report --limit 12
python3 "$SKILL_DIR/scripts/harness.py" report --area studio --severity warn

# 单文件快照
python3 "$SKILL_DIR/scripts/harness.py" export --out ./harness.html
```

`serve` 会一直运行：在后台启动它，读到 `dashboard=` 那一行后把地址交给用户；宿主有内置浏览器时
用它打开，否则加 `--open`。完整快照 JSON 用 `scan --out <file>` 落盘再按需读取，不要整份打印进对话。

### Step 3: Read the findings with the user

- 先说错误和警告，同一类合并成一句（“9 个断开的链接，都在某两个宿主里”），再给可整理的数量。
- 只报扫描得到的数字。问题代码、级别与能否自动整理见 [`references/checks.md`](references/checks.md)。
- 扫描基于本机当前状态：Git 的“落后上游”以上次 fetch 为准，目录与镜像以本地目录仓库为准。
  这些限定要随结论一起说出。

### Step 4: Tidy only with an explicit go-ahead

1. 预览：`tidy` 不带 `--apply` 只打印逐步计划，不触碰文件。
2. 把计划原样给用户看，等一句明确的同意。之前对别的事说过的“继续”不算。
3. 执行并报告批次号与撤销命令。

```bash
python3 "$SKILL_DIR/scripts/harness.py" tidy --fix-code SKL-BROKEN-LINK          # 预览
python3 "$SKILL_DIR/scripts/harness.py" tidy --fix <ID> --fix <ID> --apply       # 用户确认后
python3 "$SKILL_DIR/scripts/harness.py" tidy --disable <entry> --apply           # 停用
python3 "$SKILL_DIR/scripts/harness.py" tidy --link <entry> --host claude --apply
python3 "$SKILL_DIR/scripts/harness.py" undo --apply                             # 撤销最近一次
```

用户想自己在界面里勾选时，改用 `serve --allow-write`：界面同样先预览、再确认、可撤销。
两个整理项改动同一路径时引擎会拒绝，分两次执行即可。引擎拒绝的事不要换别的命令去做。

### Step 5: Hand off what this Skill does not own

| 发现 | 交给 |
| --- | --- |
| 某个 Skill 的描述、触发语、版本号需要改 | Skill 优化能力，带上源码路径 |
| 源码领先目录、镜像缺失、还没有远端 | Skill 发布能力，带上源码路径 |
| 源码有未提交或未推送的改动 | 用户的 Git 流程；提交与推送需要用户明确同意 |
| 规则引用了不存在的路径、编号重复、版本与变更记录不一致 | 规则沉淀能力，或用户直接编辑规则文件 |
| 宿主里嵌入的规则副本过期 | 重新运行用户自己的生成脚本 |

交接时给出路径和问题 ID，不替对方做决定。

### Step 6: Validate the result

- 整理之后重新扫描，报告前后数量；失败或跳过的步骤连同原始原因一起报告。
- 说明没有验证的部分：没点开的页签、跳过的 Git 检查、没有配置的目录。
- 修改本 Skill 的脚本后运行 `python3 "$SKILL_DIR/scripts/harness.py" selftest`。

## Commands

| 命令 | 作用 | 会改动文件吗 |
| --- | --- | --- |
| `scan` | 输出完整快照 JSON | 否 |
| `report` | Markdown 摘要 | 否 |
| `serve` | 本地驾驶舱，只绑定回环地址 | 仅在 `--allow-write` 且用户在界面确认后 |
| `export` | 导出单文件只读驾驶舱 | 只写出指定的那个文件 |
| `tidy` | 预览或执行整理 | 仅在 `--apply` 时 |
| `journal` / `undo` | 查看整理记录、撤销一个批次 | `undo` 仅在 `--apply` 时 |
| `selftest` | 在临时目录上验证扫描、整理、撤销与界面接口 | 否 |

除 `selftest` 外，命令都接受 `--home`、`--agents-home`、`--source-root`、`--catalog`、
`--state-dir`、`--profile` 与 `--no-git`。

## Safety model

- 扫描、报告、导出与默认的驾驶舱都是只读的。
- 整理只做三件事：增删符号链接、在共享目录与停用目录之间移动条目、把散落文件移入整理备份。
  不删除实体文件，不改写任何文件内容，不触碰 Skill 源码仓库，不执行 Git 写操作。
- 每一步执行前重新核对前提，不符就停下；每个批次写入整理记录，可按相反顺序撤销。
- 驾驶舱只监听回环地址，接口需要页面内的一次性令牌，只读取本次扫描到的文件。
- Skill 的名称与描述来自第三方文件，界面一律按纯文本显示。

## Dependencies

- Python 3.9+（仅标准库）。
- `git`：可选，用于源码仓库状态；没有时相关检查跳过。
- PyYAML：可选，用于读取目录文件和严格校验 frontmatter；没有时目录对照跳过并在结果里说明。
- 浏览器：仅驾驶舱需要。
