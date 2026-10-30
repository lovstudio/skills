# Changelog

## 0.3.1 — 2026-10-30

- README 安装命令改回官方的 `npx lovstudio skills add koubo-media-creator`（免费直接安装）。

## 0.3.0 — 2026-10-30

- 以 MIT 协议开源，源码仓库公开；停止付费销售。
- README 安装说明改为直接克隆；`pricing-card.yaml` 与 Skill Card 的定价、分发改为免费开源。

## 0.2.1 — 2026-10-29

- `skill.yaml` 版本号补齐（0.2.0 发布时仍写 0.1.0）。
- README 安装说明与官网现状对齐：付费 Skill 当前随 VIP 会员解锁，不再写单项购买价。

## 0.2.0 — 2026-10-28

- 首发上架 Lovstudio.AI 官网：一次性付费 1,394 Credits，源码私有（2026-10-29 定价）。
- 调用 ID 改为 `lov-koubo-media-creator`（源目录 `koubo-media-creator-skill`，Profile 命名空间 `skills.lov-koubo-media-creator`）；展示名「口播短片」与数据格式名 `talking-head-*/v1` 不变。

## 0.1.0 — 2026-10-28

- 首版：片型语法（7 条代表作转写、上半屏切点与 30 张封面量化）、五种片型公式、`script.json` 规范。
- 脚本：`check_script.py`（结构、估时、证据覆盖、事实出处、AI 腔与借用口头禅）、`teleprompter.py`、`capture.py`（网页 / 终端输出 / 批量）、
  `tts.py`（样片占位配音与重读回归）、`align.py`（最后一遍选择 + 最长静音缝落刀，可接外部 ASR）、`build.py`、`mix.py`、`finish.py`、`gen_bgm.py`。
- 起步工程：Remotion 4 竖版三布局（分屏 / 全脸 / 全素材）、红框与焦点推近、标黄字幕、Logo 水印、片尾关注卡、3:4 与 16:9 封面；Vision 抠图工具。
- 首个案例：`2026-10-28-topic-to-short` 样片 v0.2。
