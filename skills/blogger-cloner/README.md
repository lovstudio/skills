# 博主克隆 · Creator Clone

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把一个博主的文章拉下来，蒸馏出他怎么开头、怎么讲观点、怎么遣词造句、品牌位放在哪里，得到一份有逐字证据、经过留出检验的风格包；需要时再封装成能按这个风格写文章的专属 Skill。先支持公众号，其他平台的文字（帖子、口播转写）以 Markdown 目录接入。

## 它怎么保证“像”而不是“抄”

- **阅读前冻结拆分**：先选训练集和留出集再读正文，留出文章在风格包冻结前被工具封存。
- **逐字证据**：每条规则的原话都能在训练原文中逐字找到，支持数由证据推出。
- **盲测在先**：冻结后只凭留出文章的标题和摘要写试稿，登记后才打开原文检验每条规则。
- **对照组**：同题再写一篇不用画像的对照稿，比较度量带吻合。
- **防抄袭与防冒充**：审计检查与语料的连续重合（20 字以上即失败）和作者身份标识。

## 本地安装

```bash
npx lovstudio skills add blogger-cloner -g -y
```

或从源码链接：

```bash
ln -s "$(pwd)" ~/.agents/skills/lov-blogger-cloner
```

## 使用

- “克隆一下公众号「某某」的文风，以后让 AI 按他的风格写文章。”
- “把这个博主的文章都拉下来，蒸馏出他的遣词造句、论证方式和品牌信息，再封装成 Skill。”

流水线命令都在 `scripts/cloner.py`，完整顺序见 [`SKILL.md`](SKILL.md)：

```text
init → ingest → candidates → select → freeze-split → metrics → show（通读）
→ build → verify → freeze → holdout-brief → trial-register → holdout-open
→ holdout-fill → holdout-check → blind → render → package
```

单独审计一篇草稿：

```bash
python3 scripts/stylometry.py audit --pack STYLE_PACK_DIR --draft draft.md
```

## 真实案例

公众号「数字生命卡兹克」：微探缓存 20 篇（18 篇有正文），训练 15 篇、留出 3 篇，另以 6 个 AI 科技账号的 79 篇为基线。写出 39 条规则、257 条证据；留出检验 117 项全部标注，命中 87、部分 17、未中 4、不适用 9。度量带吻合均值：作者本人留出原文 0.70、按画像写的盲测稿 0.71、不用画像的对照稿 0.34。封装出的 `lov-kazike-style-writer` 通过 creator 校验，未安装。人工盲评配对已生成，尚未评分。详见 [`cases/kazike-clone/summary.json`](cases/kazike-clone/summary.json)。

## 用户 Profile（跨 session）

读取共享 `user-profile/v1`。本 Skill 的 records：`projects_root`、`baseline_accounts`、`split`。被分析博主的信息不写入 Profile。详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

上游：`lov-wxmp-cli`（公众号导出）、`lov-media-crawler`、`lov-voice2srt`；下游：`lov-skill-creator`（封装骨架与校验）、可选 `lov-skill-publisher`。视频风格交给 `lov-media-cloner`，粘贴即改写交给 `lov-style-clone`。详见 [`references/skill-composition.md`](references/skill-composition.md)。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -I scripts/test_pipeline.py
```

## 依赖

- Python 3.9+（流水线与审计只用标准库）
- PyYAML（Profile 与校验器）
- `lov-branding-consistency`

## License

MIT。被分析作品的文字、身份与品牌的权利不因分析而转授，风格包与封装产物不含原文。
