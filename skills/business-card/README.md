<p align="center">
  <img src="docs/images/example-dark-terracotta.png" alt="business-card example" width="100%">
</p>

<h1 align="center">lov-business-card</h1>

<p align="center">
  <strong>把任何人的姓名、头衔与金句，一键变成精美的编辑式名片。</strong><br>
  <sub>高清 PNG（默认 4800×2400） · 可点击下载的自包含 HTML · 三套主题</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-CC785C" alt="version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
  <a href="https://example.com">example.com</a> · part of <a href="https://example.com/skills/general-skills">general-skills</a>
</p>

---

## 这是什么

把一段身份信息渲染成一张 2:1 的**编辑式（editorial / luxury-minimal）**名片：瑞士排版网格、
发丝线分隔、单一强调色、宋体 × Didot 字体配对、刊头与底栏分区、淡淡的姓名水印。靠字号、字距、
层级建立秩序，而不是堆装饰。没有头像？自动用姓名首字渲染衬线 monogram。

## 示例

上图为「品牌方」的实际名片（`dark-terracotta` 主题 + 头像）。同一套数据，三种主题：

| `dark-terracotta`（暖深·陶土，默认） | `midnight`（冷深·钢蓝） | `ivory`（浅·象牙 + monogram 回退） |
|---|---|---|
| ![dark](docs/images/example-dark-terracotta.png) | ![midnight](docs/images/example-midnight.png) | ![ivory](docs/images/example-ivory-monogram.png) |

## Install

```bash
git clone https://example.com/skills/business-card-skill "${SKILL_SKILLS_INSTALL_DIR:?Set SKILL_SKILLS_INSTALL_DIR}/lov-business-card"
```

Requires: Python 3.8+ and Google Chrome / Chromium (for PNG rendering). macOS 用内置 `sips` 裁切，
其他平台 `pip install pillow`。没有浏览器时跳过 PNG —— 打开 HTML 用右下角按钮下载即可。

## Usage

```bash
SKILL_DIR="${SKILL_SKILLS_INSTALL_DIR:?Set SKILL_SKILLS_INSTALL_DIR}/lov-business-card"
python3 "$SKILL_DIR/scripts/render_card.py" \
  --name "品牌方" --latin "Mark Shawn" \
  --brand "SKILL.AI" --index "STUDIO — Nº 2026" \
  --tags "背包客,超级开发者,AI / OPC 布道师" \
  --tagline "在 **Agent 时代**，|寻找**人**的意义" \
  --pursuits "旅行,羽毛球,计算机科学,心理学,哲学" \
  --bases "上海 陆家嘴数智港,北京 搜狐大厦清智孵化器" \
  --avatar ./me.png --theme dark-terracotta \
  --out ./output --format both
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--name` | (required) | 姓名，支持中文 |
| `--latin` | `""` | 英文名 / 罗马音（斜体小字） |
| `--brand` | `""` | 左上品牌；含 `.` 时圆点会高亮 |
| `--index` | `""` | 右上编号，如 `STUDIO — Nº 2026` |
| `--tags` | `""` | 角色标签，逗号分隔 |
| `--tagline` | `""` | 金句；`**词**` 高亮，`\|` 换行 |
| `--pursuits` | `""` | 爱好，逗号分隔（底栏左） |
| `--bases` | `""` | 据点/城市，逗号分隔（底栏右，带定位针） |
| `--avatar` | `""` | 头像图片路径；省略则用 monogram |
| `--caption` | `""` | 头像底部图注（可选） |
| `--watermark` | 姓名末字 | 背景巨型水印字 |
| `--theme` | `dark-terracotta` | `dark-terracotta` \| `midnight` \| `ivory` |
| `--out` | `./output` | 输出目录 |
| `--format` | `both` | `png` \| `html` \| `both` |
| `--scale` | `3` | PNG 倍率（3 → 4800×2400） |

## Output

- `{name}-名片.png` — 高清名片（默认 4800×2400）
- `{name}-名片.html` + `modern-screenshot.umd.js` — 浏览器打开，点「下载为图片 PNG」自出 3× 高清图（两文件需同目录）

## 加主题

往 `scripts/render_card.py` 的 `THEMES` 字典加一组 CSS 变量即可，模板无需改动。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=skill-publisher/business-card-skill&type=Date)](https://star-history.com/#skill-publisher/business-card-skill&Date)

## License

MIT
