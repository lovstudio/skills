# 封装成专属风格 Skill

用户说“封装成 Skill”时，把冻结的风格包变成一个专属 Skill，让以后的会话能直接按这个风格写脚本、做剪辑计划和出片。本 Skill 只准备交接材料；骨架、校验与安装由 `lov-skill-creator` 负责，发布由 `lov-skill-publisher` 负责，且只在用户要求时进行。

## 命名

- **ID。** 用 `lov-SLUG-style-media-creator`，源码目录 `SLUG-style-media-creator-skill`。
- **展示名。** 沿用已有先例“某某风格短视频”：
  - `lov-laozhang-style-media-creator`：老张心理风格短视频；
  - `lov-xiaonuan-style-media-creator`：晓暖说媒风格短视频。

  展示名里出现博主名，只用来说明参考来源，不表示合作或授权；卡片里必须写明这一点。

## 带走什么

- **风格包。** 冻结风格包放在 `assets/SLUG-v0.1/`，包括 `style-profile.json`、`evidence.jsonl`、`FROZEN.json`、`holdout-report.json`、`per-video-analysis.json` 与训练集文本测量。
- **Schema。** 本 Skill 的 `assets/schemas/` 中用得到的几份。
- **创作协议。** 从规则写成新选题的创作步骤：输入、叙事模板、时间线约束、字幕与标题规则、响度目标、状态分级。
- **剪辑计划校验器。** 把规则里能自动检查的门禁写成该风格专用的检查（时间线连续、分隔时长、字幕行数与字数、标题与资料卡顺序、安全区、响度）。
- **模板。** `templates/remotion`，带该博主的 `style-tokens.json`，不带字体文件。
- **案例。** 样本到风格包的过程案例；有演示时附演示的计划与质检记录。

## 绝不带走

- 原片、抽帧、截图、封面、完整转写、听感片段；
- 博主的头像、声音、栏目名、口头签名、品牌字样与道具文字；
- 服务话术与案例数；
- 未获同意的出镜者信息；
- 凭据与本机绝对路径。

## 交接检查

- 风格包 `verify` 通过，`FROZEN.json` 的 SHA-256 与文件一致。
- 留出报告的覆盖率、独立命中与受污染项在卡片里如实写出。
- 演示素材的授权状态写清楚。例如“重剪版对外发布需当事人确认”。
- 定价交给 `lov-skill-pricing`。证据只有一两条演示时，先例都定为免费入口。
