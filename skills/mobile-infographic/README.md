# lov-mobile-infographic

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把一段已经有结论的内容，重排成手机上真的读得下去的证据型信息卡：竖版画布、单列阅读路径、
字号下限与行宽上限、可核查的口径与来源，并输出可编辑 HTML 与 2× PNG 系列。

与 `lov-professional-infographic` 的分工很清楚：那个 Skill 做 16:9 桌面阅读的咨询 Exhibit，
这个 Skill 做 1080 宽竖屏阅读的手机卡。文字、证据与排版全部由 DOM 生成，PNG 由浏览器精确栅格化，
不把整张卡交给生图模型。

## 本地安装

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
  --template single-claim --ratio 3:4 --filename card-01.html \
  --eyebrow "运营手册 · 01" --title "优化 harness 的三步" \
  --claim "模型是自变量，harness 是因变量" \
  --source "来源：一次真实项目复盘" --output-dir ./cards
python3 "$SKILL_DIR/scripts/infographic_cli.py" render --input ./cards/card-01.html --output ./cards/card-01.png --scale 2
python3 "$SKILL_DIR/scripts/infographic_cli.py" audit --input ./cards/card-01.html --image ./cards/card-01.png --report ./cards/card-01.audit.json --ratio 3:4
```

一组系列：三次 `scaffold`（`--series-index 1..3 --series-size 3`），逐张 `render` 与 `audit`，
再按 [`references/series-and-export.md`](references/series-and-export.md) 写 `manifest.json`。

真实案例见 [`cases/cases.json`](cases/cases.json)：三张 `3:4` 卡，机器审计 3/3 通过、各 100/100。

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
