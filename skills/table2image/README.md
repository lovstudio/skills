# 表格成图 · Table to Image

![Version](https://img.shields.io/badge/version-0.1.2-CC785C)

将 Markdown 表格与可选 Mable 布局参数转换为托管 PNG 地址，也可直接下载本地图片。

## 本地安装

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-table2image"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。API 根地址按命令参数、`MABLE_API_BASE`、
`skills.lov-table2image.records.api_base`、生产默认地址的顺序解析。

```bash
python3 scripts/profile_store.py read --skill-id lov-table2image --pretty
```

## 使用

返回图片地址：

```bash
export MABLE_API_TOKEN="<LovStudio token>"
python3 scripts/table2image.py ./table.md
```

Mable API 每次成功生成扣 3 Credits，响应会返回本次扣费与剩余余额。

复用 Mable 型号并下载图片：

```bash
python3 scripts/table2image.py ./table.md \
  --model Asge8oUog7I \
  --output ./table.png
```

布局参数既可传 JSON 文件，也可传内联 JSON。`--model` 与 `--layout-json` 互斥。

## 原子组合

本 Skill 独立拥有“Markdown 表格 → 托管 PNG URL”结果。通用卡片、信息图、生图和
富媒体打包保留为可选的工件级上下游，见 `references/skill-composition.md`。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、边界、风险和验证证据。
- `cases/cases.json`：真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -m unittest discover -s tests -v
```

## 依赖

- Python 3.9+
- 可访问的 Mable API

## License

MIT
