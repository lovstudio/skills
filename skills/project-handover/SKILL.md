---
name: lov-project-handover
description: >
  把进行中的项目整理成交给接手方（常同样用 Agent）的交接包：盘点脱敏、补读最新进展、写交接文档与接手约定、清单打包，并在全新目录从零重建验收。
  Use when 用户说“交接这个项目”“做个交接包”或 "hand over this project"。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.9+ (stdlib only); ffmpeg and ffprobe for media_compare.py; the project's own toolchain for the rebuild check."
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags:
    - handover
    - project-management
    - agent-workflow
    - client-work
    - packaging
---

# 项目交接 · Project Handover

把一个做到一半的项目交给别人继续：交出一个对方解开就能接着干的包。里面有一份写清现状、待办和坑的交接文档，一份给接手方 Agent 的工作约定，一份能核对完整性的文件清单，以及经过“在全新目录从零重建”验证的工程。

## Triggers

### Activate when

- “把这个项目交接给小王，他也用 Agent 继续对接甲方”“做一个交接包”“我要转出这个项目，整理一下”。
- “交接本项目以供其他人基于我已有的工作继续”“把工程打包给接手的同事，别带合同和我的账号”。
- "Hand over this project to another team", "prepare a handover package for whoever takes this over".

### Do not activate when

- 接收别人交来的项目：读对方的 `HANDOVER.md` 和 `AGENTS.md` 即可；要把克隆的仓库接到自己的 GitHub，用 `lov-repo-takeover`。
- 只想记一个里程碑或阶段小结，不移交给别人：用 `lov-checkpoint`。
- 只想改进项目的 Agent 指令文件：用 `lov-agent-instructions`。
- 发布成片、上传文件或把包发给对方：本 Skill 只在本地生成和验收，发送由用户自己做。

## Hard Rules

1. **只在本地生成，不发送。** 交接包和 zip 留在本机；发给谁、用什么渠道，由用户决定。不上传、不分享链接、不代发消息。
2. **商务与私人信息默认不出包。** 合同、报价与付款、合作方之间的分成结算、交出方的私人笔记或项目总览、联系人邮箱电话、私聊记录、交出方的账号与密钥，都留在交出方这边。用户明确要求放入的，在交接文档里写明放了什么。
3. **不带凭据，列出接手方要自备的凭据**（按环境变量名和服务列出，不写值）。
4. **事实带日期和来源。** 推断写明是推断；读不到的写“看不到”，并列进“已知缺口”。不编造进度、原话、数字或对方的态度。
5. **原文保真。** 群记录、甲方原话、脚本原文和数据原样转交；品牌门禁只约束新写的交接文字。
6. **交付前在全新目录完整验收。** 解包、核对清单、从零装依赖、跑关键工具、完整重建一次，和原产物比对。验收发现的问题先写回文档，再重新出清单和 zip。
7. **只遮盖生成物里的本机路径。** 运行时会读取的绝对路径，要回到源工程改成相对路径，不能在包里简单替换掉。

## User Profile (cross-session)

本 Skill 接入共享的 `user-profile/v1`（见 `skill.yaml`）。每次运行先读取用户、品牌、工作区、偏好和 `skills.lov-project-handover` 命名空间。会用到的长期记录：

| 记录 | 用途 |
| --- | --- |
| `records.output_dir` | 交接包默认放在项目里的哪个目录，缺省 `output/handover` |
| `records.sender_label` | 交接文档里交出方的称呼 |
| `records.always_exclude` | 每次都不出包的文件或目录模式，例如私人总览的文件名 |

用户直接说出要长期记住的偏好（例如“以后交接都别带 docs/contract”）时，用 `scripts/profile_store.py record ... --confirm` 写入并报告保存路径。推断出来的值只用于当前任务。详见 `references/user-profile.md`。

## Skill Group Composition

