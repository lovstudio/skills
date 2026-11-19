# 封装成专属写作 Skill

用户说“封装成 Skill”“以后能按他的风格写”时，把冻结风格包变成一个独立的写作 Skill。本 Skill 只写内容；骨架、校验与安装由 `lov-skill-creator` 负责，发布由 `lov-skill-publisher` 负责，且只在用户要求时进行。

## 命名

- **ID**：`lov-SLUG-style-writer`，源码目录 `SLUG-style-writer-skill`。
- **展示名**：“某某风格写作”。展示名里的博主名只说明参考来源，卡片与 README 必须写明“参考不表示合作或授权”。
- 用户给了名字就用用户的。

## 步骤

1. 确认 `holdout_checked`（未完成时需用户同意，并用 `--allow-unchecked`，卡片会写明未检验）。
2. 用 creator 初始化骨架，内容类别为 `authored-prose`：

   ```bash
   python3 "$CREATOR_DIR/scripts/init_skill.py" SLUG-style-writer --content-class authored-prose --path PARENT_DIR
   ```

   不带 `--install-dir` 时只生成源码、不安装。
3. 写入内容：

   ```bash
   python3 "$SKILL_DIR/scripts/cloner.py" package --project DIR --pack PACK --into PARENT_DIR/SLUG-style-writer-skill \
     --english-name "Name" --description "50–200 字的路由描述，含中英文触发语"
   ```

4. 在新源码目录运行 `python3 scripts/validate_skill.py .`，再用一个写作请求试一次，并跑一次 `scripts/stylometry.py audit`。
5. 安装或发布只在用户要求时做。

## 带走什么

- `assets/style-pack/`：`style-profile.json`、`evidence.jsonl`（短引文）、`metrics.train.json`、`brand.json`、`corpus-shingles.json`（哈希指纹）、`FROZEN.json`、`holdout-report.json`、`PACKAGED.json`。
- `references/style-profile.md`（渲染的画像）与 `references/writing-protocol.md`。
- `scripts/stylometry.py`（审计，原样复制）。
- `SKILL.md`、`README.md`、卡片、一条来自盲测的案例、定价卡。

## 封装时的变换

- 固定段落（品牌位）的匹配键改为 SHA-1，文本里的邮箱和链接替换为占位；
- 去掉作者头像地址；
- 其余文件与冻结包逐字节一致，变换记录写进 `PACKAGED.json`。

## 绝不带走

原文全文、基线语料、留出全文、截图与配图、试稿以外的任何原作段落、作者的联系方式与头像、凭据与本机绝对路径。

## 交接检查

- 新源码校验通过；`FROZEN.json` 与 `PACKAGED.json` 都在；
- 审计能在包内独立运行，且对试稿的结果与原风格包一致；
- 写入作者名字的探针稿审计失败；
- 卡片如实写出留出结果、带内比例与“尚无人工盲评”（如适用）。
