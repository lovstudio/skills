# lov-xhs

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把「小红书主题请求」默认整理成一份有来源、能执行的调研报告：先发现笔记，
再读取正文，最后输出结论、方案、证据表和不确定性。只有用户明确说“只搜索 /
查标题 / 导出 JSON”时，才进入纯搜索结果模式。

## 安装

如果这个 Skill 已发布到 Skills 目录：

```bash
npx skills add lov-xhs
```

本地源码安装：

```bash
export AGENT_SKILLS_DIR="/path/to/agent/skills"
mkdir -p "$AGENT_SKILLS_DIR"
ln -s /absolute/path/to/xhs-skill "$AGENT_SKILLS_DIR/lov-xhs"
```

## 默认行为：主题 → 调研报告

用户输入主题，例如「冈仁波齐线路规划」时，执行两步：

```bash
python3 scripts/xhs_search.py "冈仁波齐线路规划" \
  --pages 3 \
  --sort popular \
  --output xhs-search.json

python3 scripts/xhs_collect.py "冈仁波齐线路规划" \
  --pages 3 \
  --sort popular \
  --max-notes 12 \
  --delay 1.8 \
  --output xhs-evidence.json
```

然后按 [`references/research-report.md`](references/research-report.md) 合成报告：
结论先行、给出可执行方案、附证据表与原始笔记链接，并明确哪些是来源事实、
哪些是推理建议。搜索结果 JSON 和正文语料 JSON 都是中间证据，不是默认最终
交付物。

## 显式搜索模式

只有用户明确要求搜索、标题过滤或导出 JSON 时，才只运行：

```bash
python3 scripts/xhs_search.py "转山" \
  --must-contain "冈仁波齐" \
  --must-contain "转山" \
  --pages 3 \
  --sort popular \
  --output xhs-result.json
```

去掉 `--must-contain` 就是普通关键词搜索。更多参数见
[`references/implementation.md`](references/implementation.md)。

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

本 Skill 检查了相邻能力并记录在
[`references/skill-composition.md`](references/skill-composition.md)。它不把
`lov-media-crawler` 或 `lov-media-publisher` 当作隐藏依赖；只有用户明确要求
下载媒体时，才把选中的笔记 URL 交给 `lov-media-crawler`。跨平台或非小红书
的通用研究交给 `deep-research`。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml)
- [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

如果本机 Python 报缺少 PyYAML，先执行：

```bash
python3 -m pip install --user PyYAML
```

## 依赖

- Python 3.9+
- `xiaohongshu-cli` 0.6.4+
- 已登录的小红书浏览器状态
- 网络访问
- `lov-branding-consistency`（用于面向读者的报告文案一致性）

## License

MIT
