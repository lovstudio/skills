# 手机信息图 · Mobile Infographic

![Version](https://img.shields.io/badge/version-0.9.1-CC785C)

把一段已经有结论的内容，重排成手机上真的读得下去的证据型信息卡：竖版画布、单列阅读路径、
字号下限与行宽上限、可核查的口径与来源。**默认输出一张 1080 宽、高度自适应的卡片**
（`--ratio long`），只在用户明确要多张或长卡超过三屏上限时才做系列。

两条硬规则：标题必须是可被反驳的**观点**（不是数字复述），主关系必须**图形化**
（三项以上可比数据用 `bar-ranking` 的条形长度，不写流水账）。卡面来源只写
「来源：群聊记录」这类可披露来源，内部数据库/表名/路径由 `source_hygiene` 拦截；页脚署名可选。

与 `lov-professional-infographic` 的分工很清楚：那个 Skill 做 16:9 桌面阅读的咨询 Exhibit，
这个 Skill 做 1080 宽竖屏阅读的手机卡。文字、证据与排版全部由 DOM 生成，PNG 由浏览器精确栅格化，
不把整张卡交给生图模型。

## 本地安装

```bash
npx skills add lov-mobile-infographic -g -y
```

源码安装：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-mobile-infographic"
```

LovStudio 三层链约定：`~/.agents/skills/lov-mobile-infographic` 绝对指向本目录，
各宿主目录用相对链接指向该共享入口。

## 用户 Profile（跨 session）

本 Skill 在 `skill.yaml` 中声明 `user-profile/v1`，从共享 Profile 读取用户、品牌、
工作区偏好与本 Skill 的长期记录。用户直接说出的持久偏好或品牌事实由
`scripts/profile_store.py` 写回 `skills.lov-mobile-infographic.records`。

品牌解析顺序与字段见 [`references/user-config.md`](references/user-config.md)；
完整 Profile 契约见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

一张卡：

```bash
export SKILL_DIR="$(pwd)"
python3 "$SKILL_DIR/scripts/infographic_cli.py" scaffold \
  --template single-claim --filename card-01.html \
  --eyebrow "运营手册 · 01" --title "优化 harness 的三步" \
  --claim "模型是自变量，harness 是因变量" \
  --source "来源：一次真实项目复盘" --output-dir ./cards
python3 "$SKILL_DIR/scripts/infographic_cli.py" render --input ./cards/card-01.html --output ./cards/card-01.png --scale 2
python3 "$SKILL_DIR/scripts/infographic_cli.py" audit --input ./cards/card-01.html --image ./cards/card-01.png --report ./cards/card-01.audit.json --ratio long
```

`--ratio` 省略时即 `long`：卡片高度跟着内容走（下限 1.2× 宽，上限三个 `3:4` 屏）。
需要固定比例时显式传 `--ratio 3:4`（微信图文）、`4:5`（信息流）、`9:16`（全屏故事）或 `1:1`（九宫格）。

排位数据用条形榜单：条目按大小画长度，名单与依据写在对应条形下方，不写流水账。

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" scaffold \
  --template bar-ranking --filename card.html \
  --eyebrow "调研 · 群像" --title "最受欢迎的，是继续做事的那类城" \
  --claim "前三类合计 41 人，占可判断成员的 58%" \
  --row "01 新海|25|New Harbor · AI 进入工作|早＊ · 南艺 89" \
  --row "04 新界|13|Nexus · 低税低监管|刘＊畅 · Cakinna" \
  --source "来源：群聊记录" --output-dir ./cards
```

只有用户明确要求多张、或一张长卡超过 4320px 时才做系列：按 `--series-index 1..N --series-size N`
逐张 `scaffold`、`render`、`audit`，再按
[`references/series-and-export.md`](references/series-and-export.md) 写 `manifest.json`。

真实案例见 [`cases/cases.json`](cases/cases.json)：一次“明确要求三张”的 `3:4` 系列，
机器审计 3/3 通过、各 100/100。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录了已检查的相邻 Skills、
产物级交接、重叠处理，以及判定为 Single Skill 的理由。外部 sibling Skill 不是隐藏依赖。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)：用途、依赖、风险、输出与维度地图。
- [`cases/cases.json`](cases/cases.json)：真实 Input → Prompt → Output。
- [`pricing-card.yaml`](pricing-card.yaml)：价值锚点、交付边界与复评条件。

## 质量门

```bash
python3 scripts/test_infographic_cli.py
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+ 标准库；`scaffold` 与 `init-brand` 不需要浏览器或网络。
- `render` 与 `audit` 需要 Playwright for Python 与 Chromium 或 Google Chrome。
- 无必需凭据。

```bash
python3 -m pip install "playwright>=1.45,<2"
python3 -m playwright install chromium
```

## License

MIT
