# 插件雷达 · Plugin Radar

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

从 dshfind 插件网关检索 DSH 插件，返回带评分、等级、星标、安装方式与风险标记等证据的候选清单，并附数据版本溯源。

## 本地安装

源目录：`~/lovstudio/coding/skills/dsh-search-plugin-skill`。安装为两级符号链接：

```bash
export SKILL_SOURCE_DIR="$HOME/lovstudio/coding/skills/dsh-search-plugin-skill"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/dsh-search-plugin"
ln -s ../../.agents/skills/dsh-search-plugin "$HOME/.claude/skills/dsh-search-plugin"
```

`~/.claude/skills` 层用相对链接，`readlink -f` 才能解析到真源。

## 用户 Profile（跨 session）

本 Skill 在 `skill.yaml` 中声明 `user-profile/v1`，从共享 Profile 读取用户语言、工作区输出目录与 `skills.dsh-search-plugin` 命名空间的长期记录（网关地址、报告语言）。用户直接说出的持久偏好由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

示例一：查找记忆类插件

```bash
python3 scripts/search_plugin.py search "memory" --limit 10 --pretty
python3 scripts/search_plugin.py suggest "memory"
```

输出：`omdsh-dev/dsh-mnemon`（251 stars，featured）、`huiliyi37/dsh-tianshu-tui` 等候选，附 `data_version` 溯源。

示例二：按条件过滤并查看关键候选详情

```bash
python3 scripts/search_plugin.py search "vision" --grade S --limit 5
python3 scripts/search_plugin.py detail Anionex dsh-vision-toolkit
```

输出：`Anionex/dsh-vision-toolkit`（score 94，grade S，npm 可装）、`liustack/modlens`（85/S）等，详情含 i18n 简介与 7 日增长数据。

## 原子组合

`references/skill-composition.md` 记录了已检查的相邻 Skills：本 Skill 是检索核心原子；`dsh-search-or-create-plugin` 与 `dsh-plugin-creator` 是可选的下游交接（artifact 级，非隐藏依赖）。外部 sibling Skill 不作为隐藏运行时依赖。

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

## License

MIT
