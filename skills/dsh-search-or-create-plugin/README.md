# 插件选型顾问 · Plugin Advisor

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

检索候选插件并按五个维度分析适配度：有匹配就给出采用路径，否则产出基于最近开源实现的新插件方案并交给 dsh-plugin-creator。

## 本地安装

源目录：`~/lovstudio/coding/skills/dsh-search-or-create-plugin-skill`。安装为两级符号链接：

```bash
export SKILL_SOURCE_DIR="$HOME/lovstudio/coding/skills/dsh-search-or-create-plugin-skill"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/dsh-search-or-create-plugin"
ln -s ../../.agents/skills/dsh-search-or-create-plugin "$HOME/.claude/skills/dsh-search-or-create-plugin"
```

`~/.claude/skills` 层用相对链接，`readlink -f` 才能解析到真源。

## 用户 Profile（跨 session）

本 Skill 在 `skill.yaml` 中声明 `user-profile/v1`，从共享 Profile 读取用户语言、工作区输出目录与 `skills.dsh-search-or-create-plugin` 命名空间的长期记录（网关地址、最低等级、安装偏好）。用户直接说出的持久偏好由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

示例一（MATCH 采用）：为纯文本模型补图片问答能力

```bash
python3 scripts/search_plugin.py search "vision" --limit 10
python3 scripts/search_plugin.py detail Anionex dsh-vision-toolkit
```

分析：Anionex/dsh-vision-toolkit 能力覆盖图片问答、score 94、grade S、npm 可装、无风险标记 → MATCH，给出 npm 安装路径与验收检查。

示例二（NO-MATCH 新建）：定时抓取 RSS 并推送飞书

```bash
python3 scripts/search_plugin.py search "rss" --limit 10
python3 scripts/search_plugin.py search "feishu" --limit 10
```

分析：RSS 侧只有 STARDUSTLC666/dsh-rss（未评分），飞书侧只有 omdsh-dev/dsh-lark 等消息插件，无单一插件同时覆盖抓取与推送 → NO-MATCH，产出 new-plugin-brief-rss-feishu.md，交给 dsh-plugin-creator。

## 原子组合

`references/skill-composition.md` 记录了已检查的相邻 Skills：本 Skill 内嵌检索步骤保持自包含；`dsh-plugin-creator`（创建）与 `dsh-plugin-publisher`（发布）是可选的下游交接，均为 artifact 级，非隐藏依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：真实 Input → Prompt → Output 案例（2026-08-27 实测网关）。
- `pricing-card.yaml`：免费价值锚点、交付边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（仅标准库）
- 网络访问 `https://api.dshfind.com`（公开只读，无需鉴权）
- 可选下游：`dsh-plugin-creator`（新建路径）、`dsh-plugin-publisher`（发布）

## License

MIT