开工前读 `references/skill-composition.md`。补读最新进展时可选用聊天、会议、文档类 Skill（例如 `lov-wdb-cowork`、`lov-tencent-meeting-cowork`、飞书文档类能力），交接文档写完可交给 `lov-branding-consistency` 审新写的文字；它们都通过文件或文本交接，不是隐藏依赖。

## Authorship Integrity

交接文档是写给接手方读的成文内容。起草前读 `references/authorship-integrity.md`：先建事实台账（哪些来自项目文件、哪些来自聊天原话、哪些是推断），再写；保留未决问题和反面证据，不为显得完整而补写对方没说过的话。

## Workflow (MANDATORY)

脚本入口：

```bash
SH="python3 $SKILL_DIR/scripts"
```

`SKILL_DIR` 未设置时，从当前 Skill 的安装目录解析。所有脚本只用 Python 标准库。

### Step 0: 明确交接对象和范围边界

从请求和上下文推断，缺了会改变结果才问一个问题：

- 接手方是谁、和交出方什么关系（同公司同事、合作方、外包），是否也用 Agent；
- 接手方接下来要做什么（继续改片、对接甲方、只做后期）；
- 截止节点、对方是否已经进入项目沟通渠道；
- 交出方是否保留部分工作（例如合同内的其他交付、某个账号的发布）。

关系不清又会影响是否放入商务信息时，按 Hard Rule 2 的默认值走，并在最终汇报里列出被排除的内容，让用户决定要不要补。

### Step 1: 盘点

```bash
$SH/handover_scan.py <项目目录> --json <临时目录>/scan.json
```

读报告，记下：

- **体积大头与可重新生成的目录**：依赖树、渲染与构建缓存、预览。名称像缓存的目录里可能藏着必须带走的东西（版本快照、恢复步骤、原始音轨），逐个打开看。
- **密钥与凭据**：报告里的疑似密钥逐条确认；代码读取的凭据环境变量列入交接文档的“环境与账号”。
- **个人信息候选**：区分真联系人和误报（链接里的哈希、接口示例数据）。
- **本机绝对路径**：分清是运行时要读的（回源工程改）还是生成物里的记录（打包后遮盖）。
- **依赖管理器与版本**：锁文件版本、`packageManager` 字段、只含设置的 `pnpm-workspace.yaml`（要 pnpm 10）。
- **项目里现有的交接线索**：README、交付说明、恢复步骤、账本、版本快照。

### Step 2: 补读最新进展

项目自己的笔记常常落后于沟通渠道。交接前用能用的渠道补读最近的消息和会议，确认：

- 对方最后看到的是哪一版，最新提了哪些修改意见（逐条，保留原话要点、时间和提出人）；
- 有没有新人进群、谁负责后续，有没有待确认的脚本、数据或口径；
- 项目笔记里哪些状态已经过时（例如笔记写着“未发送”，渠道里显示早已发出），在交出方自己的笔记里更正，交接文档里写正确的状态。

读到的私人聊天只摘取交接需要的事实；读取工具生成的临时文件用完即删。读不到的渠道（图片、语音、另一个平台的群）写进“已知缺口”。

### Step 3: 定范围，写整理计划

按 `references/scope-and-privacy.md` 的默认规则，把要带走的内容写成计划 JSON（格式见 `assets/plan.example.json`）：源工程与素材、能切换版本的快照、最新成片与各版说明、甲方素材与需求记录、质检报告；排除缓存、依赖树、被否掉的方向、商务与私人文件。交接包放在 `<项目>/<records.output_dir>/<交出方>-<主题>交接包-<YYYY-MM-DD>-v0.1/`。

```bash
$SH/handover_stage.py plan.json --dry-run
$SH/handover_stage.py plan.json
```

预演时核对每一项的文件数和体积；重叠的项会注明“already in an earlier item”。

### Step 4: 遮盖生成物里的本机路径

