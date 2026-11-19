---
name: lov-blogger-cloner
description: >
  克隆任一博主的文字风格，先支持公众号：冻结训练与留出拆分，度量加逐篇通读，写出带逐字证据的八维规则与品牌位，盲测留出后封装成能写同风格文章的专属 Skill。Use when: 克隆这个博主的文风、clone a blogger's writing voice.
license: MIT
compatibility: "Python 3.9+ standard library for scripts/cloner.py and scripts/stylometry.py; PyYAML for the Profile helper and validator. Corpus from a lov-wxmp-cli export or any Markdown/TXT directory; packaging uses lov-skill-creator."
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags:
    - style-clone
    - creator-analysis
    - chinese-writing
    - wechat
    - evidence
    - holdout
---

# 博主克隆 · Creator Clone

给一个博主（公众号名称、账号或一组文章），产出一份有证据的文字风格包，并能封装成按这个风格写作的专属 Skill。先取样并在阅读前冻结训练/留出拆分，再度量、逐篇通读训练样本，写出八个维度的规则：每句原话都能在原文中逐字找到，每个数字都能回读到度量文件。冻结后先盲写试稿、再打开留出原文检验。迁移的是写法、结构与品牌位的形态，不复制作者身份、原文句子和观点。

## Triggers

### Activate when

- “克隆一下公众号「某某」的文风，以后让 AI 按他的风格写文章。”
- “把这个博主的文章都拉下来，蒸馏出他怎么遣词造句、怎么讲观点，还有他的品牌信息。”
- “我想复刻这个作者，做一个能写出他那种质量文章的 Skill。”
- “Clone this blogger's writing voice from their WeChat articles and package it as a Skill.”

### Do not activate when

- 只要下载或导出文章：交给 `lov-wxmp-cli`（公众号）或 `lov-media-crawler`（其他平台）。
- 复刻视频的剪辑、包装和画面风格：交给 `lov-media-cloner`。
- 粘贴一两篇样本、马上改写一篇稿子：交给 `lov-style-clone`。
- 已经有某位博主的专属写作 Skill，只是要按它写：直接用那个 Skill。
- 写使用者本人的文风：交给 `lov-writing-style`。
- 冒充博主发文、洗稿、搬运原文：不做。风格参考不构成身份或内容授权。

## User Profile (cross-session)