```bash
$SH/handover_sanitize.py <交接包> --root "<项目绝对路径>=<项目根>"
$SH/handover_sanitize.py <交接包> --root "<项目绝对路径>=<项目根>" --apply
```

先看预演的按目录汇总：改动应该只落在报告、日志、任务记录、校验和这类生成物上。出现 `FUNCTIONAL-LOOKING` 的文件，停下来回源工程把路径改成相对路径，或用 `--protect` 排除；`--apply` 之后剩余数应为 0。

### Step 5: 写交接文档和接手约定

按 `references/handover-doc-template.md` 写三份文件，放在交接包根目录：

- `HANDOVER.md`：概况、甲方与沟通、版本与分支、待办（最新意见逐条）、关键技术决定、工程地图、环境与账号、常用操作、交付惯例、不在包里的东西、已知缺口、验收记录。
- `AGENTS.md`：接手方 Agent 的工作约定，从交出方的项目约定改编；去掉只适用于交出方个人的规则和指向交出方本机文件的引用。
- `CLAUDE.md`：一行指向 `AGENTS.md`（不要用符号链接，Windows 解包会坏）。

写完核对文档里提到的路径都在包里：

```bash
$SH/handover_manifest.py check-refs <交接包> --ignore node_modules/
```

### Step 6: 清单与打包

```bash
$SH/handover_manifest.py build <交接包>
$SH/handover_pack.py <交接包>
```

zip 里不能有 `__MACOSX`、`._*`、`.DS_Store`；`handover_pack.py` 会自检。不要用 Finder 的“压缩”或 `ditto --sequesterRsrc`。

### Step 7: 在全新目录验收

按 `references/acceptance.md` 执行，最少包括：

1. 在临时目录解开 zip，`handover_manifest.py verify` 通过；
2. 对解开的目录再跑一次 `handover_scan.py`，确认没有密钥、联系方式、本机路径；
3. 按交接文档的命令从零安装依赖，做类型检查或构建；
4. 跑交接文档里列出的关键工具（干跑、核对、账本汇总）；
5. 完整重建一次主要产物（整片渲染、构建、导出），用 `media_compare.py` 或项目自己的测试和原产物比对。

每条命令都看它自己的退出码，不要被 `| tail` 吞掉。遇到网络下载失败（镜像源、无头浏览器等），区分“包的问题”和“验收环境的问题”：后者写进文档的坑，可以用等价的本地缓存继续验证包本身。

### Step 8: 把验收结果写回去

- 文档里写错的命令、遗漏的前置步骤、验收中遇到的坑，逐条改进 `HANDOVER.md`；
- 在 `HANDOVER.md` 末尾加“交接验收记录”：每项检查和结果，重建与原产物的比对数字；
- 重新 `build` 清单、重新打包，记下最终 zip 的大小和 SHA-256；
- 删除验收用的临时目录。

### Step 9: 汇报

先说结论（包在哪、多大、SHA-256、验收是否通过），再列：包里有什么、刻意没放什么、接手方要自备什么、已知缺口、验收中修正过的文档问题。在交出方自己的项目笔记里记一笔交接（包的位置、日期、更正过的状态）。不发送，由用户决定发给谁。

## Output Contract

```text
<交接包>/
  HANDOVER.md        交接文档（人和 Agent 的入口）
  AGENTS.md          接手方 Agent 的工作约定
  CLAUDE.md          一行指向 AGENTS.md
  MANIFEST.tsv       path, bytes, sha256
  …                  按计划带走的工程与素材，保持原有相对路径
<交接包>.zip         顶层是交接包文件夹，无平台垃圾文件
```

## Dependencies

- Python 3.9+（只用标准库）；`media_compare.py` 需要 `ffmpeg` 和 `ffprobe`。
- 验收重建需要被交接项目自己的工具链（Node、pnpm、Python 包等），按项目实际情况。
- `lov-branding-consistency`：审交接文档里新写的文字。