每次运行读取 `skill.yaml`、共享 `user-profile/v1` 与本 Skill records，优先级为当前请求、项目上下文、Skill records、共享偏好、用户/品牌 Profile、安全默认值。

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" read --skill-id lov-blogger-cloner --pretty
```

本 Skill 的 records：`projects_root`（克隆工作区根目录）、`baseline_accounts`（做对照语料的同赛道账号）、`split`（默认留出篇数）。用户明确要长期沿用的值，用 `scripts/profile_store.py record --confirm` 保存并报告路径；凭据、Cookie 和被分析博主的信息不写入 Profile。详见 `references/user-profile.md`。

## Skill Group Composition

运行前读 `references/skill-composition.md`。这是 Single Skill：取样、度量、规则、冻结、盲测、留出和封装共用一个工作区和一套台账。文章导出、发布和 Skill 校验安装都只通过文件交接。

## Authorship Integrity

写风格说明书、规则和盲测试稿前读 `references/authorship-integrity.md`。每个判断都要追到规则、证据或度量；原作的观点和商业立场是原作者的，不是本 Skill 验证过的事实；例外、未中和未知项必须保留。

## Workflow (MANDATORY)

所有命令打印 JSON（`show` 除外，它打印带段号的正文），失败时退出码非零。`C="$SKILL_DIR/scripts/cloner.py"`。

### Step 0: Resolve and resume

运行 `python3 "$C" doctor --root PROJECTS_ROOT`。已有工作区先跑 `python3 "$C" status --project DIR`，从 `next_state` 继续，不重做已完成的步骤。

### Step 1: Scope the creator

确认平台、账号显示名和要复刻的格式期（改版前后只取一个期，除非用户另有要求）。初始化：

```bash
python3 "$C" init --slug SLUG --creator "博主显示名" --platform wechat --root PROJECTS_ROOT
```

会改变结果的未知项（同名账号、格式期歧义、要不要封装）只问一个问题。

### Step 2: Acquire the corpus

读 `references/platforms-and-corpus.md`。公众号用 `lov-wxmp-cli` 导出到 `research/wxmp-export`，再导入；其他平台把文字（帖子、转写稿）整理成 Markdown 目录用 `--source files`。另导入 3–6 个同赛道账号作基线语料，用来区分个人口头禅和赛道通用词。

```bash
python3 "$C" ingest --project DIR --source wxmp-export --path DIR/research/wxmp-export
python3 "$C" ingest --project DIR --source wxmp-export --path BASELINE_EXPORT --role baseline --label 账号名
```

### Step 3: Select and freeze the split before reading

```bash
python3 "$C" candidates --project DIR
python3 "$C" select --project DIR --holdout ID1,ID2,ID3 --exclude ID --note "分层理由"
python3 "$C" freeze-split --project DIR
```

只看标题、日期、篇幅和标记选样，按子类型分层，留出约 15–20%（至少 1 篇，训练至少 3 篇）。冻结后改样本或拆分，所有工具都会拒绝运行；要换样本就开新工作区。

### Step 4: Measure the training set

```bash
python3 "$C" metrics --project DIR
```

得到句长、段长、一句成段、标点、人称、英文与数字密度、配图、标题形态、标志短语（相对基线的倍率）和固定段落（品牌位）。度量只覆盖训练集。

### Step 5: Read every training article and draft rules

读 `references/dimensions.md` 与 `references/rules-and-evidence.md`。用 `python3 "$C" show --project DIR --id ID` 逐篇通读全部训练样本（留出样本此时被封存），把每篇的开头、结构、口头禅、论证、结尾和品牌位记进 `research/reading-notes.md`，再写 `research/rules-draft.json`：八个维度齐全，每条规则写观察、写法、强度、适用分母、置信、范围、例外、验收与证据。

```bash
python3 "$C" build --project DIR --draft DIR/research/rules-draft.json --out DIR/style-pack/SLUG-v0.1
python3 "$C" verify --project DIR --pack DIR/style-pack/SLUG-v0.1
```

构建失败时看 `research/rules-draft.build-report.json`：找不到的引文附有最接近的原文段落。不改原文去迁就引文。

### Step 6: Freeze

```bash
python3 "$C" freeze --project DIR --pack DIR/style-pack/SLUG-v0.1
```

### Step 7: Blind trials before opening the holdout

读 `references/holdout-and-trials.md`。`holdout-brief` 只给留出文章的标题与摘要。按画像为每篇写一篇试稿（不编造实测、数字和经历），可再写一篇不参考画像的对照稿；用 `scripts/stylometry.py audit` 自查后登记：

```bash
python3 "$C" holdout-brief --project DIR --pack PACK
python3 "$C" trial-register --project DIR --pack PACK --holdout ID --label pack --draft FILE
```

### Step 8: Open the holdout and check every rule

```bash
python3 "$C" holdout-open --project DIR --pack PACK
python3 "$C" holdout-fill --project DIR --pack PACK --annotations DIR/research/holdout-annotations.json
python3 "$C" holdout-check --project DIR --pack PACK --write-summary
python3 "$C" blind --project DIR --pack PACK
```

逐篇通读留出原文，每个“规则 × 留出样本”记 hit / partial / miss / not_applicable，命中要附留出原文的引文。修订意见写进 `suggested_revisions`，进入下一版，不回改冻结包。`blind` 生成真假配对，交给人工盲评后用 `blind-score` 记分；Agent 不替读者作答。

### Step 9: Style guide

```bash
python3 "$C" render --project DIR --pack PACK --out DIR/deliverables/SLUG-style-guide-v0.1.md
```

说明书按 `references/deliverables.md` 补充一句话本质、方法与局限，先过 `lov-branding-consistency` 的读者可见文本门禁；引文与数字保持原样。

### Step 10 (on request): Package as a writing Skill

读 `references/packaging.md`。用 `lov-skill-creator` 初始化 `lov-SLUG-style-writer` 骨架，再写入风格包与写作协议，并跑校验器：

```bash
python3 "$C" package --project DIR --pack PACK --into SKILL_SOURCE --english-name "Name" --description "50–200 字的路由描述"
```

安装与发布只在用户要求时进行，分别交给 `lov-skill-creator` 与 `lov-skill-publisher`。

## States and reporting

`ingested`、`sampled`、`split_frozen`、`measured`、`drafted`、`verified`、`frozen`、`trial_registered`、`holdout_opened`、`holdout_checked`、`guide_rendered`、`packaged` 分别报告。度量带吻合只是表层指标，不是质量或相似度分；不编造盲评结果。留出结果按覆盖率、独立命中、未中和受污染项分开写。

## Dependencies

Python 3.9+ 标准库即可运行克隆流水线与审计；`scripts/profile_store.py` 与 `scripts/validate_skill.py` 需要 PyYAML。公众号文章导出由 `lov-wxmp-cli` 完成，封装骨架由 `lov-skill-creator` 生成；它们通过文件交接，不是隐藏依赖。
